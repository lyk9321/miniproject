# typing_game_v6.py
# 한컴타자연습 스타일의 파이썬 타자 연습 게임 (v6: 난이도별 출제 + 특수 단어)
# 실행 방법: python typing_game_v6.py
#
# [이번 버전에서 추가/개선된 점]
#  1. 단어는 스코어보드 아래에서 생성 (겹침 방지)
#  2. 입력창을 화면 중앙에 배치 (시선 집중)
#  3. 단어 깜빡임이 훨씬 부드러워짐 (900ms 보임 / 100ms 숨김)
#  4. 레벨에 따라 출제 난이도가 달라짐 (초급 → 점점 어려워짐)
#  5. Word Bag 방식으로 단어 중복 반복 줄임
#  6. 특수 단어(빨간색) 추가! 맞히면 화면 모든 일반 단어 삭제 💥

import pygame
import random
import sys
import csv
import os


# =====================================================
# 0. 배포(EXE) 환경까지 고려한 파일 경로 설정
# =====================================================
# sys.frozen: PyInstaller로 exe 변환된 상태면 True
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)       # exe와 같은 폴더
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # .py와 같은 폴더

CSV_PATH = os.path.join(BASE_DIR, "words.csv")


# =====================================================
# 1. 게임 상태 상수
# =====================================================
GAME_STATE_MENU = "menu"
GAME_STATE_PLAYING = "playing"
GAME_STATE_ESC_MENU = "esc_menu"
GAME_STATE_GAME_OVER = "game_over"


# =====================================================
# 2. 설정값
# =====================================================
# --- 화면 ---
WIDTH = 1000
HEIGHT = 750
FPS = 60

# --- 색깔 ---
BG_COLOR = (245, 245, 235)
WORD_COLOR = (40, 40, 40)                  # 일반 단어 - 어두운 회색
SPECIAL_WORD_COLOR = (220, 50, 50)         # ⭐ 특수 단어 - 빨강!
INPUT_BG = (255, 255, 255)
INPUT_TEXT_COLOR = (0, 0, 0)
COMPOSING_COLOR = (100, 100, 200)
CURSOR_COLOR = (0, 0, 0)
BORDER_COLOR = (120, 120, 120)
INFO_COLOR = (60, 80, 140)
TITLE_COLOR = (40, 60, 120)
GAMEOVER_COLOR = (200, 40, 40)
BUTTON_COLOR = (220, 230, 250)
BUTTON_BORDER = (80, 100, 180)
HELP_COLOR = (160, 160, 160)
POPUP_BG = (250, 250, 250)
POPUP_BORDER = (80, 100, 180)
POPUP_SHADOW = (0, 0, 0)
ANNOUNCE_BG = (255, 250, 220)
ANNOUNCE_TEXT = (100, 80, 30)
TOP_LINE_COLOR = (200, 200, 200)           # 스코어보드 아래 구분선

# --- 스코어보드 영역 ---
# 단어가 이 높이 아래부터 생성되도록 해서 점수/레벨 표시와 겹치지 않게 함
TOP_INFO_HEIGHT = 60

# --- 입력창 (화면 중앙에 배치) ---
INPUT_HEIGHT = 60
INPUT_WIDTH = int(WIDTH * 0.5)             # 화면의 50% 너비
INPUT_X = (WIDTH - INPUT_WIDTH) // 2       # 가로 중앙 정렬
INPUT_Y = HEIGHT - INPUT_HEIGHT - 15
INPUT_PADDING = 12
# 게임오버 판정선: 일반 단어가 이 y에 닿으면 게임오버
GAMEOVER_LINE_Y = INPUT_Y

# --- 커서 ---
CURSOR_BLINK_MS = 500
CURSOR_WIDTH = 2

# --- 단어 깜빡임 ---
BLINK_CYCLE_MS = 1000          # 한 주기: 1초
BLINK_VISIBLE_MS = 900         # 그 중 0.9초 보이고 0.1초만 숨김 (훨씬 부드러움)
BLINK_LEVEL_THRESHOLD = 5      # 레벨 5 이상부터 깜빡임

# --- 입력 모드 안내 ---
ANNOUNCE_DURATION_MS = 3000

# --- 특수 단어 ---
SPECIAL_WORD_SPEED = 2.0                   # 왼 → 오른쪽 이동 속도 (고정)
SPECIAL_WORD_SPAWN_MIN_MS = 20000          # 최소 20초 간격
SPECIAL_WORD_SPAWN_MAX_MS = 30000          # 최대 30초 간격
SPECIAL_WORD_BONUS_SCORE = 30              # 특수 단어 맞힐 때 보너스 점수

