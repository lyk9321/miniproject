# typing_game_v7.py
# 한컴타자연습 스타일의 파이썬 타자 연습 게임
# v6 + 베네치아 클래식 스타일 (사운드/애니메이션 없음, 색감/배경만 변경)
# 실행 방법: python typing_game_v7.py
#
# [이번 버전 추가 사항]
#  • 하늘 → 수평선 → 물 그라디언트 배경
#  • 정적 구름 장식 (움직임 없음)
#  • 크림/갈색 톤의 따뜻한 클래식 UI
#  • 게임 로직(v6)은 그대로 유지

import pygame
import random
import sys
import csv
import os


# =====================================================
# 0. 배포(EXE) 환경까지 고려한 파일 경로 설정
# =====================================================
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CSV_PATH = os.path.join(BASE_DIR, "words.csv")


# =====================================================
# 1. 게임 상태 상수
# =====================================================
GAME_STATE_MENU = "menu"
GAME_STATE_PLAYING = "playing"
GAME_STATE_ESC_MENU = "esc_menu"
GAME_STATE_GAME_OVER = "game_over"


# =====================================================
# 2. 화면 / 레이아웃
# =====================================================
WIDTH = 1000
HEIGHT = 750
FPS = 60

TOP_INFO_HEIGHT = 60   # 점수판 영역 (단어는 그 아래부터 떨어짐)

# 입력창 (화면 가로 중앙 정렬)
INPUT_HEIGHT = 60
INPUT_WIDTH = int(WIDTH * 0.5)
INPUT_X = (WIDTH - INPUT_WIDTH) // 2
INPUT_Y = HEIGHT - INPUT_HEIGHT - 15
INPUT_PADDING = 12
GAMEOVER_LINE_Y = INPUT_Y   # 게임오버 판정선 = 수평선


# =====================================================
# 3. 🎨 베네치아 클래식 색감
# =====================================================
# --- 배경 그라디언트 ---
SKY_TOP = (155, 200, 230)         # 위쪽 하늘 - 부드러운 푸른빛
SKY_BOTTOM = (215, 232, 242)      # 수평선 직전 - 옅은 하늘 (햇빛 받는 느낌)
WATER_TOP = (110, 160, 195)       # 수평선 바로 아래 - 청록빛 물
WATER_BOTTOM = (55, 105, 150)     # 깊은 물 - 짙은 청색
HORIZON_COLOR = (90, 130, 170)    # 수평선 강조선
CLOUD_COLOR = (252, 250, 245)     # 따뜻한 흰색 구름
CLOUD_SHADOW = (220, 225, 235)    # 구름 아랫부분 살짝 그림자

# --- 점수판 (상단 크림색 패널) ---
PANEL_BG = (248, 240, 220)        # 따뜻한 크림색
PANEL_BORDER = (160, 130, 80)     # 따뜻한 갈색 (나무 느낌)

# --- 단어 색 ---
WORD_COLOR = (30, 45, 75)         # 진한 남색 (하늘 위에 대비)
SPECIAL_WORD_COLOR = (200, 65, 60) # 코랄 레드 (베네치아 노을 톤)

# --- 입력창 ---
INPUT_BG = (252, 248, 238)        # 매우 따뜻한 흰색
INPUT_TEXT_COLOR = (35, 35, 45)
COMPOSING_COLOR = (100, 130, 180)
CURSOR_COLOR = (35, 35, 45)

# --- 정보/타이틀 ---
INFO_COLOR = (40, 60, 105)
TITLE_COLOR = (35, 55, 100)

# --- 버튼/팝업 ---
BUTTON_COLOR = (240, 230, 210)
BUTTON_BORDER = (160, 130, 80)
POPUP_BG = (248, 240, 220)
POPUP_BORDER = (160, 130, 80)
POPUP_SHADOW = (50, 50, 70)

# --- 기타 ---
BORDER_COLOR = (160, 130, 80)
HELP_COLOR = (110, 130, 155)
GAMEOVER_COLOR = (180, 50, 50)
ANNOUNCE_BG = (252, 245, 220)
ANNOUNCE_TEXT = (110, 80, 35)


# =====================================================
# 4. 게임 설정값
# =====================================================
# 커서
CURSOR_BLINK_MS = 500
CURSOR_WIDTH = 2

# 단어 깜빡임
BLINK_CYCLE_MS = 1000
BLINK_VISIBLE_MS = 900
BLINK_LEVEL_THRESHOLD = 5

