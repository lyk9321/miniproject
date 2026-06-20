# typing_game_v8.py
# 한컴타자연습 / 한메타자교사 클래식 스타일의 파이썬 타자 연습 게임
# (게임 로직 v6 그대로, 시각적 스타일만 90년대 레트로로 변경)
# 실행 방법: python typing_game_v8.py
#
# [이번 버전 변경 사항]
#  • 균일한 회색 배경 (Win95 실버)
#  • 파란 타이틀바 + 회색 스탯바
#  • 하단 회색 벽돌 벽 + 파란 파도 무늬
#  • 픽셀 느낌 폰트 (돋움/굴림, 안티앨리어싱 OFF)
#  • 두꺼운 블록 커서
#  • 각진 Win95 다이얼로그 팝업
#  • 메인 메뉴 언어 선택 안내 문구 변경

import pygame
import random
import sys
import csv
import os


# =====================================================
# 0. 배포(EXE) 환경 경로
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
# 2. 화면 / 레이아웃 상수
# =====================================================
WIDTH = 1000
HEIGHT = 750
FPS = 60

# === 상단 영역 (타이틀바 + 스탯바) ===
TITLE_BAR_HEIGHT = 32                   # 파란 타이틀바
STAT_BAR_HEIGHT = 30                    # 회색 스탯바
TOP_INFO_HEIGHT = TITLE_BAR_HEIGHT + STAT_BAR_HEIGHT   # = 62

# === 하단 영역 (벽돌 벽 + 파도) ===
WAVE_HEIGHT = 30                        # 맨 아래 파도 높이
BRICK_WALL_HEIGHT = 80                  # 벽돌 벽 높이
BRICK_WALL_Y = HEIGHT - BRICK_WALL_HEIGHT - WAVE_HEIGHT   # 벽돌 시작 = 590
WAVE_Y = HEIGHT - WAVE_HEIGHT           # 파도 시작 = 720

# 게임오버 판정선 = 벽돌 벽 위쪽 (단어가 벽에 닿으면 게임오버)
GAMEOVER_LINE_Y = BRICK_WALL_Y          # 590

# 입력창 (벽돌 벽 위에 살짝 얹힌 느낌)
INPUT_HEIGHT = 50
INPUT_WIDTH = 380                       # 클래식 한컴 느낌으로 작게
INPUT_X = (WIDTH - INPUT_WIDTH) // 2
INPUT_Y = BRICK_WALL_Y + 10             # 벽돌 위에 살짝 떠있게
INPUT_PADDING = 10


# =====================================================
# 3. 🎨 클래식 90년대 색상 팔레트 (Win95 톤)
# =====================================================
# --- 배경 ---
BG_COLOR = (192, 192, 192)              # 클래식 Win95 실버

# --- 상단 타이틀바 (네이비) ---
TITLE_BAR_BG = (0, 0, 128)              # 네이비
TITLE_BAR_TEXT = (255, 255, 255)        # 흰색

# --- 상단 스탯바 (밝은 회색) ---
STAT_BAR_BG = (212, 208, 200)           # Win95 버튼 페이스
STAT_BAR_TEXT = (0, 0, 0)               # 검정
STAT_BAR_DIVIDER = (128, 128, 128)      # 어두운 회색 구분선

# --- 단어 ---
WORD_COLOR = (0, 0, 0)                  # 순수 검정
SPECIAL_WORD_COLOR = (200, 0, 0)        # 강렬한 빨강

# --- 입력창 ---
INPUT_BG = (255, 255, 255)              # 순수 흰색
INPUT_TEXT_COLOR = (0, 0, 0)
INPUT_BORDER = (0, 0, 0)                # 검정 테두리
COMPOSING_COLOR = (0, 0, 180)           # 진한 파란 밑줄
CURSOR_COLOR = (0, 0, 0)                # 검정 블록

# --- 벽돌 벽 ---
BRICK_BG = (100, 100, 100)              # 모르타르 (어두운 회색)
BRICK_FACE = (160, 160, 160)            # 벽돌 표면
BRICK_HIGHLIGHT = (200, 200, 200)       # 벽돌 윗면 하이라이트 (3D 느낌)