# --- 난이도 ---
INITIAL_SPEED = 1.0
SPEED_STEP = 0.5
MAX_SPEED = 6.0
INITIAL_SPAWN_MS = 2000
MIN_SPAWN_MS = 800
SPAWN_STEP_MS = 100
LEVEL_UP_SCHEDULE = [30, 20]
LEVEL_UP_FIXED_INTERVAL = 15

# --- 기본 단어 리스트 (CSV 없을 때 백업용, 딕셔너리 형태) ---
# 각 원소: {"word": ..., "difficulty": ..., "category": ...}
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
# 3. 전역 상태 변수
# =====================================================
game_state = GAME_STATE_MENU

# 화면에 떠 있는 단어들
words_on_screen = []                # 일반 단어 (위→아래)
special_words_on_screen = []        # ⭐ 특수 단어 (왼→오른쪽)

# 입력창
input_text = ""
composition_text = ""

# 게임 진행 정보
score = 0
level = 1
current_speed = INITIAL_SPEED
current_spawn_ms = INITIAL_SPAWN_MS

# 타이머
last_spawn_time = 0
game_start_time = 0
last_level_up_time = 0
level_up_index = 0
next_special_spawn_time = 0          # ⭐ 다음 특수 단어 생성 예정 시각

# 일시정지 (ESC 메뉴용)
pause_start_time = 0
total_paused_time = 0

# 언어 & 단어 DB
selected_language = None
word_list = []                        # 현재 언어의 전체 단어 (딕셔너리 리스트)
english_words = []
korean_words = []

# Word Bag 시스템
word_bag = []                         # 현재 꺼내 쓰는 단어 주머니
last_word_bag_level_key = None        # 주머니가 어떤 레벨 그룹용인지 기억
last_emitted_word = None              # 직전에 출제한 단어 (연속 방지용)

# 폰트
font_word = None
font_input = None
font_info = None
font_title = None
font_gameover = None
font_help = None
font_popup = None
font_announce = None


# =====================================================
# 4. 시간 관련 함수 (일시정지 시간 보정)
# =====================================================
def get_game_time():
    """
    일시정지 시간을 제외한 '게임 시간(ms)'.
    ESC 메뉴 떠 있을 때 이 시간이 멈춘 것처럼 동작 → 단어 생성/깜빡임/특수 단어 타이머 등이 모두 함께 정지.
    """
    return pygame.time.get_ticks() - total_paused_time


def pause_game_timer():
    """ESC 메뉴가 열리는 순간 호출."""
    global pause_start_time
    pause_start_time = pygame.time.get_ticks()


def resume_game_timer():
    """ESC 메뉴가 닫히는 순간 호출. 멈춰있던 시간을 누적."""
    global total_paused_time
    total_paused_time += pygame.time.get_ticks() - pause_start_time


