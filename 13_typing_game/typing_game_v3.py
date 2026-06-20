# typing_game_v3.py
# 한컴타자연습 스타일의 파이썬 타자 연습 게임 (최종 버전)
# 실행 방법: python typing_game_v3.py
#
# [이번 버전에서 추가/개선된 점]
#  1. 게임 상태(game_state)를 명확히 구분해서 관리 (메뉴/플레이/확인창/게임오버)
#  2. Q 키 → 메뉴로 나가기 확인창
#  3. T 키 → 현재 언어 그대로 게임 리셋
#  4. ESC 키 → 프로그램 종료 확인창 (바로 꺼지지 않음)
#  5. 레벨 6 이상이면 단어가 은은하게 깜빡임
#  6. 화면 구석에 조작 안내 문구 표시
#  7. 확인창이 떠 있는 동안 시간이 정지됐다가 되살아남
#  8. PyInstaller로 exe 배포 시에도 words.csv를 잘 찾도록 경로 처리

import pygame   # 게임 라이브러리
import random   # 랜덤 선택용
import sys      # 종료 및 배포 환경 감지
import csv      # CSV 파일 읽기용
import os       # 파일 경로 처리용


# =====================================================
# 0. 배포(EXE) 환경까지 고려한 파일 경로 설정
# =====================================================
# sys.frozen: PyInstaller로 exe 변환된 상태면 True (파이썬 공식 관용구)
if getattr(sys, 'frozen', False):
    # exe로 실행 중이면 exe가 있는 폴더를 기준으로 삼는다
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 일반 파이썬 실행이면 이 .py 파일이 있는 폴더를 기준으로 삼는다
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# words.csv의 절대 경로 (실행 위치가 어디든 정확히 같은 폴더의 파일을 찾음)
CSV_PATH = os.path.join(BASE_DIR, "words.csv")


# =====================================================
# 1. 게임 상태 상수
# =====================================================
# 각 상태마다 화면에 보이는 것, 받는 입력이 달라진다.
GAME_STATE_MENU = "menu"                   # 언어 선택 화면
GAME_STATE_PLAYING = "playing"             # 실제 게임 진행
GAME_STATE_CONFIRM_QUIT = "confirm_quit"   # "메뉴로 나가시겠습니까?" 팝업
GAME_STATE_CONFIRM_EXIT = "confirm_exit"   # "프로그램을 종료하시겠습니까?" 팝업
GAME_STATE_GAME_OVER = "game_over"         # 게임 오버 화면


# =====================================================
# 2. 게임 전체에서 쓸 설정값
# =====================================================
# --- 화면 크기 ---
WIDTH = 800
HEIGHT = 600
FPS = 60

# --- 색깔 (RGB 0~255) ---
BG_COLOR = (245, 245, 235)        # 배경 - 연한 베이지
WORD_COLOR = (40, 40, 40)         # 떨어지는 단어 - 어두운 회색
INPUT_BG = (255, 255, 255)        # 입력창 배경 - 흰색
INPUT_TEXT_COLOR = (0, 0, 0)      # 확정 입력 글자 - 검정
COMPOSING_COLOR = (100, 100, 200) # 조합 중 글자 - 파란 회색
CURSOR_COLOR = (0, 0, 0)          # 커서 - 검정
BORDER_COLOR = (120, 120, 120)    # 테두리 - 회색
INFO_COLOR = (60, 80, 140)        # 정보 텍스트 - 짙은 파랑
TITLE_COLOR = (40, 60, 120)       # 제목 - 남색
GAMEOVER_COLOR = (200, 40, 40)    # GAME OVER - 빨강
BUTTON_COLOR = (220, 230, 250)    # 버튼 - 연한 파랑
BUTTON_BORDER = (80, 100, 180)    # 버튼 테두리
HELP_COLOR = (160, 160, 160)      # 구석 도움말 - 옅은 회색
POPUP_BG = (250, 250, 250)        # 팝업 배경 - 거의 흰색
POPUP_BORDER = (80, 100, 180)     # 팝업 테두리
POPUP_SHADOW = (0, 0, 0)          # 팝업 뒤 그림자