# 입력 모드 안내
ANNOUNCE_DURATION_MS = 3000

# 특수 단어
SPECIAL_WORD_SPEED = 2.0
SPECIAL_WORD_SPAWN_MIN_MS = 20000
SPECIAL_WORD_SPAWN_MAX_MS = 30000
SPECIAL_WORD_BONUS_SCORE = 30

# 난이도
INITIAL_SPEED = 1.0
SPEED_STEP = 0.5
MAX_SPEED = 6.0
INITIAL_SPAWN_MS = 2000
MIN_SPAWN_MS = 800
SPAWN_STEP_MS = 100
LEVEL_UP_SCHEDULE = [30, 20]
LEVEL_UP_FIXED_INTERVAL = 15

# 기본 단어 리스트 (CSV 없을 때 백업)
DEFAULT_ENGLISH_WORDS = [
    {"word": "apple",    "difficulty": 1, "category": "food"},
    {"word": "banana",   "difficulty": 1, "category": "food"},
    {"word": "book",     "difficulty": 1, "category": "object"},
    {"word": "cat",      "difficulty": 1, "category": "animal"},
    {"word": "dog",      "difficulty": 1, "category": "animal"},
    {"word": "school",   "difficulty": 1, "category": "place"},
    {"word": "game",     "difficulty": 1, "category": "object"},
    {"word": "keyboard", "difficulty": 2, "category": "computer"},
    {"word": "network",  "difficulty": 2, "category": "computer"},
    {"word": "function", "difficulty": 3, "category": "programming"},
    {"word": "variable", "difficulty": 3, "category": "programming"},
    {"word": "optimization", "difficulty": 4, "category": "data"},
]
DEFAULT_KOREAN_WORDS = [
    {"word": "사과",       "difficulty": 1, "category": "음식"},
    {"word": "책",         "difficulty": 1, "category": "물건"},
    {"word": "강아지",     "difficulty": 1, "category": "동물"},
    {"word": "학교",       "difficulty": 1, "category": "장소"},
    {"word": "게임",       "difficulty": 1, "category": "활동"},
    {"word": "키보드",     "difficulty": 2, "category": "컴퓨터"},
    {"word": "네트워크",   "difficulty": 2, "category": "컴퓨터"},
    {"word": "알고리즘",   "difficulty": 3, "category": "프로그래밍"},
    {"word": "데이터분석", "difficulty": 3, "category": "데이터"},
    {"word": "최적화모델", "difficulty": 4, "category": "데이터"},
]


# =====================================================
# 5. 전역 상태 변수
# =====================================================
game_state = GAME_STATE_MENU

words_on_screen = []
special_words_on_screen = []

input_text = ""
composition_text = ""

score = 0
level = 1
current_speed = INITIAL_SPEED
current_spawn_ms = INITIAL_SPAWN_MS

last_spawn_time = 0
game_start_time = 0
last_level_up_time = 0
level_up_index = 0
next_special_spawn_time = 0

pause_start_time = 0
total_paused_time = 0

selected_language = None
word_list = []
english_words = []
korean_words = []

word_bag = []
last_word_bag_level_key = None
last_emitted_word = None

# 폰트
font_word = None
font_input = None
font_info = None
font_title = None
font_gameover = None
font_help = None
font_popup = None
font_announce = None

# 🎨 미리 그려놓은 배경 Surface (성능 최적화 - 매 프레임 다시 그리지 않음)
background_surface = None


# =====================================================
# 6. 시간 함수 (일시정지 보정)
# =====================================================
def get_game_time():
    return pygame.time.get_ticks() - total_paused_time

def pause_game_timer():
    global pause_start_time
    pause_start_time = pygame.time.get_ticks()

def resume_game_timer():
    global total_paused_time
    total_paused_time += pygame.time.get_ticks() - pause_start_time


# =====================================================
# 7. 한글 폰트 찾기
# =====================================================
def get_font(size):
    """한글 표시 가능한 폰트 찾기."""
    korean_font_candidates = [
        'malgungothic', 'applegothic', 'applesdgothicneo',
        'nanumgothic', 'notosanscjkkr', 'gulim', 'dotum', 'batang'
    ]
    available = pygame.font.get_fonts()
    for name in korean_font_candidates:
        if name in available:
            return pygame.font.SysFont(name, size)
    return pygame.font.SysFont(None, size)


