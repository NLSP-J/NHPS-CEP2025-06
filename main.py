import pygame as pg
import random, time
import math
import asyncio

pg.init()
clock = pg.time.Clock()

# Colours
black = (0, 0, 0)
white = (255, 255, 255)
red = (255, 0, 0)
yellow = (255, 255, 0)
green = (0, 255, 0)
blue = (0, 0, 255)

# Window size
win_width = 800
win_height = 600
screen = pg.display.set_mode((win_width, win_height))
pg.display.set_caption('Falling Debris')

font = pg.font.Font(None, 30)

# Game variables
speed = 5
score = 0
running = True
lives = 10
game_state = 1     # 1: main game, 2: game over

# Player variables
player_size = 40
player_pos = [win_width / 2, win_height - player_size]
player_speed = 8
player_image = pg.image.load('./assets/images/mario.png')
player_image = pg.transform.scale(player_image, (player_size, player_size))
player_rect = pg.Rect(player_pos[0], player_pos[1], player_size, player_size)

# Object variables
obj_size = 60
obj_data = []
obj = pg.image.load('./assets/images/e1.png')
obj = pg.transform.scale(obj, (obj_size, obj_size))

# Boss variables (giant e1.png)
boss_size = obj_size * 3  # 180x180
boss_image = pg.image.load('./assets/images/e1.png')
boss_image = pg.transform.scale(boss_image, (boss_size, boss_size))
boss_data = []
boss_speed = 3
boss_spawn_chance = 0.005

# Background
bg_image = pg.image.load('./assets/images/background.png')
bg_image = pg.transform.scale(bg_image, (win_width, win_height))

# Jump variables
is_jumping = False
jump_velocity = 0
jump_power = -20  # Initial jump velocity (negative for upward movement)
gravity = 1
ground_y = win_height - player_size  # Ground level for player
can_double_jump = False
has_double_jumped = False
wall_jump_cooldown = 0

# Platform variables
platforms = []
platform_width_range = (100, 200)
platform_height_range = (300, 500)  # Adjusted to be higher for better jumping
platform_color = black  # Black platforms

# Bullet variables
bullets = []
bullet_speed = 15
bullet_radius = 5
bullet_color = yellow
last_shot_time = 0
shot_cooldown = 200  # milliseconds between shots

# Energy system
max_energy = 100
current_energy = max_energy
energy_regen_rate = 1  # energy per second
last_energy_regen_time = 0
energy_regen_cooldown = 5000  # 5 seconds in milliseconds
is_energy_regen = False
energy_regen_start_time = 0

''' ---------- CREATE_OBJECT FUNCTION ---------- '''
def create_object(obj_data):
    if len(obj_data) < 10 and random.random() < 0.1:
        x = random.randint(0, win_width - obj_size)
        y = 0
        obj_data.append([x, y, obj])

''' ---------- CREATE_BOSS FUNCTION ---------- '''
def create_boss(boss_data):
    if len(boss_data) < 1 and random.random() < boss_spawn_chance:
        x = random.randint(0, win_width - boss_size)
        y = 0
        boss_data.append([x, y, boss_image])

''' ---------- CREATE_PLATFORMS FUNCTION ---------- '''
def create_platforms():
    if len(platforms) < 5:  # Limit the number of platforms
        # Random platform width, y-position, and x-position
        width = random.randint(platform_width_range[0], platform_width_range[1])
        x = random.randint(0, win_width - width)
        y = random.randint(platform_height_range[0], platform_height_range[1])
        platforms.append(pg.Rect(x, y, width, 20))  # Add the platform

''' ---------- UPDATE_OBJECTS FUNCTION ---------- '''
def update_objects(obj_data):
    global score
    for object in obj_data[:]:
        x, y, image_data = object
        if y < win_height:
            y += speed
            object[1] = y
            screen.blit(image_data, (x, y))
        else:
            obj_data.remove(object)
            score += 1

''' ---------- UPDATE_BOSS FUNCTION ---------- '''
def update_boss(boss_data):
    global score
    for boss in boss_data[:]:
        x, y, image_data = boss
        if y < win_height:
            y += boss_speed
            boss[1] = y
            screen.blit(image_data, (x, y))
        else:
            boss_data.remove(boss)
            score += 5