# --- 입력창 ---
INPUT_HEIGHT = 50
INPUT_Y = HEIGHT - INPUT_HEIGHT - 10
INPUT_X = 10
INPUT_WIDTH = WIDTH - 20
INPUT_PADDING = 10
GAMEOVER_LINE_Y = INPUT_Y

# --- 커서 ---
CURSOR_BLINK_MS = 500
CURSOR_WIDTH = 2

# --- 단어 깜빡임 (레벨 6 이상에서만 적용) ---
BLINK_CYCLE_MS = 1000      # 한 주기 = 1초
BLINK_VISIBLE_MS = 750     # 그 중 0.75초는 보이고, 0.25초는 안 보임
BLINK_LEVEL_THRESHOLD = 6  # 레벨 6부터 깜빡임 시작

# --- 기본 단어 리스트 (CSV를 못 읽을 때 백업) ---
DEFAULT_ENGLISH_WORDS = ["apple", "banana", "python", "code", "data",
                         "school", "game", "keyboard", "mouse", "window",
                         "screen", "music", "river", "cloud", "book"]

DEFAULT_KOREAN_WORDS = ["사과", "학교", "파이썬", "게임", "데이터",
                        "키보드", "마우스", "화면", "음악", "구름",
                        "책상", "연습", "공부", "바다", "강아지"]

# --- 난이도 ---
INITIAL_SPEED = 1.0
SPEED_STEP = 0.5
MAX_SPEED = 6.0

INITIAL_SPAWN_MS = 2000
MIN_SPAWN_MS = 800
SPAWN_STEP_MS = 100

# 레벨업 스케줄 (초 단위): 30초 → 20초 → 그 이후 15초 고정
LEVEL_UP_SCHEDULE = [30, 20]
LEVEL_UP_FIXED_INTERVAL = 15


# =====================================================
# 3. 게임 상태 전역 변수
# =====================================================
game_state = GAME_STATE_MENU

words_on_screen = []
input_text = ""               # 확정된 글자
composition_text = ""         # 조합 중인 글자

score = 0
level = 1
current_speed = INITIAL_SPEED
current_spawn_ms = INITIAL_SPAWN_MS

# 타이머 관련 (모두 "게임 시간" 기준: 일시정지 제외한 시간)
last_spawn_time = 0
game_start_time = 0
last_level_up_time = 0
level_up_index = 0

# 일시정지 관련
pause_start_time = 0          # 확인창이 뜬 순간의 실제 시각(ms)
total_paused_time = 0         # 지금까지 일시정지로 흘려보낸 누적 시간(ms)

selected_language = None
word_list = []

english_words = []            # CSV에서 불러온 영어 단어들
korean_words = []             # CSV에서 불러온 한국어 단어들

# 폰트
font_word = None
font_input = None
font_info = None
font_title = None
font_gameover = None
font_help = None              # 구석 도움말용 작은 폰트
font_popup = None             # 팝업용 폰트


# =====================================================
# 4. "게임 시간" 계산 함수 (일시정지 시간 제외)
# =====================================================
def get_game_time():
    """
    일시정지 시간을 제외한 '진짜 게임 시간(ms)'을 돌려준다.
    이 값을 기준으로 단어 생성, 레벨업 시간을 판단한다.
    """
    return pygame.time.get_ticks() - total_paused_time


# =====================================================
# 5. 일시정지 처리
# =====================================================
def pause_game_timer():
    """확인창이 뜨는 순간 호출 - 일시정지 시작 시각 기록."""
    global pause_start_time
    # 실제 시각을 기록 (total_paused_time은 건드리지 않는다!)
    pause_start_time = pygame.time.get_ticks()


def resume_game_timer():
    """확인창이 닫히는 순간 호출 - 정지됐던 시간을 누적."""
    global total_paused_time
    # 멈춰 있던 시간을 누적 (pygame.time.get_ticks() - pause_start_time)
    paused_duration = pygame.time.get_ticks() - pause_start_time
    total_paused_time += paused_duration
    # 이제 get_game_time()은 마치 아무 일 없었던 것처럼 이어진다!