# =====================================================
# 8. 🎨 배경 Surface 생성 (한 번만!)
# =====================================================
def lerp_color(c1, c2, ratio):
    """두 색을 ratio(0~1)만큼 섞기. 그라디언트용."""
    r = int(c1[0] + (c2[0] - c1[0]) * ratio)
    g = int(c1[1] + (c2[1] - c1[1]) * ratio)
    b = int(c1[2] + (c2[2] - c1[2]) * ratio)
    return (r, g, b)


def draw_cloud(surface, cx, cy, scale=1.0):
    """
    구름 하나 그리기.
    여러 흰색 타원을 겹쳐서 폭신폭신한 모양 만들기.
    """
    # 살짝 어두운 아랫부분 (그림자) → 위에 밝은 부분 덮어쓰기
    shadow_offset = int(4 * scale)
    parts = [
        (cx - 35*scale, cy - 12*scale, 70*scale, 32*scale),
        (cx - 18*scale, cy - 25*scale, 55*scale, 38*scale),
        (cx + 12*scale, cy - 18*scale, 50*scale, 32*scale),
        (cx + 30*scale, cy - 8*scale,  45*scale, 28*scale),
    ]
    # 그림자
    for px, py, pw, ph in parts:
        pygame.draw.ellipse(surface, CLOUD_SHADOW,
                            (px, py + shadow_offset, pw, ph))
    # 본체
    for px, py, pw, ph in parts:
        pygame.draw.ellipse(surface, CLOUD_COLOR, (px, py, pw, ph))


def create_background_surface():
    """
    하늘 → 수평선 → 물 그라디언트와 정적 구름이 그려진 배경 Surface 생성.
    매 프레임 다시 그리지 않고 이걸 통째로 blit해서 성능 확보.
    """
    bg = pygame.Surface((WIDTH, HEIGHT))

    # === 1. 하늘 영역 (y=0 ~ 수평선) ===
    # 수평선 = 게임오버 판정선 (단어가 닿으면 "물에 빠지는" 느낌)
    for y in range(GAMEOVER_LINE_Y):
        ratio = y / GAMEOVER_LINE_Y
        color = lerp_color(SKY_TOP, SKY_BOTTOM, ratio)
        pygame.draw.line(bg, color, (0, y), (WIDTH, y))

    # === 2. 정적 구름 (하늘 영역에만, 움직임 없음) ===
    # 점수판 아래 ~ 화면 중앙 정도에 자연스럽게 분산 배치
    cloud_positions = [
        (170, 130, 0.9),
        (520, 95, 1.1),
        (820, 160, 0.85),
        (310, 250, 0.7),
        (700, 310, 0.95),
        (120, 380, 0.8),
        (880, 430, 0.75),
        (450, 470, 0.85),
    ]
    for cx, cy, scale in cloud_positions:
        draw_cloud(bg, cx, cy, scale)

    # === 3. 수평선 강조선 ===
    pygame.draw.line(bg, HORIZON_COLOR,
                     (0, GAMEOVER_LINE_Y), (WIDTH, GAMEOVER_LINE_Y), 2)

    # === 4. 물 영역 (수평선 ~ 화면 끝) ===
    water_height = HEIGHT - GAMEOVER_LINE_Y
    for y in range(GAMEOVER_LINE_Y, HEIGHT):
        ratio = (y - GAMEOVER_LINE_Y) / water_height
        color = lerp_color(WATER_TOP, WATER_BOTTOM, ratio)
        pygame.draw.line(bg, color, (0, y), (WIDTH, y))

    return bg