''' ---------- UPDATE_BULLETS FUNCTION ---------- '''
def update_bullets():
    global bullets
    for bullet in bullets[:]:
        # Move bullet
        bullet[0] += bullet[2]  # x += dx
        bullet[1] += bullet[3]  # y += dy
        
        # Remove bullets that go off screen
        if (bullet[0] < 0 or bullet[0] > win_width or 
            bullet[1] < 0 or bullet[1] > win_height):
            bullets.remove(bullet)
            continue
        
        # Draw bullet
        pg.draw.circle(screen, bullet_color, (int(bullet[0]), int(bullet[1])), bullet_radius)

''' ---------- CHECK BULLET COLLISIONS FUNCTION ---------- '''
def check_bullet_collisions():
    global bullets, obj_data, boss_data, score
    
    # Check collisions with regular enemies
    for bullet in bullets[:]:
        bullet_rect = pg.Rect(bullet[0] - bullet_radius, bullet[1] - bullet_radius, 
                             bullet_radius * 2, bullet_radius * 2)
        
        for enemy in obj_data[:]:
            enemy_rect = pg.Rect(enemy[0], enemy[1], obj_size, obj_size)
            if bullet_rect.colliderect(enemy_rect):
                if bullet in bullets:
                    bullets.remove(bullet)
                obj_data.remove(enemy)
                score += 2  # Bonus for shooting
                break
        
        # Check collisions with bosses
        for boss in boss_data[:]:
            boss_rect = pg.Rect(boss[0], boss[1], boss_size, boss_size)
            if bullet_rect.colliderect(boss_rect):
                if bullet in bullets:
                    bullets.remove(bullet)
                boss_data.remove(boss)
                score += 10  # Big bonus for shooting boss
                break

''' ---------- SHOOT BULLET FUNCTION ---------- '''
def shoot_bullet():
    global last_shot_time, bullets, current_energy, is_energy_regen, energy_regen_start_time
    
    # Check if we have energy to shoot
    if current_energy <= 0:
        # Start energy regeneration cooldown if not already started
        if not is_energy_regen:
            is_energy_regen = True
            energy_regen_start_time = pg.time.get_ticks()
        return
    
    current_time = pg.time.get_ticks()
    if current_time - last_shot_time > shot_cooldown:
        # Get mouse position for shooting direction
        mouse_x, mouse_y = pg.mouse.get_pos()
        
        # Calculate direction vector
        dx = mouse_x - (player_rect.x + player_size/2)
        dy = mouse_y - (player_rect.y + player_size/2)
        
        # Normalize vector
        length = math.sqrt(dx*dx + dy*dy)
        if length > 0:
            dx = dx / length * bullet_speed
            dy = dy / length * bullet_speed
            
            # Create bullet at player center
            bullet_x = player_rect.x + player_size/2
            bullet_y = player_rect.y + player_size/2
            bullets.append([bullet_x, bullet_y, dx, dy])
            
            # Use energy
            current_energy -= 5
            last_shot_time = current_time
            
            # Reset energy regen if it was active
            is_energy_regen = False

''' ---------- UPDATE ENERGY FUNCTION ---------- '''
def update_energy():
    global current_energy, is_energy_regen, energy_regen_start_time, last_energy_regen_time
    
    current_time = pg.time.get_ticks()
    
    # If energy is depleted, start regeneration cooldown
    if current_energy <= 0 and not is_energy_regen:
        is_energy_regen = True
        energy_regen_start_time = current_time
    
    # If regeneration cooldown is active
    if is_energy_regen:
        if current_time - energy_regen_start_time >= energy_regen_cooldown:
            is_energy_regen = False
            current_energy = max_energy  # Fully recharge after cooldown
        else:
            # Show cooldown progress but don't actually regen until cooldown is complete
            pass
    else:
        # Normal energy regeneration when not empty
        if current_time - last_energy_regen_time > 1000 / energy_regen_rate:
            if current_energy < max_energy:
                current_energy += 1
            last_energy_regen_time = current_time