# =====================================================
# 6. 한글 폰트 찾기
# =====================================================
def get_font(size):
    """한글을 표시할 수 있는 폰트를 찾아 돌려줌."""
    korean_font_candidates = [
        'malgungothic',     # 윈도우 - 맑은 고딕
        'applegothic',      # 맥 - 애플고딕
        'applesdgothicneo', # 맥
        'nanumgothic',      # 리눅스
        'notosanscjkkr',    # 구글 노토
        'gulim', 'dotum', 'batang'
    ]
    available = pygame.font.get_fonts()
    for name in korean_font_candidates:
        if name in available:
            return pygame.font.SysFont(name, size)
    return pygame.font.SysFont(None, size)


# =====================================================
# 7. CSV에서 단어 불러오기 (배포 환경 대응)
# =====================================================
def load_words_from_csv(filepath):
    """
    CSV 파일에서 영어/한국어 단어를 읽어옴.
    성공: (영어 리스트, 한국어 리스트, True)
    실패: (기본 영어, 기본 한국어, False)
    """
    # 파일 없음
    if not os.path.exists(filepath):
        print(f"[알림] '{filepath}' 파일 없음 → 기본 단어 리스트 사용")
        return DEFAULT_ENGLISH_WORDS.copy(), DEFAULT_KOREAN_WORDS.copy(), False

    eng_words = []
    kor_words = []
    try:
        # utf-8-sig: 엑셀 저장 CSV의 BOM까지 자동 처리
        with open(filepath, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)   # 첫 줄을 헤더로 인식
            for row in reader:
                language = (row.get("language") or "").strip().lower()
                word = (row.get("word") or "").strip()
                if not word:
                    continue
                if language == "en":
                    eng_words.append(word)
                elif language == "ko":
                    kor_words.append(word)

        # 둘 다 비면 기본 리스트로 폴백
        if not eng_words and not kor_words:
            print(f"[알림] CSV에 유효 단어 없음 → 기본 리스트 사용")
            return DEFAULT_ENGLISH_WORDS.copy(), DEFAULT_KOREAN_WORDS.copy(), False

        # 한쪽 언어만 비어도 그 쪽만 채움
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
# 8. 게임 초기화 (새로 시작하거나 T 리셋용)
# =====================================================
def init_game():
    """게임 상태값들을 처음 상태로 되돌림."""
    global words_on_screen, input_text, composition_text, score, level
    global current_speed, current_spawn_ms
    global last_spawn_time, game_start_time, last_level_up_time, level_up_index
    global total_paused_time

    words_on_screen = []
    input_text = ""
    composition_text = ""
    score = 0
    level = 1
    current_speed = INITIAL_SPEED
    current_spawn_ms = INITIAL_SPAWN_MS

    # 중요: 일시정지 누적 시간도 리셋
    total_paused_time = 0

    # 모든 타이머는 "지금 이 순간"부터 시작
    now = pygame.time.get_ticks()
    last_spawn_time = now
    game_start_time = now
    last_level_up_time = now
    level_up_index = 0


def reset_current_game():
    """T 키: 같은 언어로 게임만 처음부터 다시 시작."""
    # word_list, selected_language는 그대로 두고, 나머지만 초기화
    init_game()


def return_to_menu():
    """Q 확인창에서 Y: 메뉴로 복귀 (언어 선택부터 다시)."""
    global game_state, selected_language, word_list, input_text, composition_text
    game_state = GAME_STATE_MENU
    selected_language = None
    word_list = []
    input_text = ""
    composition_text = ""
    # 메뉴 화면에서는 IME 꺼두기
    pygame.key.stop_text_input()


# =====================================================
# 9. 새 단어 생성 / 단어 이동 / 입력 검사
# =====================================================
def create_word():
    """단어 하나를 랜덤으로 만들어 화면 맨 위에 추가."""
    text = random.choice(word_list)
    word_surface = font_word.render(text, True, WORD_COLOR)
    word_width = word_surface.get_width()
    x = random.randint(0, WIDTH - word_width)
    y = 0
    words_on_screen.append({"text": text, "x": x, "y": y})


def update_words():
    """모든 단어를 아래로 이동. 바닥에 닿으면 게임오버."""
    global game_state
    for word in words_on_screen:
        word["y"] += current_speed
        if word["y"] >= GAMEOVER_LINE_Y:
            game_state = GAME_STATE_GAME_OVER


