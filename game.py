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
GOLD = (255, 215, 0)  # 色の定義を追加
RAINBOW_COLORS = [
    (255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0),
    (0, 0, 255), (75, 0, 130), (148, 0, 211)
]
rainbow_idx_shifter = 0

player = pygame.Rect(300, 400, 10, 10)
player_speed = 5

bullets = []
base_bullet_speed = 3
chaser = None
chaser_speed_base = 3.0

font = pygame.font.Font(None, 24)

start_time = time.time()

quiz_interval_min = 10
quiz_interval_max = 20
next_quiz_interval = random.uniform(quiz_interval_min, quiz_interval_max)
last_quiz_time = time.time()

current_quiz = 'Type the correct print statement in Python:'
correct_answer = 'print("Hello World")'
quiz_mode = False
user_input = ""

base_bullet_interval = 0.5

last_top_attack_time = time.time()
last_other_attack_time = time.time()

correct_count = 0

incorrect_message = ""
incorrect_message_time = 0
incorrect_message_duration = 2

attack_texts = ['print', 'Hello', 'World', '""', '()']
normal_speed_multiplier = 1.5

admin_invincible = False # 管理者モード（無敵）フラグ

def game_over_screen(elapsed_time, final_correct_count):
    win.fill(BLACK)
    big_font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 32)

    over_text = big_font.render("Game Over!", True, WHITE)
    time_text = small_font.render(f"Time Survived: {int(elapsed_time)} seconds", True, WHITE)
    correct_text_render = small_font.render(f"Correct Answers: {final_correct_count}", True, WHITE)
    prompt_text = small_font.render("Press any key to quit.", True, WHITE)

    win.blit(over_text, (WIDTH//2 - over_text.get_width()//2, HEIGHT//2 - 80))
    win.blit(time_text, (WIDTH//2 - time_text.get_width()//2, HEIGHT//2))
    win.blit(correct_text_render, (WIDTH//2 - correct_text_render.get_width()//2, HEIGHT//2 + 40))
    win.blit(prompt_text, (WIDTH//2 - prompt_text.get_width()//2, HEIGHT//2 + 100))

    pygame.display.update()
    waiting = True
    while waiting:
        for event_wait in pygame.event.get():
            if event_wait.type == pygame.QUIT or event_wait.type == pygame.KEYDOWN:
                waiting = False
    pygame.quit()
    sys.exit()

def game_clear_screen(elapsed_time, final_correct_count):
    win.fill(BLACK)
    big_font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 32)

    clear_text_color = RAINBOW_COLORS[random.randint(0,len(RAINBOW_COLORS)-1)]
    clear_text = big_font.render("Game Clear! Congratulations!", True, clear_text_color)
    time_text = small_font.render(f"Total Time: {int(elapsed_time)} seconds", True, WHITE)
    correct_text_render = small_font.render(f"Correct Answers: {final_correct_count}", True, WHITE)
    prompt_text = small_font.render("Press any key to quit.", True, WHITE)

    win.blit(clear_text, (WIDTH//2 - clear_text.get_width()//2, HEIGHT//2 - 80))
    win.blit(time_text, (WIDTH//2 - time_text.get_width()//2, HEIGHT//2))
    win.blit(correct_text_render, (WIDTH//2 - correct_text_render.get_width()//2, HEIGHT//2 + 40))
    win.blit(prompt_text, (WIDTH//2 - prompt_text.get_width()//2, HEIGHT//2 + 100))

    pygame.display.update()
    waiting = True
    while waiting:
        for event_wait in pygame.event.get():
            if event_wait.type == pygame.QUIT or event_wait.type == pygame.KEYDOWN:
                waiting = False
    pygame.quit()
    sys.exit()

def draw_game():
    global rainbow_idx_shifter, admin_invincible # admin_invincible を参照
    win.fill(BLACK)
    
    player_color_to_draw = WHITE
    if admin_invincible:
        player_color_to_draw = GOLD # 無敵モードなら金色
    pygame.draw.rect(win, player_color_to_draw, player)


    bullet_color_to_use = PROGRAMMING_COLOR
    chaser_color_to_use = ORANGE_COLOR

    if correct_count == 5:
        rainbow_idx_shifter = (rainbow_idx_shifter + 1) % (len(RAINBOW_COLORS) * 3)
        current_rainbow_color = RAINBOW_COLORS[(rainbow_idx_shifter // 3) % len(RAINBOW_COLORS)]
        bullet_color_to_use = current_rainbow_color
        chaser_color_to_use = current_rainbow_color
    elif correct_count == 4:
        bullet_color_to_use = ORANGE_COLOR
    elif correct_count >= 2:
        bullet_color_to_use = PINK_COLOR

    for bullet_item in bullets:
        text_surface = font.render(bullet_item["text"], True, bullet_color_to_use)
        win.blit(text_surface, (bullet_item["rect"].x, bullet_item["rect"].y - 15))

    if chaser is not None:
        pygame.draw.rect(win, chaser_color_to_use, chaser["rect"])

    elapsed_time_current = int(time.time() - start_time)
    time_text_render = font.render(f"Time: {elapsed_time_current}s", True, WHITE)
    correct_text_render = font.render(f"Correct: {correct_count}", True, WHITE)
    win.blit(time_text_render, (WIDTH - 140, 10))
    win.blit(correct_text_render, (WIDTH - 140, 30))

    if quiz_mode:
        pygame.draw.rect(win, BLACK, (50, 100, 540, 150))
        pygame.draw.rect(win, WHITE, (50, 100, 540, 150), 2)
        question_text = font.render(current_quiz, True, WHITE)
        input_text = font.render(">> " + user_input, True, WHITE)
        win.blit(question_text, (60, 120))
        win.blit(input_text, (60, 150))

    if incorrect_message and time.time() - incorrect_message_time < incorrect_message_duration:
        # 管理者モード有効化メッセージもここで表示される
        feedback_color = (255,100,100) if "Incorrect" in incorrect_message else (200,200,0) # 黄色っぽい色で管理者モード通知
        if "Admin mode" in incorrect_message:
             feedback_color = GOLD
        error_text = font.render(incorrect_message, True, feedback_color)
        win.blit(error_text, (50, HEIGHT - 50)) # 画面下部中央寄りに表示変更

    pygame.display.update()

def game_over_wrapper():
    current_elapsed_time = time.time() - start_time
    game_over_screen(current_elapsed_time, correct_count)

def handle_quiz_submission():
    global quiz_mode, user_input, correct_count, admin_invincible # admin_invincible をグローバル宣言に追加
    global incorrect_message, incorrect_message_time, last_quiz_time, next_quiz_interval

    # 管理者モードのチェックを最優先
    if user_input.strip().lower() == "admin":
        admin_invincible = True
        quiz_mode = False # クイズモードを終了
        user_input = ""   # 入力をクリア
        incorrect_message = "Admin mode: Invincibility ON!" # フィードバックメッセージ
        incorrect_message_time = time.time()
        # 次のクイズを通常通りスケジュール
        last_quiz_time = time.time()
        next_quiz_interval = random.uniform(quiz_interval_min, quiz_interval_max)
        return # 通常の回答処理をスキップ

    # 通常の回答処理
    if user_input.strip() == correct_answer:
        quiz_mode = False
        user_input = ""
        correct_count += 1
        if correct_count == 6:
            current_elapsed_time = time.time() - start_time
            game_clear_screen(current_elapsed_time, correct_count)

        incorrect_message = "" # 正解時はメッセージをクリア
        last_quiz_time = time.time()
        next_quiz_interval = random.uniform(quiz_interval_min, quiz_interval_max)
    else:
        incorrect_message = "Incorrect answer! Try again."
        incorrect_message_time = time.time()
        user_input = ""
        # quiz_mode は True のまま

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
                handle_quiz_submission() 
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

    if not quiz_mode and time.time() - last_quiz_time > next_quiz_interval:
        quiz_mode = True
        user_input = ""
        incorrect_message = "" # 新しいクイズ開始時にメッセージをクリア

    # --- Bullet Generation ---
    current_cycle_base_interval = base_bullet_interval
    current_slow_factor = 1
    if quiz_mode:
        if correct_count <= 1: current_slow_factor = 10
        elif correct_count <= 3: current_slow_factor = 6
        else: current_slow_factor = 4
        current_cycle_base_interval *= current_slow_factor
    
    interval_for_top_attacks = current_cycle_base_interval
    if correct_count == 5:
        interval_for_top_attacks *= 2.0

    if time.time() - last_top_attack_time > interval_for_top_attacks:
        last_top_attack_time = time.time()
        attack_text = random.choice(attack_texts)
        anchor_x = random.randint(0, WIDTH - 50)
        anchor_y = 0
        bullets.append({
            "rect": pygame.Rect(anchor_x, anchor_y, 1, 1),
            "text": attack_text,
            "pos_x_float": float(anchor_x),
            "pos_y_float": float(anchor_y),
            "direction": "top"
        })

    if correct_count == 5:
        interval_for_other_attacks = current_cycle_base_interval
        if time.time() - last_other_attack_time > interval_for_other_attacks:
            last_other_attack_time = time.time()
            chosen_direction = random.choice(['left', 'right', 'bottom'])
            attack_text = random.choice(attack_texts)
            
            temp_surf = font.render(attack_text, True, BLACK)
            text_w = temp_surf.get_width()
            text_h = temp_surf.get_height()

            anchor_x, anchor_y = 0, 0
            if chosen_direction == 'left':
                anchor_x = 0 - text_w 
                anchor_y = random.randint(15 + text_h, HEIGHT - text_h - 15) 
            elif chosen_direction == 'right':
                anchor_x = WIDTH 
                anchor_y = random.randint(15 + text_h, HEIGHT - text_h - 15)
            elif chosen_direction == 'bottom':
                anchor_x = random.randint(0, WIDTH - text_w)
                anchor_y = HEIGHT + 15 
            
            bullets.append({
                "rect": pygame.Rect(anchor_x, anchor_y, 1, 1),
                "text": attack_text,
                "pos_x_float": float(anchor_x),
                "pos_y_float": float(anchor_y),
                "direction": chosen_direction
            })

    # --- Bullet Movement and Collision ---
    for bullet in bullets[:]:
        bullet_move_speed = base_bullet_speed
        current_bullet_slow_factor = 1
        if quiz_mode:
            if correct_count <= 1: current_bullet_slow_factor = 10
            elif correct_count <= 3: current_bullet_slow_factor = 6
            else: current_bullet_slow_factor = 4
            if current_bullet_slow_factor > 0 :
                 bullet_move_speed /= current_bullet_slow_factor
        else:
            bullet_move_speed *= normal_speed_multiplier

        if bullet['direction'] == 'top':
            bullet['pos_y_float'] += bullet_move_speed
        elif bullet['direction'] == 'bottom':
            bullet['pos_y_float'] -= bullet_move_speed
        elif bullet['direction'] == 'left':
            bullet['pos_x_float'] += bullet_move_speed
        elif bullet['direction'] == 'right':
            bullet['pos_x_float'] -= bullet_move_speed

        bullet["rect"].x = int(bullet["pos_x_float"])
        bullet["rect"].y = int(bullet["pos_y_float"])

        temp_text_surface = font.render(bullet["text"], True, BLACK)
        text_w = temp_text_surface.get_width()
        text_h = temp_text_surface.get_height()
        text_actual_rect = pygame.Rect(bullet["rect"].x, bullet["rect"].y - 15, text_w, text_h)

        if player.colliderect(text_actual_rect) and not admin_invincible: # 無敵でない場合のみ衝突判定
            game_over_wrapper()

        if text_actual_rect.right < -50 or text_actual_rect.left > WIDTH + 50 or \
           text_actual_rect.bottom < -50 or text_actual_rect.top > HEIGHT + 50:
            bullets.remove(bullet)

    # --- Chaser (Homing Attack) ---
    if correct_count >= 3 and chaser is None:
        start_x = max(0, player.x - 100)
        start_y = max(0, player.y - 100)
        chaser_rect = pygame.Rect(start_x, start_y, player.width, player.height)
        chaser = {"rect": chaser_rect, "speed": chaser_speed_base}

    if chaser is not None:
        if not quiz_mode: # クイズモード中は追尾しない
            dx = player.centerx - chaser["rect"].centerx
            dy = player.centery - chaser["rect"].centery
            dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)

            move_x = chaser["speed"] * dx / dist
            move_y = chaser["speed"] * dy / dist

            chaser["rect"].x += int(move_x)
            chaser["rect"].y += int(move_y)

            if chaser["rect"].colliderect(player) and not admin_invincible: # 無敵でない場合のみ衝突判定
                game_over_wrapper()

    draw_game()