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
cursor_position = 0  # カーソル位置を管理

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

# ステージ7用の四角形攻撃システム
import math
square_attacks = []  # 四角形攻撃の弾を管理するリスト
square_attack_phase = 0  # 0: 配置フェーズ, 1: 突進フェーズ, 2: 待機フェーズ, 3: 第2攻撃配置, 4: 第2攻撃中央突進
square_spawn_timer = 0
square_spawn_interval = 0.05  # 弾の出現間隔（高速化）
square_margin = 5  # 画面端からのマージン（10→5にさらに縮小）
square_rush_timer = 0
square_rush_delay = 0.5  # 配置完了から突進開始までの時間（短縮）
total_square_bullets = 60  # 配置する弾の総数（5倍: 12→60）
second_attack_wait_time = 1.0  # 第1攻撃完了から第2攻撃開始までの待機時間
second_attack_positions = []  # 第2攻撃の位置を保存するリスト
stage7_question_delay = 2.0  # 第2攻撃配置完了から問題出題までの時間
stage7_question_timer = 0  # 問題出題タイマー
stage7_question_active = False  # Stage 7の問題出題制御フラグ

# 自動補完機能のための設定
auto_complete_pairs = {
    '(': ')',
    '"': '"',
    "'": "'"
}

def insert_character_at_cursor(text, char, cursor_pos):
    """カーソル位置に文字を挿入"""
    return text[:cursor_pos] + char + text[cursor_pos:]

def handle_auto_complete(char, current_text, cursor_pos):
    """自動補完処理"""
    if char in auto_complete_pairs:
        # 既存の閉じ括弧/引用符をスキップする場合
        if cursor_pos < len(current_text) and current_text[cursor_pos] == auto_complete_pairs[char]:
            return current_text, cursor_pos + 1
        
        # 新しい補完ペアを追加
        new_text = insert_character_at_cursor(current_text, char + auto_complete_pairs[char], cursor_pos)
        return new_text, cursor_pos + 1
    
    return insert_character_at_cursor(current_text, char, cursor_pos), cursor_pos + 1

def reset_stage_systems():
    """すべての攻撃システムをリセット"""
    global bullets, chaser, square_attacks, square_attack_phase, square_spawn_timer, square_rush_timer
    global second_attack_positions, stage7_question_timer, stage7_question_active
    
    # 既存の攻撃をクリア
    bullets.clear()
    chaser = None
    
    # 四角形攻撃システムをリセット
    square_attacks.clear()
    square_attack_phase = 0
    square_spawn_timer = time.time()
    square_rush_timer = 0
    second_attack_positions.clear()
    stage7_question_timer = 0
    stage7_question_active = False

def jump_to_stage(stage_number):
    """指定されたステージにジャンプ"""
    global correct_count, quiz_mode, user_input, cursor_position
    global incorrect_message, incorrect_message_time, last_quiz_time, next_quiz_interval
    
    # ステージ番号を correct_count に変換 (ステージ1 = correct_count 0)
    target_correct_count = max(0, min(stage_number - 1, 3))  # 最大4ステージに変更
    correct_count = target_correct_count
    
    # クイズモードを終了
    quiz_mode = False
    user_input = ""
    cursor_position = 0
    
    # すべての攻撃システムをリセット
    reset_stage_systems()
    
    # メッセージ設定
    if stage_number == 4:  # 新Final Boss
        incorrect_message = f"Jumped to Stage {stage_number} (Final Boss)!"
    else:
        incorrect_message = f"Jumped to Stage {stage_number}!"
    incorrect_message_time = time.time()
    
    # 次のクイズをスケジュール
    last_quiz_time = time.time()
    next_quiz_interval = random.uniform(quiz_interval_min, quiz_interval_max)