''' ---------- DRAW ENERGY BAR FUNCTION ---------- '''
def draw_energy_bar():
    # Draw background
    bar_width = 200
    bar_height = 20
    bar_x = 20
    bar_y = 20
    pg.draw.rect(screen, black, (bar_x, bar_y, bar_width, bar_height), 2)
    
    # Draw energy level
    energy_width = int((current_energy / max_energy) * (bar_width - 4))
    energy_color = green
    if current_energy <= 0:
        # Show cooldown progress when energy is depleted
        cooldown_progress = min(1.0, (pg.time.get_ticks() - energy_regen_start_time) / energy_regen_cooldown)
        energy_width = int(cooldown_progress * (bar_width - 4))
        energy_color = blue
    
    pg.draw.rect(screen, energy_color, (bar_x + 2, bar_y + 2, energy_width, bar_height - 4))
    
    # Draw energy text
    if current_energy <= 0:
        cooldown_remaining = max(0, energy_regen_cooldown - (pg.time.get_ticks() - energy_regen_start_time))
        cooldown_sec = cooldown_remaining // 1000 + 1
        energy_text = font.render(f"Energy: Recharging... {cooldown_sec}s", True, black)
    else:
        energy_text = font.render(f"Energy: {current_energy}/{max_energy}", True, black)
    screen.blit(energy_text, (bar_x + bar_width + 10, bar_y))

''' ---------- CHECK WALL COLLISION FUNCTION ---------- '''
def check_wall_collision():
    global wall_jump_cooldown
    
    # Reduce wall jump cooldown
    if wall_jump_cooldown > 0:
        wall_jump_cooldown -= 1
    
    # Check if player is touching left or right wall
    touching_left_wall = player_rect.left <= 0
    touching_right_wall = player_rect.right >= win_width
    
    return touching_left_wall, touching_right_wall

''' ---------- WALL JUMP FUNCTION ---------- '''
def wall_jump(is_touching_left, is_touching_right):
    global is_jumping, jump_velocity, wall_jump_cooldown, has_double_jumped
    
    if wall_jump_cooldown > 0:
        return False
    
    if is_touching_left or is_touching_right:
        is_jumping = True
        jump_velocity = jump_power
        
        # Push away from the wall
        if is_touching_left:
            player_rect.x += 10  # Push right
        else:
            player_rect.x -= 10  # Push left
            
        wall_jump_cooldown = 20  # Set cooldown
        has_double_jumped = False  # Reset double jump after wall jump
        return True
    
    return False

''' ---------- CHECK PLATFORM COLLISION FUNCTION ---------- '''
def check_platform_collision():
    global is_jumping, jump_velocity, can_double_jump, has_double_jumped
    
    # Check if player is on any platform
    on_platform = False
    for platform in platforms:
        # Check if player's feet are touching the platform and falling down
        if (player_rect.bottom >= platform.top and 
            player_rect.bottom <= platform.top + 10 and
            player_rect.right > platform.left and 
            player_rect.left < platform.right and
            jump_velocity >= 0):  # Only when falling down
            
            player_rect.bottom = platform.top
            on_platform = True
            is_jumping = False
            jump_velocity = 0
            can_double_jump = True
            has_double_jumped = False
            break
    
    # If not on platform and not jumping, apply gravity
    if not on_platform and not is_jumping and player_rect.bottom < ground_y:
        jump_velocity += gravity
        player_rect.y += jump_velocity
    
    # Check if player reached the ground
    if player_rect.bottom >= ground_y:
        player_rect.bottom = ground_y
        is_jumping = False
        jump_velocity = 0
        can_double_jump = True
        has_double_jumped = False
        
    return on_platform

''' ---------- COLLISION_CHECK FUNCTION ---------- '''
def collision_check(obj_data, player_rect, boss_data):
    global running, lives, game_state

    # Check debris collisions
    for object in obj_data[:]:
        x, y, image_data = object
        obj_rect = pg.Rect(x, y, obj_size, obj_size)
        if player_rect.colliderect(obj_rect):
            lives -= 1
            obj_data.remove(object)
            if lives <= 0:
                game_state = 2
                break

    # Check boss collisions
    for boss in boss_data[:]:
        x, y, image_data = boss
        boss_rect = pg.Rect(x, y, boss_size, boss_size)
        if player_rect.colliderect(boss_rect):
            lives -= 5
            boss_data.remove(boss)
            if lives <= 0:
                game_state = 2
                break