def check_input():
    """Enter 눌렀을 때: 확정 입력값과 일치하는 단어 삭제."""
    global input_text, composition_text, score
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
# 10. 난이도 조정
# =====================================================
def update_difficulty():
    """게임 시간이 지나면 속도/생성 간격을 조절."""
    global current_speed, current_spawn_ms, level
    global last_level_up_time, level_up_index

    now = get_game_time()   # ⚠️ 반드시 게임 시간 사용 (일시정지 제외)
    elapsed_since_levelup = now - last_level_up_time

    # 이번 레벨업까지 필요한 시간(초)
    if level_up_index < len(LEVEL_UP_SCHEDULE):
        interval_seconds = LEVEL_UP_SCHEDULE[level_up_index]
    else:
        interval_seconds = LEVEL_UP_FIXED_INTERVAL   # 이후 15초 고정

    if elapsed_since_levelup >= interval_seconds * 1000:
        level += 1
        current_speed = min(current_speed + SPEED_STEP, MAX_SPEED)
        current_spawn_ms = max(current_spawn_ms - SPAWN_STEP_MS, MIN_SPAWN_MS)
        last_level_up_time = now
        if level_up_index < len(LEVEL_UP_SCHEDULE) - 1:
            level_up_index += 1
        elif level_up_index == len(LEVEL_UP_SCHEDULE) - 1:
            # 마지막 인덱스에서 한 번 더 올려두면 이후엔 고정 간격 사용
            level_up_index += 1