# --- 파도 ---
WAVE_BG = (0, 60, 180)                  # 진한 파랑 (물)
WAVE_FOAM = (140, 180, 255)             # 밝은 파랑 (물거품)

# --- 팝업 (Win95 다이얼로그 스타일) ---
POPUP_BG = (212, 208, 200)              # 다이얼로그 배경
POPUP_TITLE_BG = (0, 0, 128)            # 네이비 헤더
POPUP_TITLE_TEXT = (255, 255, 255)
POPUP_BORDER_DARK = (64, 64, 64)        # 3D 효과: 어두운 면
POPUP_BORDER_LIGHT = (255, 255, 255)    # 3D 효과: 밝은 면
POPUP_TEXT = (0, 0, 0)

# --- 메뉴 버튼 ---
BUTTON_FACE = (212, 208, 200)
BUTTON_BORDER_DARK = (128, 128, 128)
BUTTON_BORDER_LIGHT = (255, 255, 255)
BUTTON_TEXT = (0, 0, 0)

# --- 게임오버 ---
GAMEOVER_COLOR = (200, 0, 0)

# --- 안내 (언어 모드 안내) ---
ANNOUNCE_BG = (255, 255, 200)           # 옛날 노란 메모지 톤
ANNOUNCE_TEXT = (0, 0, 0)
ANNOUNCE_BORDER = (0, 0, 0)

# --- 도움말 텍스트 ---
HELP_COLOR = (255, 255, 255)            # 타이틀바 위에 표시할 거라 흰색


# =====================================================
# 4. 게임 설정값 (로직 변경 X)
# =====================================================
CURSOR_BLINK_MS = 500
CURSOR_WIDTH = 14                       # 두꺼운 블록 커서 (클래식)

BLINK_CYCLE_MS = 1000
BLINK_VISIBLE_MS = 900
BLINK_LEVEL_THRESHOLD = 5

ANNOUNCE_DURATION_MS = 3000

SPECIAL_WORD_SPEED = 2.0
SPECIAL_WORD_SPAWN_MIN_MS = 20000
SPECIAL_WORD_SPAWN_MAX_MS = 30000
SPECIAL_WORD_BONUS_SCORE = 30

INITIAL_SPEED = 1.0
SPEED_STEP = 0.5
MAX_SPEED = 6.0
INITIAL_SPAWN_MS = 2000
MIN_SPAWN_MS = 800
SPAWN_STEP_MS = 100
LEVEL_UP_SCHEDULE = [30, 20]
LEVEL_UP_FIXED_INTERVAL = 15

# 기본 단어 (CSV 없을 때 백업)
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

# 폰트 (레트로 픽셀 느낌)
font_word = None              # 떨어지는 단어용
font_input = None             # 입력창 글자용
font_stat = None              # 스탯바 (단계/점수/시간)
font_titlebar = None          # 파란 타이틀바 글자
font_title_big = None         # 메뉴 큰 제목용
font_gameover = None          # GAME OVER 글자
font_help = None              # 도움말
font_popup_title = None       # 팝업 헤더
font_popup = None             # 팝업 본문
font_announce = None          # 언어 안내

# 미리 그려놓는 배경 Surface (성능 최적화)
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
# 7. 레트로 한글 폰트 찾기
# =====================================================
def get_font(size):
    """
    한글 표시 + 레트로 픽셀 느낌 폰트.
    돋움/굴림 같은 비트맵 폰트를 우선해서 90년대 느낌을 살림.
    """
    retro_korean_candidates = [
        'batang',          # 바탕
        'gungsuh',         # 궁서
        'gulim',           # 굴림 - 한컴 시절 폰트
        'dotum',           # 돋움 - 가장 90년대 느낌                
        'malgungothic',    # 폴백
        'applegothic',
        'applesdgothicneo',
        'nanumgothic',
    ]
    available = pygame.font.get_fonts()
    for name in retro_korean_candidates:
        if name in available:
            return pygame.font.SysFont(name, size)
    return pygame.font.SysFont(None, size)