''' ---------- SHOW GAME OVER ---------- '''
def show_game_over():
    screen.fill((0, 0, 0))
    game_over_text = font.render("GAME OVER", True, (255, 0, 0))
    score_text = font.render(f"Final Score: {score}", True, white)
    restart_text = font.render("Press R to restart or Q to quit", True, white)
    
    screen.blit(game_over_text, (win_width // 2 - 70, win_height // 2 - 30))
    screen.blit(score_text, (win_width // 2 - 80, win_height // 2))
    screen.blit(restart_text, (win_width // 2 - 150, win_height // 2 + 30))


''' ---------- RESET GAME ---------- '''
def reset_game():
    global score, lives, player_rect, obj_data, boss_data, platforms, game_state
    global is_jumping, jump_velocity, bullets, current_energy, is_energy_regen
    global can_double_jump, has_double_jumped, wall_jump_cooldown
    
    score = 0
    lives = 10
    game_state = 1
    player_rect.x = win_width / 2
    player_rect.y = win_height - player_size
    obj_data = []
    boss_data = []
    platforms = []
    bullets = []
    is_jumping = False
    jump_velocity = 0
    current_energy = max_energy
    is_energy_regen = False
    can_double_jump = True
    has_double_jumped = False
    wall_jump_cooldown = 0
    create_platforms()

''' ---------- MAIN LOOP ---------- '''
reset_game()

async def main():

    global running, game_state
    global on_ground, on_platform, is_jumping
    global touching_left, touching_right, wall_jumped
    global jump_velocity, can_double_jump, has_double_jumped, jump_velocity

    while running:
        if game_state == 1:

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False

                if event.type == pg.KEYDOWN:
                    # Jump when pressing UP arrow key
                    if event.key == pg.K_UP:
                        # Check if player is on ground or platform
                        on_ground = player_rect.bottom >= ground_y
                        on_platform = check_platform_collision()
                        
                        # Check if touching walls for wall jump
                        touching_left, touching_right = check_wall_collision()
                        wall_jumped = wall_jump(touching_left, touching_right)
                        
                        if not wall_jumped:
                            if (on_ground or on_platform) and not is_jumping:
                                is_jumping = True
                                jump_velocity = jump_power
                                can_double_jump = True
                                has_double_jumped = False
                            elif can_double_jump and not has_double_jumped and is_jumping:
                                # Double jump
                                jump_velocity = jump_power * 0.8  # Slightly weaker double jump
                                has_double_jumped = True
                                can_double_jump = False
                
                # Shoot when clicking mouse
                if event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        shoot_bullet()

            # Handle continuous key presses for smoother movement
            keys = pg.key.get_pressed()
            if keys[pg.K_LEFT]:
                player_rect.x -= player_speed
            if keys[pg.K_RIGHT]:
                player_rect.x += player_speed

            # Apply jump physics if jumping
            if is_jumping:
                player_rect.y += jump_velocity
                jump_velocity += gravity

            # Check platform collisions
            check_platform_collision()
            
            # Check wall collisions
            touching_left, touching_right = check_wall_collision()

            # Clamp player inside the window horizontally
            if player_rect.x < 0:
                player_rect.x = 0
            elif player_rect.x > win_width - player_size:
                player_rect.x = win_width - player_size

            # Create and update objects, platforms, and bosses
            create_object(obj_data)
            create_boss(boss_data)
            if len(platforms) < 3:  # Keep at least 3 platforms
                create_platforms()

            # Update energy system
            update_energy()

            # Draw everything
            screen.blit(bg_image, (0, 0))
            
            # Draw platforms
            for platform in platforms:
                pg.draw.rect(screen, platform_color, platform)
            
            update_objects(obj_data)
            update_boss(boss_data)
            
            # Update and draw bullets
            update_bullets()
            
            # Check bullet collisions
            check_bullet_collisions()

            # Draw player
            screen.blit(player_image, (player_rect.x, player_rect.y))

            # Collision checks
            collision_check(obj_data, player_rect, boss_data)

            # Draw energy bar
            draw_energy_bar()

            # Draw score and lives
            score_text = font.render(f'Score: {score}', True, black)
            lives_text = font.render(f'Lives: {lives}', True, black)
            screen.blit(score_text, (win_width - 200, win_height - 40))
            screen.blit(lives_text, (win_width - 200, win_height - 60))
            
            # Draw shooting instructions
            shoot_text = font.render('Click to shoot (Energy: 100 max)', True, black)
            screen.blit(shoot_text, (20, win_height - 40))
            
            # Draw jump instructions
            jump_text = font.render('UP: Jump/Double Jump, WALL: Wall Jump', True, black)
            screen.blit(jump_text, (20, win_height - 70))

        elif game_state == 2:
            show_game_over()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_r:  # Restart
                        game_state = 1
                        reset_game()
                    if event.key == pg.K_q:  # Quit
                        running = False

        clock.tick(30)
        pg.display.flip()
        await asyncio.sleep(0)

    pg.quit()


asyncio.run(main())