# =====================================================
# 11. 커서 표시 여부 / 단어 깜빡임 여부
# =====================================================
def should_show_cursor():
    """커서를 지금 그려야 하나? (깜빡임 로직)"""
    if len(input_text) > 0 or len(composition_text) > 0:
        return True   # 글자가 있으면 항상 보임
    # 비어 있으면 500ms 간격으로 깜빡
    now = pygame.time.get_ticks()
    return (now // CURSOR_BLINK_MS) % 2 == 0


def should_show_words():
    """
    떨어지는 단어를 지금 그려야 하나?
    - 레벨 5 이하: 항상 True
    - 레벨 6 이상: 1초 주기 중 0.75초만 True
    ⚠️ 위치/충돌 판정과는 무관! 오직 '그리기'만 영향을 줌
    """
    if level < BLINK_LEVEL_THRESHOLD:
        return True
    # 게임 시간을 기준으로 계산 (정지 중엔 깜빡이지 않음)
    now_in_cycle = get_game_time() % BLINK_CYCLE_MS
    return now_in_cycle < BLINK_VISIBLE_MS


# =====================================================
# 12. 그리기 함수들
# =====================================================
def draw_menu(screen):
    """메뉴(언어 선택) 화면 그리기."""
    screen.fill(BG_COLOR)

    title_surface = font_title.render("Typing Game / 타자 연습", True, TITLE_COLOR)
    screen.blit(title_surface, title_surface.get_rect(center=(WIDTH // 2, 120)))

    guide = font_info.render("언어를 선택하세요 / Select Language", True, INFO_COLOR)
    screen.blit(guide, guide.get_rect(center=(WIDTH // 2, 200)))

    # 버튼 1: English
    btn1_rect = pygame.Rect(WIDTH // 2 - 150, 280, 300, 70)
    pygame.draw.rect(screen, BUTTON_COLOR, btn1_rect, border_radius=10)
    pygame.draw.rect(screen, BUTTON_BORDER, btn1_rect, 3, border_radius=10)
    btn1_text = font_info.render("[ 1 ]  English", True, TITLE_COLOR)
    screen.blit(btn1_text, btn1_text.get_rect(center=btn1_rect.center))

    # 버튼 2: 한국어
    btn2_rect = pygame.Rect(WIDTH // 2 - 150, 370, 300, 70)
    pygame.draw.rect(screen, BUTTON_COLOR, btn2_rect, border_radius=10)
    pygame.draw.rect(screen, BUTTON_BORDER, btn2_rect, 3, border_radius=10)
    btn2_text = font_info.render("[ 2 ]  한국어", True, TITLE_COLOR)
    screen.blit(btn2_text, btn2_text.get_rect(center=btn2_rect.center))

    # 하단 안내
    info = font_info.render("ESC: 종료 / Quit", True, (120, 120, 120))
    screen.blit(info, info.get_rect(center=(WIDTH // 2, 520)))


def draw_game(screen):
    """실제 게임 화면 그리기 (단어들 + 정보 + 입력창 + 커서 + 도움말)."""
    screen.fill(BG_COLOR)

    # --- 떨어지는 단어들 ---
    # 레벨 6+ 에서는 깜빡임 적용. 단, 위치는 영향 X.
    show_words = should_show_words()
    for word in words_on_screen:
        if show_words:
            surface = font_word.render(word["text"], True, WORD_COLOR)
            screen.blit(surface, (word["x"], word["y"]))
        # show_words가 False면 안 그리지만 word["y"]는 계속 업데이트되고 있음

    # --- 상단 정보 (점수, 레벨, 시간) ---
    elapsed_sec = (get_game_time() - game_start_time) // 1000
    minutes = elapsed_sec // 60
    seconds = elapsed_sec % 60
    info_text = f"Score: {score}    Level: {level}    Time: {minutes:02d}:{seconds:02d}"
    info_surface = font_info.render(info_text, True, INFO_COLOR)
    screen.blit(info_surface, (10, 10))

    # --- 게임 오버 판정선 ---
    pygame.draw.line(screen, BORDER_COLOR,
                     (0, GAMEOVER_LINE_Y), (WIDTH, GAMEOVER_LINE_Y), 1)

    # --- 입력창 ---
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


def draw_help_text(screen):
    """
    화면 구석에 작은 조작 안내 문구 표시.
    현재 game_state에 따라 다르게 표시 (팝업이 뜨면 숨김).
    """
    # 팝업이 떠 있으면 구석 안내는 숨김 (겹치지 않게)
    if game_state in (GAME_STATE_CONFIRM_QUIT, GAME_STATE_CONFIRM_EXIT):
        return
    # 플레이 중일 때만 표시
    if game_state != GAME_STATE_PLAYING:
        return

    help_lines = [
        "Q: 메뉴로 나가기",
        "T: 현재 게임 다시 시작",
        "ESC: 프로그램 종료",
    ]
    # 화면 오른쪽 위 (정보 텍스트와 입력창 사이의 안전지대)
    line_height = font_help.get_height() + 2
    right_margin = 10
    top_margin = 10
    # 각 줄을 위에서부터 그리기 (오른쪽 정렬)
    for i, line in enumerate(help_lines):
        surface = font_help.render(line, True, HELP_COLOR)
        # 오른쪽 정렬: WIDTH - 우측여백 - 글자 폭
        x = WIDTH - right_margin - surface.get_width()
        y = top_margin + i * line_height
        screen.blit(surface, (x, y))


def draw_popup_box(screen, lines, color_highlight_first=True):
    """
    중앙 팝업 박스를 그리는 공통 함수.
    lines: 줄 단위 문자열 리스트 (첫 줄이 보통 제목, 나머지는 선택지)
    """
    # 박스 크기 계산 (가장 긴 줄 기준 + 여유)
    box_width = 500
    box_height = 60 + len(lines) * (font_popup.get_height() + 8) + 20
    box_x = (WIDTH - box_width) // 2
    box_y = (HEIGHT - box_height) // 2

    # 살짝 뒤 그림자 효과
    shadow_offset = 6
    shadow = pygame.Surface((box_width, box_height))
    shadow.set_alpha(60)
    shadow.fill(POPUP_SHADOW)
    screen.blit(shadow, (box_x + shadow_offset, box_y + shadow_offset))

    # 박스 본체
    pygame.draw.rect(screen, POPUP_BG,
                     (box_x, box_y, box_width, box_height), border_radius=12)
    pygame.draw.rect(screen, POPUP_BORDER,
                     (box_x, box_y, box_width, box_height), 3, border_radius=12)

    # 글자들
    current_y = box_y + 30
    for i, line in enumerate(lines):
        # 첫 줄은 조금 더 진하게(제목), 나머지는 정보색
        color = TITLE_COLOR if (i == 0 and color_highlight_first) else INFO_COLOR
        surface = font_popup.render(line, True, color)
        rect = surface.get_rect(center=(WIDTH // 2, current_y + font_popup.get_height() // 2))
        screen.blit(surface, rect)
        current_y += font_popup.get_height() + 8


def show_confirm_quit_popup(screen):
    """Q 키로 뜬 '메뉴로 나가기' 확인창."""
    draw_popup_box(screen, [
        "게임을 종료하시겠습니까?",
        "",
        "Y: 예, 메인 메뉴로 이동",
        "N: 아니오, 계속 진행",
    ])


def show_confirm_exit_popup(screen):
    """ESC 키로 뜬 '프로그램 종료' 확인창."""
    draw_popup_box(screen, [
        "프로그램을 종료하시겠습니까?",
        "",
        "Y: 예, 프로그램 종료",
        "N: 아니오, 계속 진행",
    ])


def draw_game_over(screen):
    """GAME OVER 오버레이."""
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((255, 255, 255))
    screen.blit(overlay, (0, 0))

    go_surface = font_gameover.render("GAME OVER", True, GAMEOVER_COLOR)
    screen.blit(go_surface, go_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80)))

    score_text = f"최종 점수 / Final Score: {score}"
    score_surface = font_info.render(score_text, True, TITLE_COLOR)
    screen.blit(score_surface, score_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

    # 안내 문구 (너무 진하지 않게 INFO_COLOR 정도)
    hint1 = font_help.render("R: 메인 메뉴로 돌아가기", True, INFO_COLOR)
    screen.blit(hint1, hint1.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60)))
    hint2 = font_help.render("ESC: 프로그램 종료", True, INFO_COLOR)
    screen.blit(hint2, hint2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 90)))


# =====================================================
# 13. 이벤트 처리 (상태별로 분기)
# =====================================================
def handle_event_menu(event):
    """메뉴 상태에서의 키 입력: 1, 2, ESC."""
    global game_state, selected_language, word_list
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_1:
            selected_language = "english"
            word_list = english_words
            enter_playing_state()
        elif event.key == pygame.K_2:
            selected_language = "korean"
            word_list = korean_words
            enter_playing_state()
        elif event.key == pygame.K_ESCAPE:
            # 메뉴에서 ESC는 바로 종료 (확인창 없이) - 보통 메뉴는 안전한 위치라서
            pygame.quit()
            sys.exit()


def enter_playing_state():
    """메뉴 → 플레이 상태로 전환."""
    global game_state
    init_game()
    pygame.key.start_text_input()
    input_rect = pygame.Rect(INPUT_X, INPUT_Y, INPUT_WIDTH, INPUT_HEIGHT)
    pygame.key.set_text_input_rect(input_rect)
    game_state = GAME_STATE_PLAYING


def handle_event_playing(event):
    """플레이 중 이벤트 처리."""
    global input_text, composition_text, game_state

    # (A) TEXTINPUT: 확정된 글자
    if event.type == pygame.TEXTINPUT:
        input_text += event.text
        composition_text = ""
        return

    # (B) TEXTEDITING: 조합 중 글자
    if event.type == pygame.TEXTEDITING:
        composition_text = event.text
        return

    # (C) KEYDOWN: 특수키
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_RETURN:
            check_input()
        elif event.key == pygame.K_BACKSPACE:
            # 조합 중이면 IME가 처리하므로 건드리지 않음
            if composition_text == "":
                input_text = input_text[:-1]
        elif event.key == pygame.K_q:
            # Q: 메뉴 복귀 확인창 열기
            open_confirm_quit()
        elif event.key == pygame.K_t:
            # T: 현재 언어로 게임 리셋 (바로 시작)
            reset_current_game()
        elif event.key == pygame.K_ESCAPE:
            # ESC: 프로그램 종료 확인창 열기
            open_confirm_exit()


def open_confirm_quit():
    """Q → 확인창 열기 (시간 정지 시작)."""
    global game_state
    game_state = GAME_STATE_CONFIRM_QUIT
    pause_game_timer()
    # 팝업 동안 IME는 중지 (Y/N만 받음)
    pygame.key.stop_text_input()


def open_confirm_exit():
    """ESC → 확인창 열기 (시간 정지 시작)."""
    global game_state
    game_state = GAME_STATE_CONFIRM_EXIT
    pause_game_timer()
    pygame.key.stop_text_input()


def close_confirm_back_to_playing():
    """N → 팝업 닫고 게임으로 복귀 (시간 보정 후 재개)."""
    global game_state
    resume_game_timer()
    # 다시 IME 활성화
    pygame.key.start_text_input()
    input_rect = pygame.Rect(INPUT_X, INPUT_Y, INPUT_WIDTH, INPUT_HEIGHT)
    pygame.key.set_text_input_rect(input_rect)
    game_state = GAME_STATE_PLAYING


def handle_event_confirm_quit(event):
    """Q 확인창 상태: Y면 메뉴로, N이면 게임 복귀."""
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_y:
            # Y: 메뉴로 복귀 (정지 시간은 버림 - 어차피 새 게임)
            return_to_menu()
        elif event.key == pygame.K_n:
            # N: 게임 복귀
            close_confirm_back_to_playing()


def handle_event_confirm_exit(event):
    """ESC 확인창 상태: Y면 프로그램 종료, N이면 게임 복귀."""
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_y:
            pygame.quit()
            sys.exit()
        elif event.key == pygame.K_n:
            close_confirm_back_to_playing()


def handle_event_game_over(event):
    """게임오버 상태: R이면 메뉴로, ESC면 종료."""
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_r:
            return_to_menu()
        elif event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()


# =====================================================
# 14. 메인 루프
# =====================================================
def main():
    """게임 전체 실행 (하나의 루프로 상태별 분기)."""
    global last_spawn_time
    global english_words, korean_words
    global font_word, font_input, font_info, font_title, font_gameover, font_help, font_popup
    global game_state

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Typing Game - 타자 연습")
    clock = pygame.time.Clock()

    # 폰트
    font_word = get_font(32)
    font_input = get_font(28)
    font_info = get_font(24)
    font_title = get_font(48)
    font_gameover = get_font(72)
    font_help = get_font(16)      # 구석 도움말 (작게)
    font_popup = get_font(26)     # 팝업용

    # CSV 불러오기
    english_words, korean_words, _ = load_words_from_csv(CSV_PATH)

    # 시작은 메뉴 상태
    game_state = GAME_STATE_MENU
    pygame.key.stop_text_input()

    # ============ 메인 루프 ============
    while True:
        # ---------- 이벤트 처리 ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # 상태에 따라 적절한 핸들러 호출
            if game_state == GAME_STATE_MENU:
                handle_event_menu(event)
            elif game_state == GAME_STATE_PLAYING:
                handle_event_playing(event)
            elif game_state == GAME_STATE_CONFIRM_QUIT:
                handle_event_confirm_quit(event)
            elif game_state == GAME_STATE_CONFIRM_EXIT:
                handle_event_confirm_exit(event)
            elif game_state == GAME_STATE_GAME_OVER:
                handle_event_game_over(event)

        # ---------- 로직 업데이트 ----------
        # 플레이 상태일 때만 단어 이동/생성/난이도 증가
        if game_state == GAME_STATE_PLAYING:
            now = get_game_time()   # 일시정지 제외한 시간
            # 단어 생성
            if now - last_spawn_time >= current_spawn_ms:
                create_word()
                last_spawn_time = now
            # 단어 이동 및 게임오버 판정
            update_words()
            # 난이도 조정
            update_difficulty()

        # ---------- 그리기 ----------
        if game_state == GAME_STATE_MENU:
            draw_menu(screen)
        else:
            # 플레이/확인창/게임오버 모두 게임 화면을 기본으로 그린 후
            # 상태에 맞는 오버레이를 얹음
            draw_game(screen)
            if game_state == GAME_STATE_CONFIRM_QUIT:
                show_confirm_quit_popup(screen)
            elif game_state == GAME_STATE_CONFIRM_EXIT:
                show_confirm_exit_popup(screen)
            elif game_state == GAME_STATE_GAME_OVER:
                draw_game_over(screen)

        pygame.display.flip()
        clock.tick(FPS)


# 프로그램 시작점
if __name__ == "__main__":
    main()
