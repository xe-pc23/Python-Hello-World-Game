import pygame
import random
import sys
import time

pygame.init()

WIDTH, HEIGHT = 640, 480
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Code Dodging Game")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PROGRAMMING_COLOR = (100, 200, 255)
PINK_COLOR = (255, 105, 180)
ORANGE_COLOR = (255, 165, 0)

player = pygame.Rect(300, 400, 10, 10)
player_speed = 5

bullets = []
base_bullet_speed = 3

font = pygame.font.Font(None, 24)

start_time = time.time()
quiz_interval = 15
last_quiz_time = time.time()

current_quiz = 'Type the correct print statement in Python:'
correct_answer = 'print("Hello World")'
quiz_mode = False
user_input = ""
quiz_start_time = 0
quiz_duration = 5

slow_factor = 10
last_bullet_time = time.time()
base_bullet_interval = 0.5

correct_count = 0

incorrect_message = ""
incorrect_message_time = 0
incorrect_message_duration = 2

def game_over_screen(elapsed_time, correct_count):
    win.fill(BLACK)
    big_font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 32)

    over_text = big_font.render("Game Over!", True, WHITE)
    time_text = small_font.render(f"Time Survived: {elapsed_time} seconds", True, WHITE)
    correct_text = small_font.render(f"Correct Answers: {correct_count}", True, WHITE)
    prompt_text = small_font.render("Press any key to quit.", True, WHITE)

    win.blit(over_text, (WIDTH//2 - over_text.get_width()//2, HEIGHT//2 - 80))
    win.blit(time_text, (WIDTH//2 - time_text.get_width()//2, HEIGHT//2))
    win.blit(correct_text, (WIDTH//2 - correct_text.get_width()//2, HEIGHT//2 + 40))
    win.blit(prompt_text, (WIDTH//2 - prompt_text.get_width()//2, HEIGHT//2 + 100))

    pygame.display.update()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                waiting = False
    pygame.quit()
    sys.exit()

def draw_game():
    win.fill(BLACK)
    pygame.draw.rect(win, WHITE, player)

    bullet_color = PROGRAMMING_COLOR
    if correct_count >= 4:
        bullet_color = ORANGE_COLOR
    elif correct_count >= 2:
        bullet_color = PINK_COLOR

    for bullet in bullets:
        text_surface = font.render(bullet["text"], True, bullet_color)
        win.blit(text_surface, (bullet["rect"].x, bullet["rect"].y - 15))

    elapsed_time = int(time.time() - start_time)
    time_text = font.render(f"Time: {elapsed_time}s", True, WHITE)
    correct_text = font.render(f"Correct: {correct_count}", True, WHITE)
    win.blit(time_text, (WIDTH - 140, 10))
    win.blit(correct_text, (WIDTH - 140, 30))

    if quiz_mode:
        pygame.draw.rect(win, BLACK, (50, 100, 540, 150))
        pygame.draw.rect(win, WHITE, (50, 100, 540, 150), 2)
        question_text = font.render(current_quiz, True, WHITE)
        input_text = font.render(">> " + user_input, True, WHITE)
        win.blit(question_text, (60, 120))
        win.blit(input_text, (60, 150))

    if incorrect_message and time.time() - incorrect_message_time < incorrect_message_duration:
        error_text = font.render(incorrect_message, True, (255, 100, 100))
        win.blit(error_text, (50, 270))

    pygame.display.update()

def game_over():
    elapsed_time = int(time.time() - start_time)
    game_over_screen(elapsed_time, correct_count)

def handle_quiz():
    global quiz_mode, user_input, quiz_start_time, correct_count
    global incorrect_message, incorrect_message_time, last_quiz_time

    if time.time() - quiz_start_time > quiz_duration:
        if user_input.strip() == correct_answer:
            quiz_mode = False
            user_input = ""
            correct_count += 1
            incorrect_message = ""
            last_quiz_time = time.time()
        else:
            incorrect_message = "Incorrect answer! Try again."
            incorrect_message_time = time.time()
            user_input = ""

clock = pygame.time.Clock()

while True:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if quiz_mode and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                user_input = user_input[:-1]
            elif event.key == pygame.K_RETURN:
                handle_quiz()
            else:
                user_input += event.unicode

    keys = pygame.key.get_pressed()
    if not quiz_mode:
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and player.left > 0:
            player.move_ip(-player_speed, 0)
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and player.right < WIDTH:
            player.move_ip(player_speed, 0)
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and player.top > 0:
            player.move_ip(0, -player_speed)
        if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and player.bottom < HEIGHT:
            player.move_ip(0, player_speed)

    if not quiz_mode and time.time() - last_quiz_time > quiz_interval:
        quiz_mode = True
        quiz_start_time = time.time()
        user_input = ""

    if quiz_mode:
        if correct_count <= 1:
            slow_factor = 10
        elif correct_count <= 3:
            slow_factor = 6
        else:
            slow_factor = 4
        current_bullet_interval = base_bullet_interval * slow_factor
    else:
        current_bullet_interval = base_bullet_interval

    if time.time() - last_bullet_time > current_bullet_interval:
        rect = pygame.Rect(random.randint(0, WIDTH - 140), 0, 140, 20)
        bullets.append({
            "rect": rect,
            "text": correct_answer,
            "vy": float(rect.y)
        })
        last_bullet_time = time.time()

    for bullet in bullets[:]:
        text_surface = font.render(bullet["text"], True, PROGRAMMING_COLOR)
        text_rect = text_surface.get_rect(topleft=(bullet["rect"].x, bullet["rect"].y - 15))

        speed = base_bullet_speed
        if quiz_mode:
            speed = base_bullet_speed / slow_factor

        bullet["vy"] += speed
        bullet["rect"].y = int(bullet["vy"])

        if player.colliderect(text_rect):
            game_over()

        if bullet["rect"].top > HEIGHT:
            bullets.remove(bullet)

    draw_game()