def create_square_attack(spawn_order, attack_text):
    """四角形攻撃用の弾を画面の四辺に配置"""
    center_x = WIDTH // 2
    center_y = HEIGHT // 2
    
    # 四角形の周囲に60個の弾を配置
    # 各辺に15個ずつ配置（上、右、下、左）
    bullets_per_side = total_square_bullets // 4
    side = spawn_order // bullets_per_side  # どの辺か（0:上, 1:右, 2:下, 3:左）
    position_on_side = spawn_order % bullets_per_side  # 辺のどの位置か
    
    if side == 0:  # 上辺
        pos_x = square_margin + (WIDTH - 2 * square_margin) * position_on_side / (bullets_per_side - 1)
        pos_y = square_margin
    elif side == 1:  # 右辺
        pos_x = WIDTH - square_margin
        pos_y = square_margin + (HEIGHT - 2 * square_margin) * position_on_side / (bullets_per_side - 1)
    elif side == 2:  # 下辺
        pos_x = WIDTH - square_margin - (WIDTH - 2 * square_margin) * position_on_side / (bullets_per_side - 1)
        pos_y = HEIGHT - square_margin
    else:  # 左辺
        pos_x = square_margin
        pos_y = HEIGHT - square_margin - (HEIGHT - 2 * square_margin) * position_on_side / (bullets_per_side - 1)
    
    # 中央への方向ベクトルを計算
    dx = center_x - pos_x
    dy = center_y - pos_y
    distance = math.sqrt(dx**2 + dy**2)
    dir_x = dx / distance
    dir_y = dy / distance
    
    return {
        "rect": pygame.Rect(int(pos_x), int(pos_y), 1, 1),
        "text": attack_text,
        "pos_x_float": float(pos_x),
        "pos_y_float": float(pos_y),
        "center_x": center_x,
        "center_y": center_y,
        "dir_x": dir_x,
        "dir_y": dir_y,
        "side": side,
        "phase": "positioned",  # "positioned", "rushing"
        "rush_speed": 8.0,  # 突進速度
        "spawn_order": spawn_order
    }