def render_pixel(font, text, color):
    """
    안티앨리어싱 OFF로 렌더링 → 픽셀 느낌이 살아남.
    레트로 폰트는 안티앨리어싱 끈 게 더 또렷하고 90년대 같음.
    """
    return font.render(text, False, color)


# =====================================================
# 8. 🎨 배경 Surface 생성 (한 번만!)
# =====================================================
def draw_brick_wall(surface, top_y, height):
    """
    벽돌 벽 그리기.
    1) 모르타르(시멘트) 색으로 배경 채우기
    2) 그 위에 벽돌 사각형들을 행마다 어긋나게 배치
    3) 각 벽돌 위쪽에 밝은 라인 → 3D 느낌
    """
    # 1) 모르타르 배경
    pygame.draw.rect(surface, BRICK_BG, (0, top_y, WIDTH, height))

    # 2) 벽돌 패턴
    brick_w = 64                # 벽돌 가로 크기
    brick_h = 22                # 벽돌 세로 크기
    mortar_size = 2             # 사이 간격 (모르타르 두께)

    row = 0
    y = top_y
    while y < top_y + height:
        # 짝수 행은 0부터, 홀수 행은 절반 어긋나게 시작 (벽돌 패턴!)
        x_offset = (brick_w // 2) if (row % 2 == 1) else 0
        x = -x_offset
        while x < WIDTH:
            # 벽돌 본체
            brick_rect = (x + mortar_size, y + mortar_size,
                          brick_w - mortar_size * 2, brick_h - mortar_size * 2)
            pygame.draw.rect(surface, BRICK_FACE, brick_rect)
            # 윗면 하이라이트 (3D 효과)
            pygame.draw.line(surface, BRICK_HIGHLIGHT,
                             (x + mortar_size, y + mortar_size),
                             (x + brick_w - mortar_size - 1, y + mortar_size),
                             1)
            x += brick_w
        y += brick_h
        row += 1


def draw_waves(surface, top_y, height):
    """
    파도 무늬 그리기.
    1) 진한 파란색으로 물 영역 채우기
    2) 그 위에 밝은 파란색 지그재그 라인 (물결 무늬)
    """
    # 1) 물 배경
    pygame.draw.rect(surface, WAVE_BG, (0, top_y, WIDTH, height))

    # 2) 지그재그 파도 (위쪽 가장자리)
    peak_w = 22                 # 한 파도의 가로 길이
    peak_h = 7                  # 파도 위아래 진폭

    points = []
    x = 0
    going_up = True
    while x <= WIDTH + peak_w:
        if going_up:
            points.append((x, top_y + 4))                  # 골(아래)
        else:
            points.append((x, top_y + 4 + peak_h))         # 정점(위쪽)... wait 반대
        going_up = not going_up
        x += peak_w // 2

    # 그릴 점이 충분하면 라인으로 연결
    if len(points) >= 2:
        pygame.draw.lines(surface, WAVE_FOAM, False, points, 2)

    # 한 줄 더 (조금 아래에 두 번째 파도) → 깊이감
    points2 = []
    x = peak_w // 4
    going_up = True
    while x <= WIDTH + peak_w:
        if going_up:
            points2.append((x, top_y + 16))
        else:
            points2.append((x, top_y + 16 + peak_h))
        going_up = not going_up
        x += peak_w // 2
    if len(points2) >= 2:
        pygame.draw.lines(surface, WAVE_FOAM, False, points2, 2)


def create_background_surface():
    """
    전체 배경을 한 번만 그려놓고 캐싱.
    매 프레임 다시 그리지 않으니 성능 좋음.
    """
    bg = pygame.Surface((WIDTH, HEIGHT))

    # === 1. 메인 배경 (균일한 회색) ===
    bg.fill(BG_COLOR)

    # === 2. 벽돌 벽 ===
    draw_brick_wall(bg, BRICK_WALL_Y, BRICK_WALL_HEIGHT)

    # === 3. 파도 ===
    draw_waves(bg, WAVE_Y, WAVE_HEIGHT)

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
# 10. 난이도별 출제 & Word Bag (변경 없음)
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
    word_surface = render_pixel(font_word, text, WORD_COLOR)
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
    word_surface = render_pixel(font_word, text, SPECIAL_WORD_COLOR)
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
# 18. 그리기 - 상단 영역 (타이틀바 + 스탯바)
# =====================================================
def draw_top_bars(screen):
    """
    상단 두 줄: 네이비 타이틀바 + 회색 스탯바.
    한컴타자연습 / 한메타자교사 같은 90년대 PC 프로그램 느낌.
    """
    # === 1. 네이비 타이틀바 ===
    pygame.draw.rect(screen, TITLE_BAR_BG,
                     (0, 0, WIDTH, TITLE_BAR_HEIGHT))

    # 타이틀 텍스트 (중앙 정렬, 글자 사이 띄움 → 매우 클래식한 느낌)
    title_text = "타 자 연 습"
    title_surface = render_pixel(font_titlebar, title_text, TITLE_BAR_TEXT)
    title_rect = title_surface.get_rect(center=(WIDTH // 2, TITLE_BAR_HEIGHT // 2))
    screen.blit(title_surface, title_rect)

    # 우측 상단 도움말 (게임 진행 중일 때만)
    if game_state == GAME_STATE_PLAYING:
        help_surface = render_pixel(font_help, "ESC: 메뉴", HELP_COLOR)
        help_rect = help_surface.get_rect(
            midright=(WIDTH - 10, TITLE_BAR_HEIGHT // 2))
        screen.blit(help_surface, help_rect)

    # === 2. 회색 스탯바 ===
    pygame.draw.rect(screen, STAT_BAR_BG,
                     (0, TITLE_BAR_HEIGHT, WIDTH, STAT_BAR_HEIGHT))
    # 위/아래 어두운 구분선 (3D 느낌)
    pygame.draw.line(screen, STAT_BAR_DIVIDER,
                     (0, TITLE_BAR_HEIGHT),
                     (WIDTH, TITLE_BAR_HEIGHT), 1)
    pygame.draw.line(screen, STAT_BAR_DIVIDER,
                     (0, TOP_INFO_HEIGHT - 1),
                     (WIDTH, TOP_INFO_HEIGHT - 1), 1)

    # 스탯 텍스트 (단계 / 점수 / 시간)
    elapsed_sec = (get_game_time() - game_start_time) // 1000
    minutes = elapsed_sec // 60
    seconds = elapsed_sec % 60
    stat_text = f"단계 : {level}        점수 : {score}        시간 : {minutes:02d}:{seconds:02d}"
    stat_surface = render_pixel(font_stat, stat_text, STAT_BAR_TEXT)
    stat_rect = stat_surface.get_rect(
        center=(WIDTH // 2, TITLE_BAR_HEIGHT + STAT_BAR_HEIGHT // 2))
    screen.blit(stat_surface, stat_rect)


# =====================================================
# 19. 그리기 - 메뉴 / 게임 / 팝업 / 게임오버
# =====================================================
def draw_3d_box(screen, rect, face_color, raised=True):
    """
    Win95 풍 3D 박스 그리기 (얇은 라이트/다크 라인으로 입체감).
    raised=True: 위로 솟은 느낌 (밝은 위/왼, 어두운 아래/오른)
    raised=False: 들어간 느낌 (반대)
    """
    x, y, w, h = rect
    pygame.draw.rect(screen, face_color, rect)
    if raised:
        light, dark = BUTTON_BORDER_LIGHT, BUTTON_BORDER_DARK
    else:
        light, dark = BUTTON_BORDER_DARK, BUTTON_BORDER_LIGHT
    # 위 / 왼 = 밝은 라인
    pygame.draw.line(screen, light, (x, y), (x + w - 1, y), 2)
    pygame.draw.line(screen, light, (x, y), (x, y + h - 1), 2)
    # 아래 / 오른 = 어두운 라인
    pygame.draw.line(screen, dark, (x, y + h - 1), (x + w - 1, y + h - 1), 2)
    pygame.draw.line(screen, dark, (x + w - 1, y), (x + w - 1, y + h - 1), 2)


def draw_menu(screen):
    """메뉴 화면 - 회색 배경 + 클래식 버튼."""
    # 배경 (그냥 회색)
    screen.fill(BG_COLOR)

    # 상단 타이틀바만 (스탯바는 게임 시작 전이라 표시 X)
    pygame.draw.rect(screen, TITLE_BAR_BG, (0, 0, WIDTH, TITLE_BAR_HEIGHT))
    title_text = "타 자 연 습"
    title_surface = render_pixel(font_titlebar, title_text, TITLE_BAR_TEXT)
    screen.blit(title_surface,
                title_surface.get_rect(center=(WIDTH // 2, TITLE_BAR_HEIGHT // 2)))

    # 큰 제목
    big_title = render_pixel(font_title_big, "타  자  연  습", (0, 0, 80))
    screen.blit(big_title, big_title.get_rect(center=(WIDTH // 2, 180)))

    # 안내
    #guide = render_pixel(font_stat, "언어를 선택하세요 / Select Language", (0, 0, 0))
    #screen.blit(guide, guide.get_rect(center=(WIDTH // 2, 280)))

    guide = render_pixel(font_stat, "숫자 버튼으로 언어를 선택하세요 / Press [ 1 ] or [ 2 ]", (0, 0, 0))
    screen.blit(guide, guide.get_rect(center=(WIDTH // 2, 280)))
    '''
    line_gap = font_stat.get_height() + 15   # 폰트 높이 + 여유 15px
    guide1 = render_pixel(font_stat, "언어를 선택하세요 / Select Language", (0, 0, 0))
    guide2 = render_pixel(font_stat, "숫자 버튼으로 언어 선택 / Press Num Button", (0, 0, 0))
    screen.blit(guide1, guide1.get_rect(center=(WIDTH // 2, 265)))
    screen.blit(guide2, guide2.get_rect(center=(WIDTH // 2, 265 + line_gap)))
    '''
    # 버튼 1: English (Win95 풍 3D 버튼)
    btn1_rect = (WIDTH // 2 - 180, 350, 360, 70)
    draw_3d_box(screen, btn1_rect, BUTTON_FACE, raised=True)
    btn1_text = render_pixel(font_stat, "[ 1 ]   English", BUTTON_TEXT)
    screen.blit(btn1_text, btn1_text.get_rect(
        center=(btn1_rect[0] + btn1_rect[2] // 2,
                btn1_rect[1] + btn1_rect[3] // 2)))

    # 버튼 2: 한국어
    btn2_rect = (WIDTH // 2 - 180, 450, 360, 70)
    draw_3d_box(screen, btn2_rect, BUTTON_FACE, raised=True)
    btn2_text = render_pixel(font_stat, "[ 2 ]   한국어", BUTTON_TEXT)
    screen.blit(btn2_text, btn2_text.get_rect(
        center=(btn2_rect[0] + btn2_rect[2] // 2,
                btn2_rect[1] + btn2_rect[3] // 2)))

    # 하단 안내
    info = render_pixel(font_stat, "ESC: 종료 / Quit", (80, 80, 80))
    screen.blit(info, info.get_rect(center=(WIDTH // 2, 600)))


def draw_game(screen):
    """게임 플레이 화면."""
    # === 1. 미리 만들어둔 배경 (회색 + 벽돌 + 파도) ===
    screen.blit(background_surface, (0, 0))

    # === 2. 떨어지는 일반 단어 (깜빡임 적용) ===
    show_words = should_show_words()
    if show_words:
        for word in words_on_screen:
            surface = render_pixel(font_word, word["text"], WORD_COLOR)
            screen.blit(surface, (word["x"], word["y"]))

    # === 3. 특수 단어 (빨간색) ===
    for sw in special_words_on_screen:
        surface = render_pixel(font_word, sw["text"], SPECIAL_WORD_COLOR)
        screen.blit(surface, (sw["x"], sw["y"]))

    # === 4. 상단 타이틀바 + 스탯바 (배경 위에 덮어쓰기) ===
    draw_top_bars(screen)

    # === 5. 입력창 (벽돌 위에 흰색 박스) ===
    # 검정 테두리 사각형
    pygame.draw.rect(screen, INPUT_BORDER,
                     (INPUT_X - 2, INPUT_Y - 2,
                      INPUT_WIDTH + 4, INPUT_HEIGHT + 4))
    pygame.draw.rect(screen, INPUT_BG,
                     (INPUT_X, INPUT_Y, INPUT_WIDTH, INPUT_HEIGHT))

    text_x = INPUT_X + INPUT_PADDING
    text_y = INPUT_Y + INPUT_PADDING

    # 확정 글자
    confirmed_width = 0
    if input_text:
        confirmed_surface = render_pixel(font_input, input_text, INPUT_TEXT_COLOR)
        screen.blit(confirmed_surface, (text_x, text_y))
        confirmed_width = confirmed_surface.get_width()

    # 조합 중 글자 + 밑줄
    composing_width = 0
    if composition_text:
        composing_surface = render_pixel(font_input, composition_text, COMPOSING_COLOR)
        screen.blit(composing_surface, (text_x + confirmed_width, text_y))
        underline_y = text_y + composing_surface.get_height() - 2
        pygame.draw.line(screen, COMPOSING_COLOR,
                         (text_x + confirmed_width, underline_y),
                         (text_x + confirmed_width + composing_surface.get_width(),
                          underline_y), 2)
        composing_width = composing_surface.get_width()

    # 커서 (블록 모양 - 두꺼운 사각형)
    if should_show_cursor():
        cursor_x = text_x + confirmed_width + composing_width
        cursor_y_top = text_y + 2
        cursor_height = font_input.get_height() - 4
        pygame.draw.rect(screen, CURSOR_COLOR,
                         (cursor_x, cursor_y_top, CURSOR_WIDTH, cursor_height))

    # === 6. 언어 모드 안내 ===
    draw_language_announcement(screen)


def draw_language_announcement(screen):
    elapsed = get_game_time() - game_start_time
    if elapsed > ANNOUNCE_DURATION_MS:
        return
    if selected_language == "korean":
        text = "한국어 모드입니다. 한글 입력 상태에서 플레이하세요."
    else:
        text = "English mode. Please use English keyboard input."
    surface = render_pixel(font_announce, text, ANNOUNCE_TEXT)
    padding_x = 14
    padding_y = 8
    box_width = surface.get_width() + padding_x * 2
    box_height = surface.get_height() + padding_y * 2
    box_x = (WIDTH - box_width) // 2
    box_y = TOP_INFO_HEIGHT + 10

    pygame.draw.rect(screen, ANNOUNCE_BG, (box_x, box_y, box_width, box_height))
    pygame.draw.rect(screen, ANNOUNCE_BORDER,
                     (box_x, box_y, box_width, box_height), 1)
    screen.blit(surface, (box_x + padding_x, box_y + padding_y))


def draw_dialog_popup(screen, title, lines):
    """
    Win95 풍 다이얼로그 팝업.
    구조: 네이비 타이틀바 + 회색 본문 + 3D 테두리.
    """
    box_width = 540
    line_height = font_popup.get_height() + 8
    title_height = 28
    content_padding = 20
    box_height = title_height + content_padding + len(lines) * line_height + content_padding
    box_x = (WIDTH - box_width) // 2
    box_y = (HEIGHT - box_height) // 2

    # 3D 박스 (raised)
    draw_3d_box(screen, (box_x, box_y, box_width, box_height),
                POPUP_BG, raised=True)

    # 네이비 타이틀바
    pygame.draw.rect(screen, POPUP_TITLE_BG,
                     (box_x + 4, box_y + 4, box_width - 8, title_height))
    title_surface = render_pixel(font_popup_title, title, POPUP_TITLE_TEXT)
    title_rect = title_surface.get_rect(
        midleft=(box_x + 14, box_y + 4 + title_height // 2))
    screen.blit(title_surface, title_rect)

    # 본문 글자들
    current_y = box_y + title_height + content_padding
    for line in lines:
        surface = render_pixel(font_popup, line, POPUP_TEXT)
        rect = surface.get_rect(center=(WIDTH // 2,
                                        current_y + font_popup.get_height() // 2))
        screen.blit(surface, rect)
        current_y += line_height


def draw_esc_menu(screen):
    draw_dialog_popup(screen, "메뉴", [
        "",
        "T : 현재 게임 다시 시작",
        "Q : 메인 메뉴로 나가기",
        "X : 프로그램 종료",
        "ESC : 게임으로 돌아가기",
    ])


def draw_game_over(screen):
    """GAME OVER 다이얼로그 (반투명 X, 그냥 화면 위에 다이얼로그)."""
    # 화면 살짝 어둡게 (회색 그대로 두면 너무 안 보일까봐)
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(120)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # 다이얼로그 박스
    box_width = 540
    box_height = 360
    box_x = (WIDTH - box_width) // 2
    box_y = (HEIGHT - box_height) // 2

    draw_3d_box(screen, (box_x, box_y, box_width, box_height),
                POPUP_BG, raised=True)

    # 네이비 타이틀바
    title_height = 28
    pygame.draw.rect(screen, POPUP_TITLE_BG,
                     (box_x + 4, box_y + 4, box_width - 8, title_height))
    title_surface = render_pixel(font_popup_title, "GAME OVER", POPUP_TITLE_TEXT)
    title_rect = title_surface.get_rect(
        midleft=(box_x + 14, box_y + 4 + title_height // 2))
    screen.blit(title_surface, title_rect)

    # GAME OVER 큰 글자
    big = render_pixel(font_gameover, "GAME OVER", GAMEOVER_COLOR)
    screen.blit(big, big.get_rect(
        center=(WIDTH // 2, box_y + 110)))

    # 점수
    score_surface = render_pixel(font_popup,
                                 f"최종 점수 : {score}", POPUP_TEXT)
    screen.blit(score_surface, score_surface.get_rect(
        center=(WIDTH // 2, box_y + 200)))

    # 선택지
    lines = [
        "T : 같은 언어로 다시 시작",
        "Q : 메인 메뉴로 이동",
        "X : 프로그램 종료",
    ]
    y = box_y + 250
    for line in lines:
        s = render_pixel(font_popup, line, POPUP_TEXT)
        screen.blit(s, s.get_rect(center=(WIDTH // 2, y)))
        y += font_popup.get_height() + 6


# =====================================================
# 20. 이벤트 처리 (변경 없음)
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
# 21. 메인 루프
# =====================================================
def main():
    global last_spawn_time
    global english_words, korean_words
    global font_word, font_input, font_stat, font_titlebar
    global font_title_big, font_gameover, font_help, font_popup_title, font_popup, font_announce
    global game_state, background_surface

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("타자연습")
    clock = pygame.time.Clock()

    # === 폰트 (레트로 픽셀 느낌) ===
    # 비트맵 폰트는 작은 사이즈에서 더 또렷하고 90년대 같음
    font_word = get_font(30)              # 떨어지는 단어
    font_input = get_font(30)             # 입력창 (살짝 작게)
    font_stat = get_font(20)              # 스탯바
    font_titlebar = get_font(20)          # 타이틀바
    font_title_big = get_font(54)         # 메뉴 큰 제목
    font_gameover = get_font(56)          # GAME OVER
    font_help = get_font(15)              # 도움말
    font_popup_title = get_font(18)       # 팝업 헤더
    font_popup = get_font(22)             # 팝업 본문
    font_announce = get_font(18)          # 안내

    # 배경 캐싱
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