# =====================================================
# 9. CSV 로딩
# =====================================================
def load_words_from_csv(filepath):
    if not os.path.exists(filepath):
        print(f"[알림] '{filepath}' 파일 없음 → 기본 단어 리스트 사용")
        return DEFAULT_ENGLISH_WORDS.copy(), DEFAULT_KOREAN_WORDS.copy(), False

    eng_words, kor_words = [], []
    try:
        with open(filepath, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                language = (row.get("language") or "").strip().lower()
                word = (row.get("word") or "").strip()
                if not word:
                    continue
                try:
                    difficulty = int((row.get("difficulty") or "1").strip())
                except ValueError:
                    difficulty = 1
                difficulty = max(1, min(4, difficulty))
                category = (row.get("category") or "").strip()
                entry = {"word": word, "difficulty": difficulty, "category": category}
                if language == "en":
                    eng_words.append(entry)
                elif language == "ko":
                    kor_words.append(entry)

        if not eng_words and not kor_words:
            print("[알림] CSV에 유효 단어 없음 → 기본 리스트 사용")
            return DEFAULT_ENGLISH_WORDS.copy(), DEFAULT_KOREAN_WORDS.copy(), False
        if not eng_words:
            eng_words = DEFAULT_ENGLISH_WORDS.copy()
        if not kor_words:
            kor_words = DEFAULT_KOREAN_WORDS.copy()
        print(f"[OK] 영어 {len(eng_words)}개, 한국어 {len(kor_words)}개 로드")
        return eng_words, kor_words, True
    except Exception as e:
        print(f"[오류] CSV 읽기 실패 ({e}) → 기본 리스트 사용")
        return DEFAULT_ENGLISH_WORDS.copy(), DEFAULT_KOREAN_WORDS.copy(), False


# =====================================================
# 10. 난이도별 출제 & Word Bag
# =====================================================
def get_level_key(lv):
    if lv <= 2: return "EASY"
    elif lv <= 4: return "BASIC"
    elif lv <= 6: return "MID"
    else: return "ALL"

def get_allowed_difficulties_by_level(lv):
    if lv <= 2:    return {1: 10}
    elif lv <= 4:  return {1: 4, 2: 6}
    elif lv <= 6:  return {2: 7, 3: 3}
    else:          return {1: 2, 2: 4, 3: 3, 4: 1}

def build_word_bag_by_level():
    weights = get_allowed_difficulties_by_level(level)
    bag = []
    for difficulty, weight in weights.items():
        matching = [w for w in word_list if w["difficulty"] == difficulty]
        for _ in range(weight):
            bag.extend(matching)
    random.shuffle(bag)
    return bag

def get_next_word_by_level():
    global word_bag, last_word_bag_level_key, last_emitted_word
    current_key = get_level_key(level)
    if not word_bag or current_key != last_word_bag_level_key:
        word_bag = build_word_bag_by_level()
        last_word_bag_level_key = current_key
    if not word_bag:
        return None
    word_entry = word_bag.pop()
    if (last_emitted_word is not None
            and word_entry["word"] == last_emitted_word
            and len(word_bag) > 0):
        alternative = word_bag.pop(0)
        word_bag.insert(0, word_entry)
        word_entry = alternative
    last_emitted_word = word_entry["word"]
    return word_entry


# =====================================================
# 11. 게임 초기화 & 상태 전환
# =====================================================
def init_game():
    global words_on_screen, special_words_on_screen
    global input_text, composition_text, score, level
    global current_speed, current_spawn_ms
    global last_spawn_time, game_start_time, last_level_up_time, level_up_index
    global total_paused_time, next_special_spawn_time
    global word_bag, last_word_bag_level_key, last_emitted_word

    words_on_screen = []
    special_words_on_screen = []
    input_text = ""
    composition_text = ""
    score = 0
    level = 1
    current_speed = INITIAL_SPEED
    current_spawn_ms = INITIAL_SPAWN_MS
    total_paused_time = 0

    now = pygame.time.get_ticks()
    last_spawn_time = now
    game_start_time = now
    last_level_up_time = now
    level_up_index = 0

    word_bag = []
    last_word_bag_level_key = None
    last_emitted_word = None

    schedule_next_special_word()


def start_playing():
    global game_state
    init_game()
    pygame.key.start_text_input()
    input_rect = pygame.Rect(INPUT_X, INPUT_Y, INPUT_WIDTH, INPUT_HEIGHT)
    pygame.key.set_text_input_rect(input_rect)
    game_state = GAME_STATE_PLAYING


def reset_current_game():
    start_playing()


def return_to_menu():
    global game_state, selected_language, word_list, input_text, composition_text
    game_state = GAME_STATE_MENU
    selected_language = None
    word_list = []
    input_text = ""
    composition_text = ""
    pygame.key.stop_text_input()


def quit_program():
    pygame.quit()
    sys.exit()


# =====================================================
# 12. 단어 생성 / 이동
# =====================================================
def create_word():
    entry = get_next_word_by_level()
    if entry is None:
        return
    text = entry["word"]
    word_surface = font_word.render(text, True, WORD_COLOR)
    word_width = word_surface.get_width()
    x = random.randint(0, max(0, WIDTH - word_width))
    y = TOP_INFO_HEIGHT
    words_on_screen.append({"text": text, "x": x, "y": y})


def update_words():
    for word in words_on_screen:
        word["y"] += current_speed
        if word["y"] >= GAMEOVER_LINE_Y:
            enter_game_over_state()
            break


def enter_game_over_state():
    global game_state
    game_state = GAME_STATE_GAME_OVER
    pygame.key.stop_text_input()


# =====================================================
# 13. 특수 단어
# =====================================================
def schedule_next_special_word():
    global next_special_spawn_time
    delay = random.randint(SPECIAL_WORD_SPAWN_MIN_MS, SPECIAL_WORD_SPAWN_MAX_MS)
    next_special_spawn_time = get_game_time() + delay


def create_special_word():
    if len(special_words_on_screen) > 0:
        return
    candidates = [w for w in word_list if w["difficulty"] in (1, 2)]
    if not candidates:
        candidates = word_list
    if not candidates:
        return
    entry = random.choice(candidates)
    text = entry["word"]
    word_surface = font_word.render(text, True, SPECIAL_WORD_COLOR)
    word_width = word_surface.get_width()
    y_min = TOP_INFO_HEIGHT + 20
    y_max = GAMEOVER_LINE_Y - 50
    if y_max <= y_min:
        y_max = y_min + 1
    y = random.randint(y_min, y_max)
    special_words_on_screen.append({
        "text": text, "x": -word_width, "y": y,
        "speed": SPECIAL_WORD_SPEED, "width": word_width,
    })


def update_special_words():
    for sw in special_words_on_screen[:]:
        sw["x"] += sw["speed"]
        if sw["x"] > WIDTH:
            special_words_on_screen.remove(sw)


def clear_all_visible_words():
    count = len(words_on_screen)
    words_on_screen.clear()
    return count


# =====================================================
# 14. 입력 검사
# =====================================================
def check_special_word_input():
    global input_text, composition_text, score
    typed = input_text.strip()
    if typed == "":
        return False
    for sw in special_words_on_screen:
        if sw["text"] == typed:
            cleared_count = clear_all_visible_words()
            special_words_on_screen.remove(sw)
            score += cleared_count * 10 + SPECIAL_WORD_BONUS_SCORE
            input_text = ""
            composition_text = ""
            return True
    return False


def check_input():
    global input_text, composition_text, score
    if check_special_word_input():
        return
    typed = input_text.strip()
    if typed == "":
        input_text = ""
        composition_text = ""
        return
    matched_index = -1
    max_y = -1
    for i, word in enumerate(words_on_screen):
        if word["text"] == typed and word["y"] > max_y:
            max_y = word["y"]
            matched_index = i
    if matched_index >= 0:
        words_on_screen.pop(matched_index)
        score += 10
    input_text = ""
    composition_text = ""


# =====================================================
# 15. 난이도 조정
# =====================================================
def update_difficulty():
    global current_speed, current_spawn_ms, level
    global last_level_up_time, level_up_index
    now = get_game_time()
    elapsed_since_levelup = now - last_level_up_time
    if level_up_index < len(LEVEL_UP_SCHEDULE):
        interval_seconds = LEVEL_UP_SCHEDULE[level_up_index]
    else:
        interval_seconds = LEVEL_UP_FIXED_INTERVAL
    if elapsed_since_levelup >= interval_seconds * 1000:
        level += 1
        current_speed = min(current_speed + SPEED_STEP, MAX_SPEED)
        current_spawn_ms = max(current_spawn_ms - SPAWN_STEP_MS, MIN_SPAWN_MS)
        last_level_up_time = now
        if level_up_index < len(LEVEL_UP_SCHEDULE):
            level_up_index += 1


# =====================================================
# 16. 커서 / 단어 깜빡임
# =====================================================
def should_show_cursor():
    if len(input_text) > 0 or len(composition_text) > 0:
        return True
    now = pygame.time.get_ticks()
    return (now // CURSOR_BLINK_MS) % 2 == 0


def should_show_words():
    if level < BLINK_LEVEL_THRESHOLD:
        return True
    now_in_cycle = get_game_time() % BLINK_CYCLE_MS
    return now_in_cycle < BLINK_VISIBLE_MS


# =====================================================
# 17. ESC 메뉴
# =====================================================
def open_esc_menu():
    global game_state
    game_state = GAME_STATE_ESC_MENU
    pause_game_timer()
    pygame.key.stop_text_input()


def close_esc_menu():
    global game_state
    resume_game_timer()
    pygame.key.start_text_input()
    input_rect = pygame.Rect(INPUT_X, INPUT_Y, INPUT_WIDTH, INPUT_HEIGHT)
    pygame.key.set_text_input_rect(input_rect)
    game_state = GAME_STATE_PLAYING


# =====================================================
# 18. 그리기 함수들
# =====================================================
def draw_score_panel(screen):
    """
    상단 점수판 (크림색 패널 + 갈색 테두리).
    한컴타자연습의 클래식한 느낌을 위해 따뜻한 톤으로 표시.
    """
    # 패널 배경
    pygame.draw.rect(screen, PANEL_BG, (0, 0, WIDTH, TOP_INFO_HEIGHT))
    # 패널 아래 구분선 (살짝 굵게)
    pygame.draw.line(screen, PANEL_BORDER,
                     (0, TOP_INFO_HEIGHT), (WIDTH, TOP_INFO_HEIGHT), 2)

    # 점수/레벨/시간 텍스트
    elapsed_sec = (get_game_time() - game_start_time) // 1000
    minutes = elapsed_sec // 60
    seconds = elapsed_sec % 60
    info_text = f"Score: {score}    Level: {level}    Time: {minutes:02d}:{seconds:02d}"
    info_surface = font_info.render(info_text, True, INFO_COLOR)
    screen.blit(info_surface, (15, 15))


def draw_menu(screen):
    """언어 선택 화면 - 베네치아 배경 위에 메뉴 표시."""
    # 배경 (그라디언트 + 구름)
    screen.blit(background_surface, (0, 0))

    # 제목
    title_surface = font_title.render("Typing Game / 타자 연습", True, TITLE_COLOR)
    screen.blit(title_surface, title_surface.get_rect(center=(WIDTH // 2, 150)))

    # 안내
    guide = font_info.render("언어를 선택하세요 / Select Language", True, INFO_COLOR)
    screen.blit(guide, guide.get_rect(center=(WIDTH // 2, 250)))

    # 버튼 1: English
    btn1_rect = pygame.Rect(WIDTH // 2 - 180, 340, 360, 80)
    pygame.draw.rect(screen, BUTTON_COLOR, btn1_rect, border_radius=10)
    pygame.draw.rect(screen, BUTTON_BORDER, btn1_rect, 3, border_radius=10)
    btn1_text = font_info.render("[ 1 ]  English", True, TITLE_COLOR)
    screen.blit(btn1_text, btn1_text.get_rect(center=btn1_rect.center))

    # 버튼 2: 한국어
    btn2_rect = pygame.Rect(WIDTH // 2 - 180, 445, 360, 80)
    pygame.draw.rect(screen, BUTTON_COLOR, btn2_rect, border_radius=10)
    pygame.draw.rect(screen, BUTTON_BORDER, btn2_rect, 3, border_radius=10)
    btn2_text = font_info.render("[ 2 ]  한국어", True, TITLE_COLOR)
    screen.blit(btn2_text, btn2_text.get_rect(center=btn2_rect.center))

    # 안내
    info = font_info.render("ESC: 종료 / Quit", True, (90, 100, 120))
    screen.blit(info, info.get_rect(center=(WIDTH // 2, 660)))


def draw_game(screen):
    """게임 플레이 화면."""
    # === 1. 베네치아 배경 (하늘+물+구름) ===
    screen.blit(background_surface, (0, 0))

    # === 2. 일반 단어 (깜빡임 적용) ===
    show_words = should_show_words()
    if show_words:
        for word in words_on_screen:
            surface = font_word.render(word["text"], True, WORD_COLOR)
            screen.blit(surface, (word["x"], word["y"]))

    # === 3. 특수 단어 (코랄 레드) ===
    for sw in special_words_on_screen:
        surface = font_word.render(sw["text"], True, SPECIAL_WORD_COLOR)
        screen.blit(surface, (sw["x"], sw["y"]))

    # === 4. 점수판 (배경 위에 덮어쓰기) ===
    # 단어가 점수판 영역과 겹칠 일은 없지만 안전하게 위에 덮음
    draw_score_panel(screen)

    # === 5. 입력창 (수평선 위에 살짝 떠 있는 패널 느낌) ===
    pygame.draw.rect(screen, INPUT_BG, (INPUT_X, INPUT_Y, INPUT_WIDTH, INPUT_HEIGHT))
    pygame.draw.rect(screen, BORDER_COLOR, (INPUT_X, INPUT_Y, INPUT_WIDTH, INPUT_HEIGHT), 3)

    text_x = INPUT_X + INPUT_PADDING
    text_y = INPUT_Y + INPUT_PADDING

    # 확정 글자
    confirmed_width = 0
    if input_text:
        confirmed_surface = font_input.render(input_text, True, INPUT_TEXT_COLOR)
        screen.blit(confirmed_surface, (text_x, text_y))
        confirmed_width = confirmed_surface.get_width()

    # 조합 중 글자 + 밑줄
    composing_width = 0
    if composition_text:
        composing_surface = font_input.render(composition_text, True, COMPOSING_COLOR)
        screen.blit(composing_surface, (text_x + confirmed_width, text_y))
        underline_y = text_y + composing_surface.get_height() - 2
        pygame.draw.line(screen, COMPOSING_COLOR,
                         (text_x + confirmed_width, underline_y),
                         (text_x + confirmed_width + composing_surface.get_width(), underline_y),
                         2)
        composing_width = composing_surface.get_width()

    # 커서
    if should_show_cursor():
        cursor_x = text_x + confirmed_width + composing_width
        cursor_y_top = text_y + 2
        cursor_y_bottom = text_y + font_input.get_height() - 2
        pygame.draw.line(screen, CURSOR_COLOR,
                         (cursor_x, cursor_y_top),
                         (cursor_x, cursor_y_bottom),
                         CURSOR_WIDTH)

    # === 6. 도움말 (오른쪽 위) ===
    draw_help_text(screen)

    # === 7. 언어 모드 안내 (게임 시작 후 잠깐) ===
    draw_language_announcement(screen)


def draw_help_text(screen):
    if game_state != GAME_STATE_PLAYING:
        return
    text = "ESC: 메뉴"
    surface = font_help.render(text, True, HELP_COLOR)
    x = WIDTH - 15 - surface.get_width()
    y = 15
    screen.blit(surface, (x, y))


def draw_language_announcement(screen):
    elapsed = get_game_time() - game_start_time
    if elapsed > ANNOUNCE_DURATION_MS:
        return
    if selected_language == "korean":
        text = "한국어 모드입니다. 한글 입력 상태에서 플레이하세요."
    else:
        text = "English mode. Please use English keyboard input."
    surface = font_announce.render(text, True, ANNOUNCE_TEXT)
    padding_x = 16
    padding_y = 8
    box_width = surface.get_width() + padding_x * 2
    box_height = surface.get_height() + padding_y * 2
    box_x = (WIDTH - box_width) // 2
    box_y = TOP_INFO_HEIGHT + 15
    pygame.draw.rect(screen, ANNOUNCE_BG,
                     (box_x, box_y, box_width, box_height), border_radius=6)
    pygame.draw.rect(screen, ANNOUNCE_TEXT,
                     (box_x, box_y, box_width, box_height), 1, border_radius=6)
    screen.blit(surface, (box_x + padding_x, box_y + padding_y))


def draw_popup_box(screen, lines, title_first=True):
    box_width = 620
    line_height = font_popup.get_height() + 8
    box_height = 40 + len(lines) * line_height + 20
    box_x = (WIDTH - box_width) // 2
    box_y = (HEIGHT - box_height) // 2

    shadow = pygame.Surface((box_width, box_height))
    shadow.set_alpha(60)
    shadow.fill(POPUP_SHADOW)
    screen.blit(shadow, (box_x + 6, box_y + 6))

    pygame.draw.rect(screen, POPUP_BG,
                     (box_x, box_y, box_width, box_height), border_radius=12)
    pygame.draw.rect(screen, POPUP_BORDER,
                     (box_x, box_y, box_width, box_height), 3, border_radius=12)

    current_y = box_y + 30
    for i, line in enumerate(lines):
        color = TITLE_COLOR if (i == 0 and title_first) else INFO_COLOR
        surface = font_popup.render(line, True, color)
        rect = surface.get_rect(center=(WIDTH // 2, current_y + font_popup.get_height() // 2))
        screen.blit(surface, rect)
        current_y += line_height


def draw_esc_menu(screen):
    draw_popup_box(screen, [
        "메뉴",
        "",
        "T: 현재 게임 다시 시작",
        "Q: 메인 메뉴로 나가기",
        "X: 프로그램 종료",
        "ESC: 게임으로 돌아가기",
    ])


def draw_game_over(screen):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((255, 250, 240))   # 따뜻한 톤 오버레이
    screen.blit(overlay, (0, 0))

    go_surface = font_gameover.render("GAME OVER", True, GAMEOVER_COLOR)
    screen.blit(go_surface, go_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 160)))

    score_text = f"최종 점수 / Final Score: {score}"
    score_surface = font_info.render(score_text, True, TITLE_COLOR)
    screen.blit(score_surface, score_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 70)))

    menu_title = font_popup.render("메뉴", True, TITLE_COLOR)
    screen.blit(menu_title, menu_title.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 5)))

    lines = [
        "T: 같은 언어로 다시 시작",
        "Q: 메인 메뉴로 이동",
        "X: 프로그램 종료",
    ]
    y = HEIGHT // 2 + 55
    for line in lines:
        s = font_info.render(line, True, INFO_COLOR)
        screen.blit(s, s.get_rect(center=(WIDTH // 2, y)))
        y += font_info.get_height() + 6


# =====================================================
# 19. 이벤트 처리
# =====================================================
def handle_event_menu(event):
    global selected_language, word_list
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_1:
            selected_language = "english"
            word_list = english_words
            start_playing()
        elif event.key == pygame.K_2:
            selected_language = "korean"
            word_list = korean_words
            start_playing()
        elif event.key == pygame.K_ESCAPE:
            quit_program()


def handle_event_playing(event):
    global input_text, composition_text
    if event.type == pygame.TEXTINPUT:
        input_text += event.text
        composition_text = ""
        return
    if event.type == pygame.TEXTEDITING:
        composition_text = event.text
        return
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_RETURN:
            check_input()
        elif event.key == pygame.K_BACKSPACE:
            if composition_text == "":
                input_text = input_text[:-1]
        elif event.key == pygame.K_ESCAPE:
            open_esc_menu()


def handle_event_esc_menu(event):
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_t:
            reset_current_game()
        elif event.key == pygame.K_q:
            return_to_menu()
        elif event.key == pygame.K_x:
            quit_program()
        elif event.key == pygame.K_ESCAPE:
            close_esc_menu()


def handle_event_game_over(event):
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_t:
            reset_current_game()
        elif event.key == pygame.K_q:
            return_to_menu()
        elif event.key == pygame.K_x:
            quit_program()


# =====================================================
# 20. 메인 루프
# =====================================================
def main():
    global last_spawn_time
    global english_words, korean_words
    global font_word, font_input, font_info, font_title, font_gameover
    global font_help, font_popup, font_announce
    global game_state, background_surface

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Typing Game - 타자 연습")
    clock = pygame.time.Clock()

    # 폰트
    font_word = get_font(38)
    font_input = get_font(34)
    font_info = get_font(28)
    font_title = get_font(58)
    font_gameover = get_font(86)
    font_help = get_font(18)
    font_popup = get_font(30)
    font_announce = get_font(22)

    # 🎨 배경 Surface 한 번만 생성 (그라디언트는 무거우니까 캐싱!)
    background_surface = create_background_surface()

    # CSV 로드
    english_words, korean_words, _ = load_words_from_csv(CSV_PATH)

    game_state = GAME_STATE_MENU
    pygame.key.stop_text_input()

    # ========= 메인 루프 =========
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_program()
            if game_state == GAME_STATE_MENU:
                handle_event_menu(event)
            elif game_state == GAME_STATE_PLAYING:
                handle_event_playing(event)
            elif game_state == GAME_STATE_ESC_MENU:
                handle_event_esc_menu(event)
            elif game_state == GAME_STATE_GAME_OVER:
                handle_event_game_over(event)

        if game_state == GAME_STATE_PLAYING:
            now = get_game_time()
            if now - last_spawn_time >= current_spawn_ms:
                create_word()
                last_spawn_time = now
            update_words()
            if game_state == GAME_STATE_PLAYING and now >= next_special_spawn_time:
                create_special_word()
                schedule_next_special_word()
            update_special_words()
            update_difficulty()

        if game_state == GAME_STATE_MENU:
            draw_menu(screen)
        else:
            draw_game(screen)
            if game_state == GAME_STATE_ESC_MENU:
                draw_esc_menu(screen)
            elif game_state == GAME_STATE_GAME_OVER:
                draw_game_over(screen)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