def update_square_attacks():
    """四角形攻撃システムの更新"""
    global square_attack_phase, square_spawn_timer, square_rush_timer
    global stage7_question_timer, stage7_question_active
    
    if correct_count != 3:  # 新Stage 4のみ
        return
    
    current_time = time.time()
    
    # フェーズ0: 弾の瞬間出現
    if square_attack_phase == 0:
        if current_time - square_spawn_timer > square_spawn_interval:
            square_spawn_timer = current_time
            
            # 60個の弾を順次生成（瞬間出現）
            if len(square_attacks) < total_square_bullets:
                attack_text = random.choice(attack_texts)
                square_attacks.append(create_square_attack(len(square_attacks), attack_text))
            
            # 全ての弾の出現完了
            if len(square_attacks) >= total_square_bullets:
                square_attack_phase = 1
                square_rush_timer = current_time
    
    # フェーズ1: 順次突進攻撃
    elif square_attack_phase == 1:
        if current_time - square_rush_timer > square_rush_delay:
            # 配置した順番に突進開始
            for attack in square_attacks:
                if attack["phase"] == "positioned":
                    rush_delay = attack["spawn_order"] * 0.03  # 0.03秒間隔で高速突進
                    if current_time - square_rush_timer - square_rush_delay > rush_delay:
                        attack["phase"] = "rushing"
        
        # 全ての弾が画面外に出たかチェック
        if len(square_attacks) == 0:  # 全ての弾が削除された
            square_attack_phase = 2
            square_rush_timer = current_time  # 待機時間の開始
    
    # フェーズ2: 第2攻撃前の待機
    elif square_attack_phase == 2:
        if current_time - square_rush_timer > second_attack_wait_time:
            square_attack_phase = 3
            square_spawn_timer = current_time
            # 第2攻撃用の位置を記録
            second_attack_positions.clear()
    
    # フェーズ3: 第2攻撃の配置（同じ位置）
    elif square_attack_phase == 3:
        if current_time - square_spawn_timer > square_spawn_interval:
            square_spawn_timer = current_time
            
            # 60個の弾を同じ位置に再配置
            if len(square_attacks) < total_square_bullets:
                attack_text = random.choice(attack_texts)
                new_attack = create_square_attack(len(square_attacks), attack_text)
                # 元の位置情報を保存
                second_attack_positions.append({
                    "original_x": new_attack["pos_x_float"],
                    "original_y": new_attack["pos_y_float"]
                })
                square_attacks.append(new_attack)
            
            # 全ての弾の配置完了
            if len(square_attacks) >= total_square_bullets:
                square_attack_phase = 4
                square_rush_timer = current_time
                # Stage 7専用: 問題出題タイマー開始
                stage7_question_timer = current_time
                stage7_question_active = False  # まだ問題は出題しない
    
    # フェーズ4: 第2攻撃 - ゆっくり中央に向かう攻撃
    elif square_attack_phase == 4:
        if current_time - square_rush_timer > square_rush_delay:
            # 全ての弾が同時に中央に向かって移動開始
            for attack in square_attacks:
                if attack["phase"] == "positioned":
                    attack["phase"] = "slow_center_rush"
                    attack["slow_rush_speed"] = attack["rush_speed"] / 20.0  # 1/10 → 1/20の速度（さらに半分）
    
    # 弾の移動処理
    for attack in square_attacks[:]:
        if attack["phase"] == "rushing":
            # 第1攻撃: 中央を通って反対側に突き抜ける（高速）
            attack["pos_x_float"] += attack["dir_x"] * attack["rush_speed"]
            attack["pos_y_float"] += attack["dir_y"] * attack["rush_speed"]
            attack["rect"].x = int(attack["pos_x_float"])
            attack["rect"].y = int(attack["pos_y_float"])
            
            # 画面外に出た弾を削除
            if (attack["rect"].x < -100 or attack["rect"].x > WIDTH + 100 or 
                attack["rect"].y < -100 or attack["rect"].y > HEIGHT + 100):
                square_attacks.remove(attack)
        
        elif attack["phase"] == "slow_center_rush":
            # 第2攻撃: ゆっくりと中央に向かう
            center_x = WIDTH // 2
            center_y = HEIGHT // 2
            
            # 中央に向かう方向を計算
            dx = center_x - attack["pos_x_float"]
            dy = center_y - attack["pos_y_float"]
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > 1:  # 中央に到達していない
                # 正規化した方向ベクトル × ゆっくりとした速度
                move_x = (dx / distance) * attack["slow_rush_speed"]
                move_y = (dy / distance) * attack["slow_rush_speed"]
                
                attack["pos_x_float"] += move_x
                attack["pos_y_float"] += move_y
                attack["rect"].x = int(attack["pos_x_float"])
                attack["rect"].y = int(attack["pos_y_float"])
            else:
                # 中央に到達したら削除
                square_attacks.remove(attack)
        
        # 衝突判定
        if attack["phase"] in ["positioned", "rushing", "slow_center_rush"]:
            temp_text_surface = font.render(attack["text"], True, BLACK)
            text_w = temp_text_surface.get_width()
            text_h = temp_text_surface.get_height()
            text_actual_rect = pygame.Rect(attack["rect"].x, attack["rect"].y - 15, text_w, text_h)
            
            if player.colliderect(text_actual_rect) and not admin_invincible:
                game_over_wrapper()

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
    global stage7_question_timer, stage7_question_active  # Stage 7問題出題制御変数
    win.fill(BLACK)
    
    player_color_to_draw = WHITE
    if admin_invincible:
        player_color_to_draw = GOLD # 無敵モードなら金色
    pygame.draw.rect(win, player_color_to_draw, player)


    bullet_color_to_use = PROGRAMMING_COLOR
    chaser_color_to_use = ORANGE_COLOR

    if correct_count == 2:  # 新Stage 3 (旧Stage 6): レインボー色
        rainbow_idx_shifter = (rainbow_idx_shifter + 1) % (len(RAINBOW_COLORS) * 3)
        current_rainbow_color = RAINBOW_COLORS[(rainbow_idx_shifter // 3) % len(RAINBOW_COLORS)]
        bullet_color_to_use = current_rainbow_color
        chaser_color_to_use = current_rainbow_color
    elif correct_count == 1:  # 新Stage 2 (旧Stage 5): オレンジ色
        bullet_color_to_use = ORANGE_COLOR

    for bullet_item in bullets:
        text_surface = font.render(bullet_item["text"], True, bullet_color_to_use)
        win.blit(text_surface, (bullet_item["rect"].x, bullet_item["rect"].y - 15))

    # 四角形攻撃の描画
    if correct_count == 3:  # 新Stage 4 (旧Stage 7): Final Boss
        for attack in square_attacks:
            if attack["phase"] == "positioned":
                # 配置完了時は黄色で表示
                attack_color = (255, 255, 100)
            else:
                # 突進中は明るい赤色で表示
                attack_color = (255, 100, 100)
            
            text_surface = font.render(attack["text"], True, attack_color)
            win.blit(text_surface, (attack["rect"].x, attack["rect"].y - 15))

    if chaser is not None:
        pygame.draw.rect(win, chaser_color_to_use, chaser["rect"])

    elapsed_time_current = int(time.time() - start_time)
    current_stage = correct_count + 1  # ステージ番号（1-7）
    time_text_render = font.render(f"Time: {elapsed_time_current}s", True, WHITE)
    correct_text_render = font.render(f"Correct: {correct_count}", True, WHITE)
    stage_text_render = font.render(f"Stage: {current_stage}", True, WHITE)
    win.blit(time_text_render, (WIDTH - 140, 10))
    win.blit(correct_text_render, (WIDTH - 140, 30))
    win.blit(stage_text_render, (WIDTH - 140, 50))

    if quiz_mode:
        # Stage 4専用: 問題出題タイミング制御
        show_quiz = True
        if correct_count == 3:  # Stage 4（Final Boss）の場合
            if stage7_question_timer > 0:  # タイマーが設定されている
                current_time = time.time()
                if current_time - stage7_question_timer < stage7_question_delay:
                    show_quiz = False  # まだ2秒経っていないので問題を表示しない
                elif not stage7_question_active:
                    stage7_question_active = True  # 2秒経ったので問題表示開始
        
        if show_quiz:
            pygame.draw.rect(win, BLACK, (50, 100, 540, 150))
            pygame.draw.rect(win, WHITE, (50, 100, 540, 150), 2)
            question_text = font.render(current_quiz, True, WHITE)
            
            # カーソル位置を考慮したテキスト表示
            prompt = ">> "
            left_part = user_input[:cursor_position]
            right_part = user_input[cursor_position:]
            
            # テキストの幅を測定してカーソル位置を計算
            prompt_width = font.size(prompt)[0]
            left_width = font.size(left_part)[0] if left_part else 0
            
            input_text = font.render(prompt + user_input, True, WHITE)
            win.blit(question_text, (60, 120))
            win.blit(input_text, (60, 150))
            
            # カーソルを描画（点滅効果付き）
            cursor_x = 60 + prompt_width + left_width
            cursor_y = 150
            cursor_height = font.get_height()
            
            # 点滅効果（1秒周期）
            if int(time.time() * 2) % 2:  # 0.5秒ごとに点滅
                pygame.draw.line(win, WHITE, (cursor_x, cursor_y), (cursor_x, cursor_y + cursor_height), 2)

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
    global quiz_mode, user_input, correct_count, admin_invincible, cursor_position # cursor_position を追加
    global incorrect_message, incorrect_message_time, last_quiz_time, next_quiz_interval

    # 管理者モードのチェックを最優先
    user_command = user_input.strip().lower()
    
    # 通常の無敵モード admin
    if user_command == "admin":
        admin_invincible = True
        quiz_mode = False # クイズモードを終了
        user_input = ""   # 入力をクリア
        cursor_position = 0  # カーソル位置もリセット
        incorrect_message = "Admin mode: Invincibility ON!" # フィードバックメッセージ
        incorrect_message_time = time.time()
        # 次のクイズを通常通りスケジュール
        last_quiz_time = time.time()
        next_quiz_interval = random.uniform(quiz_interval_min, quiz_interval_max)
        return # 通常の回答処理をスキップ
    
    # ステージスキップ機能 admin + 数字
    elif user_command.startswith("admin") and len(user_command) > 5:
        try:
            # admin後の数字を抽出
            stage_str = user_command[5:]  # "admin"の後の部分
            stage_number = int(stage_str)
            
            if 1 <= stage_number <= 4:  # ステージ1-4の範囲チェック（4ステージ構成）
                jump_to_stage(stage_number)
                return  # 通常の回答処理をスキップ
            else:
                incorrect_message = "Stage number must be 1-4!"
                incorrect_message_time = time.time()
                user_input = ""
                cursor_position = 0
                return
        except ValueError:
            # 数字でない場合は通常の間違い処理に続行
            pass

    # 通常の回答処理
    if user_input.strip() == correct_answer:
        quiz_mode = False
        user_input = ""
        cursor_position = 0  # カーソル位置もリセット
        correct_count += 1
        if correct_count == 4:  # 4問正解でゲームクリア（新構成）
            current_elapsed_time = time.time() - start_time
            game_clear_screen(current_elapsed_time, correct_count)

        incorrect_message = "" # 正解時はメッセージをクリア
        last_quiz_time = time.time()
        next_quiz_interval = random.uniform(quiz_interval_min, quiz_interval_max)
        
        # ステージ7開始時の初期化
        if correct_count == 3:  # 新Stage 4でSquare攻撃開始
            # 既存の攻撃をクリア
            reset_stage_systems()
    else:
        incorrect_message = "Incorrect answer! Try again."
        incorrect_message_time = time.time()
        user_input = ""
        cursor_position = 0  # カーソル位置もリセット
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
                if cursor_position > 0:
                    user_input = user_input[:cursor_position-1] + user_input[cursor_position:]
                    cursor_position -= 1
            elif event.key == pygame.K_DELETE:
                if cursor_position < len(user_input):
                    user_input = user_input[:cursor_position] + user_input[cursor_position+1:]
            elif event.key == pygame.K_LEFT:
                cursor_position = max(0, cursor_position - 1)
            elif event.key == pygame.K_RIGHT:
                cursor_position = min(len(user_input), cursor_position + 1)
            elif event.key == pygame.K_HOME:
                cursor_position = 0
            elif event.key == pygame.K_END:
                cursor_position = len(user_input)
            elif event.key == pygame.K_RETURN:
                handle_quiz_submission() 
            elif event.unicode and event.unicode.isprintable():
                # 自動補完機能を適用
                user_input, cursor_position = handle_auto_complete(event.unicode, user_input, cursor_position)

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
        cursor_position = 0  # カーソル位置をリセット
        incorrect_message = "" # 新しいクイズ開始時にメッセージをクリア

    # --- Bullet Generation ---
    # ステージ7では既存の攻撃を停止
    if correct_count < 6:
        current_cycle_base_interval = base_bullet_interval
        current_slow_factor = 1
        if quiz_mode:
            if correct_count <= 1: current_slow_factor = 10
            elif correct_count <= 3: current_slow_factor = 6
            else: current_slow_factor = 4
            current_cycle_base_interval *= current_slow_factor
        
        interval_for_top_attacks = current_cycle_base_interval
        if correct_count >= 2:  # 新Stage 3,4で上攻撃の間隔を2倍に（4方向攻撃がある時）
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

        if correct_count == 2:  # 新Stage 3のみで4方向攻撃
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
    
    # 新Stage 4の四角形攻撃システム
    if correct_count == 3:
        update_square_attacks()

    # --- Bullet Movement and Collision ---
    # 新Stage 4では既存の弾システムを停止
    if correct_count < 3:
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
    # ステージ7では追尾攻撃を停止
    if correct_count >= 1 and correct_count < 3 and chaser is None:  # 新Stage 2,3で追跡攻撃
        start_x = max(0, player.x - 100)
        start_y = max(0, player.y - 100)
        chaser_rect = pygame.Rect(start_x, start_y, player.width, player.height)
        chaser = {"rect": chaser_rect, "speed": chaser_speed_base}

    if chaser is not None and correct_count < 6:
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
    
    # ステージ7開始時にチェイサーを削除
    if correct_count == 3 and chaser is not None:  # 新Stage 4でchaser停止
        chaser = None

    draw_game()