# =====================================================
# 5. 한글 폰트 찾기
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
# 6. CSV 로딩 (difficulty, category까지 저장)
# =====================================================
def load_words_from_csv(filepath):
    """
    CSV에서 단어 + 난이도 + 카테고리를 읽음.
    성공: (영어 리스트, 한국어 리스트, True)
    실패: 기본 리스트 사용.
    각 원소는 딕셔너리 형태: {"word": ..., "difficulty": ..., "category": ...}
    """
    if not os.path.exists(filepath):
        print(f"[알림] '{filepath}' 파일 없음 → 기본 단어 리스트 사용")
        return DEFAULT_ENGLISH_WORDS.copy(), DEFAULT_KOREAN_WORDS.copy(), False

    eng_words = []
    kor_words = []
    try:
        with open(filepath, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                language = (row.get("language") or "").strip().lower()
                word = (row.get("word") or "").strip()
                if not word:
                    continue
                # difficulty를 정수로 변환 (실패하면 1로 간주)
                try:
                    difficulty = int((row.get("difficulty") or "1").strip())
                except ValueError:
                    difficulty = 1
                # 1~4 범위로 제한 (이상한 값이 들어오는 경우 대비)
                if difficulty < 1:
                    difficulty = 1
                elif difficulty > 4:
                    difficulty = 4
                category = (row.get("category") or "").strip()

                # 딕셔너리로 저장
                entry = {"word": word, "difficulty": difficulty, "category": category}
                if language == "en":
                    eng_words.append(entry)
                elif language == "ko":
                    kor_words.append(entry)

        # 빈 체크
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
# 7. 난이도별 허용 단어 & 가중치
# =====================================================
def get_level_key(lv):
    """
    레벨을 '난이도 그룹 키'로 바꿔줌.
    같은 그룹 안에서는 word bag을 유지하고, 그룹이 바뀔 때만 새로 만든다.
    """
    if lv <= 2:
        return "EASY"       # 레벨 1~2
    elif lv <= 4:
        return "BASIC"      # 레벨 3~4
    elif lv <= 6:
        return "MID"        # 레벨 5~6
    else:
        return "ALL"        # 레벨 7+


def get_allowed_difficulties_by_level(lv):
    """
    현재 레벨에서 출제 가능한 난이도 목록과 각 난이도의 가중치를 돌려줌.
    (난이도 → 가중치) 형태 딕셔너리. 가중치가 높을수록 word bag에 여러 번 들어감.
    """
    if lv <= 2:
        # 레벨 1~2: 초급 100%
        return {1: 10}
    elif lv <= 4:
        # 레벨 3~4: 초급 40%, 중급 60%
        return {1: 4, 2: 6}
    elif lv <= 6:
        # 레벨 5~6: 중급 70%, 고급 30%
        return {2: 7, 3: 3}
    else:
        # 레벨 7+: 초급 20%, 중급 40%, 고급 30%, 최상급 10%
        return {1: 2, 2: 4, 3: 3, 4: 1}


# =====================================================
# 8. Word Bag (단어 주머니) 시스템
# =====================================================
def build_word_bag_by_level():
    """
    현재 레벨에서 출제 가능한 단어들로 주머니를 가득 채움.
    난이도별 가중치만큼 단어를 복제해서 넣고 셔플 → 비율이 자연스럽게 맞음.
    """
    weights = get_allowed_difficulties_by_level(level)
    bag = []
    for difficulty, weight in weights.items():
        # 해당 난이도의 단어들을 뽑기
        matching = [w for w in word_list if w["difficulty"] == difficulty]
        # 가중치만큼 복제 → 비율 자동 조절
        for _ in range(weight):
            bag.extend(matching)
    # 원본 리스트를 건드리지 않도록 shuffle은 bag에만
    random.shuffle(bag)
    return bag


def get_next_word_by_level():
    """
    현재 레벨에 맞는 단어 하나를 word bag에서 꺼내 돌려줌.
    - 주머니가 비거나 레벨 그룹이 바뀌면 새로 채운다.
    - 직전 단어와 같은 단어가 나오면 다음 것과 자리를 바꿔 연속 방지.
    """
    global word_bag, last_word_bag_level_key, last_emitted_word

    current_key = get_level_key(level)

    # 주머니가 비었거나, 난이도 그룹이 바뀌었으면 재구성
    if not word_bag or current_key != last_word_bag_level_key:
        word_bag = build_word_bag_by_level()
        last_word_bag_level_key = current_key

    # 혹시 word_list가 비어서 주머니가 그래도 비면 안전장치
    if not word_bag:
        return None

    # 뒤에서 하나 꺼내기 (pop은 뒤에서 꺼내는 게 효율적)
    word_entry = word_bag.pop()

    # 직전과 같은 단어면 다른 것과 교환
    if (last_emitted_word is not None
            and word_entry["word"] == last_emitted_word
            and len(word_bag) > 0):
        # 앞쪽 단어를 꺼내 쓰고, 방금 꺼낸 걸 앞쪽에 다시 넣기
        alternative = word_bag.pop(0)
        word_bag.insert(0, word_entry)
        word_entry = alternative

    last_emitted_word = word_entry["word"]
    return word_entry


# =====================================================
# 9. 게임 초기화 & 상태 전환
# =====================================================
def init_game():
    """게임 상태값들을 처음 상태로 되돌림 (새 게임/리셋/R 재시작 공용)."""
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

    # 일시정지 누적 시간도 리셋
    total_paused_time = 0

    now = pygame.time.get_ticks()
    last_spawn_time = now
    game_start_time = now
    last_level_up_time = now
    level_up_index = 0

    # 워드 백 리셋
    word_bag = []
    last_word_bag_level_key = None
    last_emitted_word = None

    # 특수 단어 생성 예정 시각 초기화
    schedule_next_special_word()


def start_playing():
    """플레이 상태로 진입 (IME 켜기 + 초기화)."""
    global game_state
    init_game()
    pygame.key.start_text_input()
    input_rect = pygame.Rect(INPUT_X, INPUT_Y, INPUT_WIDTH, INPUT_HEIGHT)
    pygame.key.set_text_input_rect(input_rect)
    game_state = GAME_STATE_PLAYING


def reset_current_game():
    """같은 언어 유지한 채 게임만 재시작."""
    start_playing()


def return_to_menu():
    """언어 선택 화면으로 복귀."""
    global game_state, selected_language, word_list, input_text, composition_text
    game_state = GAME_STATE_MENU
    selected_language = None
    word_list = []
    input_text = ""
    composition_text = ""
    pygame.key.stop_text_input()


def quit_program():
    """프로그램 완전 종료."""
    pygame.quit()
    sys.exit()


# =====================================================
# 10. 일반 단어 생성 / 이동
# =====================================================
def create_word():
    """일반 단어 하나를 word bag에서 뽑아 스코어보드 아래부터 떨어뜨림."""
    entry = get_next_word_by_level()
    if entry is None:
        return  # 안전장치

    text = entry["word"]
    word_surface = font_word.render(text, True, WORD_COLOR)
    word_width = word_surface.get_width()
    # x는 화면 밖으로 잘리지 않게
    x = random.randint(0, max(0, WIDTH - word_width))
    # y는 스코어보드 영역 아래에서 시작 (겹침 방지)
    y = TOP_INFO_HEIGHT
    words_on_screen.append({"text": text, "x": x, "y": y})


def update_words():
    """모든 일반 단어를 아래로 이동. 바닥에 닿으면 게임오버."""
    for word in words_on_screen:
        word["y"] += current_speed
        if word["y"] >= GAMEOVER_LINE_Y:
            enter_game_over_state()
            break


def enter_game_over_state():
    """게임오버 상태로 전환."""
    global game_state
    game_state = GAME_STATE_GAME_OVER
    pygame.key.stop_text_input()   # IME 꺼서 T/Q/X 키가 언어 상관없이 동작


# =====================================================
# 11. 특수 단어 (왼 → 오른쪽)
# =====================================================
def schedule_next_special_word():
    """다음 특수 단어 생성 예정 시각을 랜덤으로 정함."""
    global next_special_spawn_time
    delay = random.randint(SPECIAL_WORD_SPAWN_MIN_MS, SPECIAL_WORD_SPAWN_MAX_MS)
    next_special_spawn_time = get_game_time() + delay


def create_special_word():
    """
    특수 단어 생성. 
    - 이미 화면에 특수 단어가 있으면 생성하지 않음
    - 초급/중급(난이도 1~2) 단어 중에서 뽑음 (너무 어려우면 안 되니까)
    - x는 화면 왼쪽 바깥, y는 스코어보드와 입력창 사이의 안전 구간에서 랜덤
    """
    # 동시에 여러 개 금지
    if len(special_words_on_screen) > 0:
        return

    # 초급/중급 단어 풀에서 뽑기
    candidates = [w for w in word_list if w["difficulty"] in (1, 2)]
    if not candidates:
        candidates = word_list   # 안전장치
    if not candidates:
        return

    entry = random.choice(candidates)
    text = entry["word"]

    # 단어 폭 계산 (왼쪽 바깥에서 시작하는 x 좌표 용)
    word_surface = font_word.render(text, True, SPECIAL_WORD_COLOR)
    word_width = word_surface.get_width()

    # y는 스코어보드와 입력창 사이에서 랜덤
    y_min = TOP_INFO_HEIGHT + 20
    y_max = GAMEOVER_LINE_Y - 50
    if y_max <= y_min:
        y_max = y_min + 1  # 안전장치
    y = random.randint(y_min, y_max)

    special_words_on_screen.append({
        "text": text,
        "x": -word_width,            # 화면 왼쪽 바깥에서 등장
        "y": y,
        "speed": SPECIAL_WORD_SPEED,
        "width": word_width,
    })


def update_special_words():
    """특수 단어를 오른쪽으로 이동. 화면 밖으로 나가면 조용히 제거 (게임오버 X)."""
    # 슬라이싱 복사본으로 순회해야 제거가 안전
    for sw in special_words_on_screen[:]:
        sw["x"] += sw["speed"]
        if sw["x"] > WIDTH:
            special_words_on_screen.remove(sw)


def clear_all_visible_words():
    """화면에 보이는 모든 일반 단어 삭제 (특수 단어 효과로 호출)."""
    count = len(words_on_screen)
    words_on_screen.clear()
    return count   # 몇 개 지웠는지 반환 (점수 계산용)


# =====================================================
# 12. 입력 검사 (특수 단어 → 일반 단어 순서)
# =====================================================
def check_special_word_input():
    """
    입력값이 특수 단어와 일치하는지 검사.
    일치 시:
      - 화면의 모든 일반 단어 삭제
      - 해당 특수 단어도 삭제
      - 점수 추가 (삭제된 일반 단어 수 × 10 + 보너스)
      - 입력창 비우기
      - True 반환
    일치 안 하면 False 반환.
    """
    global input_text, composition_text, score

    typed = input_text.strip()
    if typed == "":
        return False

    for sw in special_words_on_screen:
        if sw["text"] == typed:
            # 🎆 특수 단어 적중!
            cleared_count = clear_all_visible_words()           # 일반 단어 전부 삭제
            special_words_on_screen.remove(sw)                  # 특수 단어 자신도 삭제
            score += cleared_count * 10 + SPECIAL_WORD_BONUS_SCORE
            input_text = ""
            composition_text = ""
            return True
    return False


def check_input():
    """Enter 눌렀을 때: 특수 단어를 먼저 검사, 그 다음 일반 단어 검사."""
    global input_text, composition_text, score

    # 1) 특수 단어 먼저
    if check_special_word_input():
        return

    # 2) 일반 단어 검사
    typed = input_text.strip()
    if typed == "":
        input_text = ""
        composition_text = ""
        return

    # 같은 단어 중 가장 아래에 있는 것 고르기
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
# 13. 난이도 조정
# =====================================================
def update_difficulty():
    """게임 시간이 지나면 속도/생성 간격 조절 + 레벨 업."""
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
# 14. 커서 / 단어 깜빡임
# =====================================================
def should_show_cursor():
    """커서 표시 여부."""
    if len(input_text) > 0 or len(composition_text) > 0:
        return True
    now = pygame.time.get_ticks()
    return (now // CURSOR_BLINK_MS) % 2 == 0


def should_show_words():
    """
    단어 표시 여부.
    - 레벨 5 미만: 항상 True
    - 레벨 5 이상: 1초 주기 중 0.9초 보임, 0.1초 숨김 (부드러운 깜빡임)
    ⚠️ 위치/충돌엔 영향 X. 오직 '그리기'에만 영향.
    """
    if level < BLINK_LEVEL_THRESHOLD:
        return True
    now_in_cycle = get_game_time() % BLINK_CYCLE_MS
    return now_in_cycle < BLINK_VISIBLE_MS


# =====================================================
# 15. ESC 메뉴 열고 닫기
# =====================================================
def open_esc_menu():
    """ESC 메뉴 열기 + 일시정지 시작."""
    global game_state
    game_state = GAME_STATE_ESC_MENU
    pause_game_timer()
    pygame.key.stop_text_input()


def close_esc_menu():
    """게임으로 복귀 + 일시정지 해제."""
    global game_state
    resume_game_timer()
    pygame.key.start_text_input()
    input_rect = pygame.Rect(INPUT_X, INPUT_Y, INPUT_WIDTH, INPUT_HEIGHT)
    pygame.key.set_text_input_rect(input_rect)
    game_state = GAME_STATE_PLAYING


# =====================================================
# 16. 그리기 함수들
# =====================================================
def draw_menu(screen):
    """언어 선택 화면."""
    screen.fill(BG_COLOR)

    title_surface = font_title.render("Typing Game / 타자 연습", True, TITLE_COLOR)
    screen.blit(title_surface, title_surface.get_rect(center=(WIDTH // 2, 150)))

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

    info = font_info.render("ESC: 종료 / Quit", True, (120, 120, 120))
    screen.blit(info, info.get_rect(center=(WIDTH // 2, 660)))


def draw_game(screen):
    """플레이 화면: 단어들 + 특수 단어 + 정보 + 입력창 + 도움말 + 안내."""
    screen.fill(BG_COLOR)

    # --- 일반 단어 (깜빡임 적용) ---
    show_words = should_show_words()
    if show_words:
        for word in words_on_screen:
            surface = font_word.render(word["text"], True, WORD_COLOR)
            screen.blit(surface, (word["x"], word["y"]))

    # --- ⭐ 특수 단어 (항상 표시, 빨간색) ---
    # 참고: 특수 단어는 깜빡임 대상이 아님 - 특수한 단어니까 잘 보이는 게 중요
    for sw in special_words_on_screen:
        surface = font_word.render(sw["text"], True, SPECIAL_WORD_COLOR)
        screen.blit(surface, (sw["x"], sw["y"]))

    # --- 상단 정보 (점수/레벨/시간) ---
    elapsed_sec = (get_game_time() - game_start_time) // 1000
    minutes = elapsed_sec // 60
    seconds = elapsed_sec % 60
    info_text = f"Score: {score}    Level: {level}    Time: {minutes:02d}:{seconds:02d}"
    info_surface = font_info.render(info_text, True, INFO_COLOR)
    screen.blit(info_surface, (15, 15))

    # 스코어보드 아래 얇은 구분선 (단어 생성 영역 표시)
    pygame.draw.line(screen, TOP_LINE_COLOR,
                     (0, TOP_INFO_HEIGHT), (WIDTH, TOP_INFO_HEIGHT), 1)

    # --- 게임오버 판정선 ---
    pygame.draw.line(screen, BORDER_COLOR,
                     (0, GAMEOVER_LINE_Y), (WIDTH, GAMEOVER_LINE_Y), 1)

    # --- 입력창 (중앙 배치) ---
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

    # 구석 도움말
    draw_help_text(screen)

    # 언어 모드 안내 (게임 시작 후 짧게만)
    draw_language_announcement(screen)


def draw_help_text(screen):
    """화면 오른쪽 위에 'ESC: 메뉴' 안내."""
    if game_state != GAME_STATE_PLAYING:
        return
    text = "ESC: 메뉴"
    surface = font_help.render(text, True, HELP_COLOR)
    x = WIDTH - 15 - surface.get_width()
    y = 15
    screen.blit(surface, (x, y))


def draw_language_announcement(screen):
    """게임 시작 후 ANNOUNCE_DURATION_MS 동안 입력 모드 안내 박스."""
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
    # 스코어보드 아래, 구분선 밑에 표시
    box_y = TOP_INFO_HEIGHT + 15

    pygame.draw.rect(screen, ANNOUNCE_BG,
                     (box_x, box_y, box_width, box_height), border_radius=6)
    pygame.draw.rect(screen, ANNOUNCE_TEXT,
                     (box_x, box_y, box_width, box_height), 1, border_radius=6)
    screen.blit(surface, (box_x + padding_x, box_y + padding_y))


def draw_popup_box(screen, lines, title_first=True):
    """중앙 팝업 박스 공통 그리기."""
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
    """ESC 메뉴 팝업."""
    draw_popup_box(screen, [
        "메뉴",
        "",
        "T: 현재 게임 다시 시작",
        "Q: 메인 메뉴로 나가기",
        "X: 프로그램 종료",
        "ESC: 게임으로 돌아가기",
    ])


def draw_game_over(screen):
    """게임오버 화면 + 선택지(T/Q/X)."""
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((255, 255, 255))
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
# 17. 이벤트 처리 (상태별 분기)
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
    """PLAYING 상태: 문자 입력 최우선. 기능키는 Enter/Backspace/ESC만!"""
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
    """ESC 메뉴 상태: IME 꺼져있음. T/Q/X/ESC."""
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
    """게임오버: T/Q/X."""
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_t:
            reset_current_game()
        elif event.key == pygame.K_q:
            return_to_menu()
        elif event.key == pygame.K_x:
            quit_program()


# =====================================================
# 18. 메인 루프
# =====================================================
def main():
    global last_spawn_time
    global english_words, korean_words
    global font_word, font_input, font_info, font_title, font_gameover
    global font_help, font_popup, font_announce
    global game_state

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

    # CSV 로드
    english_words, korean_words, _ = load_words_from_csv(CSV_PATH)

    game_state = GAME_STATE_MENU
    pygame.key.stop_text_input()

    # ========= 메인 루프 =========
    while True:
        # ---- 이벤트 ----
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

        # ---- 로직 업데이트 (PLAYING일 때만) ----
        if game_state == GAME_STATE_PLAYING:
            now = get_game_time()

            # 일반 단어 생성
            if now - last_spawn_time >= current_spawn_ms:
                create_word()
                last_spawn_time = now

            # 일반 단어 이동 & 게임오버 판정
            update_words()

            # ⭐ 특수 단어 생성 (예정 시각 도달 시)
            if game_state == GAME_STATE_PLAYING and now >= next_special_spawn_time:
                create_special_word()
                schedule_next_special_word()   # 다음 특수 단어 예약

            # 특수 단어 이동 (게임오버 판정엔 포함 X)
            update_special_words()

            # 난이도 조정
            update_difficulty()

        # ---- 그리기 ----
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
