# typing_game_v5.py
# 한컴타자연습 스타일의 파이썬 타자 연습 게임 (ESC 메뉴 통합 버전)
# 실행 방법: python typing_game_v5.py
#
# [이번 버전에서 바뀐 점]
#  1. 게임 화면 크기를 800x600에서 1000x750으로 확대 → 기존 4:3 비율 유지
#  2. 화면 확대에 맞춰 입력창, 폰트, 메뉴 버튼, 팝업 박스 크기 조정
#  3. 게임오버 조작키를 ESC 메뉴와 동일하게 통일
#     - T: 같은 언어로 다시 시작
#     - Q: 메인 메뉴로 이동
#     - X: 프로그램 종료
#  4. 기존 게임오버 조작키 R/M/X 중 R, M을 제거하고 T/Q/X 방식으로 변경

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
    # exe로 실행 중이면 exe가 있는 폴더를 기준으로 삼는다
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 일반 파이썬 실행이면 이 .py 파일이 있는 폴더를 기준으로 삼는다
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# words.csv의 절대 경로 (어디서 실행하든 정확히 같은 폴더의 파일을 찾음)
CSV_PATH = os.path.join(BASE_DIR, "words.csv")


# =====================================================
# 1. 게임 상태 상수 (단순화됨!)
# =====================================================
GAME_STATE_MENU = "menu"              # 언어 선택 화면
GAME_STATE_PLAYING = "playing"        # 실제 게임 진행
GAME_STATE_ESC_MENU = "esc_menu"      # ESC 메뉴 팝업 (리셋/메인/종료 통합)
GAME_STATE_GAME_OVER = "game_over"    # 게임 오버 화면


# =====================================================
# 2. 설정값 (색, 크기 등)
# =====================================================
# --- 화면 ---
WIDTH = 1000
HEIGHT = 750
FPS = 60

# --- 색깔 ---
BG_COLOR = (245, 245, 235)
WORD_COLOR = (40, 40, 40)
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
ANNOUNCE_BG = (255, 250, 220)     # 입력 모드 안내 - 연한 노랑
ANNOUNCE_TEXT = (100, 80, 30)     # 안내 글씨 - 진한 갈색

# --- 입력창 ---
INPUT_HEIGHT = 60
INPUT_Y = HEIGHT - INPUT_HEIGHT - 15
INPUT_X = 15
INPUT_WIDTH = WIDTH - 30
INPUT_PADDING = 12
GAMEOVER_LINE_Y = INPUT_Y

# --- 커서 ---
CURSOR_BLINK_MS = 500
CURSOR_WIDTH = 2

# --- 단어 깜빡임 ---
BLINK_CYCLE_MS = 1000
BLINK_VISIBLE_MS = 750
BLINK_LEVEL_THRESHOLD = 5   # 레벨 5 이상부터 깜빡임

# --- 입력 모드 안내 표시 시간 ---
ANNOUNCE_DURATION_MS = 3000   # 게임 시작 후 3초간 표시

# --- 기본 단어 리스트 (CSV 없을 때 백업) ---
DEFAULT_ENGLISH_WORDS = ["apple", "banana", "python", "code", "data",
                         "school", "game", "keyboard", "mouse", "window",
                         "screen", "music", "river", "cloud", "book",
                         "quiet", "type", "text", "quit", "quick"]

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
LEVEL_UP_SCHEDULE = [30, 20]    # 30초 → 20초 → 이후 15초 고정
LEVEL_UP_FIXED_INTERVAL = 15


# =====================================================
# 3. 전역 상태 변수
# =====================================================
game_state = GAME_STATE_MENU

words_on_screen = []
input_text = ""
composition_text = ""

score = 0
level = 1
current_speed = INITIAL_SPEED
current_spawn_ms = INITIAL_SPAWN_MS

# 타이머 (게임 시간 기준: 일시정지 제외)
last_spawn_time = 0
game_start_time = 0
last_level_up_time = 0
level_up_index = 0

# 일시정지 관련
pause_start_time = 0
total_paused_time = 0

selected_language = None    # "english" / "korean"
word_list = []

english_words = []
korean_words = []

# 폰트들
font_word = None
font_input = None
font_info = None
font_title = None
font_gameover = None
font_help = None
font_popup = None
font_announce = None


# =====================================================
# 4. 시간 관련 함수들
# =====================================================
def get_game_time():
    """
    일시정지 시간을 제외한 '게임 시간(ms)'.
    단어 생성/레벨업/경과시간 표시/단어 깜빡임 모두 이 값을 기준으로 계산한다.
    → ESC 메뉴가 떠 있는 동안엔 이 시간이 멈춘 것처럼 보이게 된다.
    """
    return pygame.time.get_ticks() - total_paused_time


def pause_game_timer():
    """ESC 메뉴가 열리는 순간 호출 - 일시정지 시작 시각 기록."""
    global pause_start_time
    pause_start_time = pygame.time.get_ticks()


def resume_game_timer():
    """ESC 메뉴가 닫히고 게임으로 돌아가는 순간 호출 - 멈춰있던 시간 누적."""
    global total_paused_time
    paused_duration = pygame.time.get_ticks() - pause_start_time
    total_paused_time += paused_duration


# =====================================================
# 5. 한글 폰트 찾기
# =====================================================
def get_font(size):
    """한글을 표시할 수 있는 폰트를 찾아 돌려줌."""
    korean_font_candidates = [
        'malgungothic',     # 윈도우 - 맑은 고딕
        'applegothic',      # 맥 - 애플고딕
        'applesdgothicneo', # 맥
        'nanumgothic',      # 리눅스
        'notosanscjkkr',
        'gulim', 'dotum', 'batang'
    ]
    available = pygame.font.get_fonts()
    for name in korean_font_candidates:
        if name in available:
            return pygame.font.SysFont(name, size)
    return pygame.font.SysFont(None, size)


# =====================================================
# 6. CSV에서 단어 불러오기 (배포 환경 대응)
# =====================================================
def load_words_from_csv(filepath):
    """
    CSV에서 영어/한국어 단어를 읽어옴.
    성공: (영어 리스트, 한국어 리스트, True)
    실패: 기본 리스트 사용, (..., False)
    """
    if not os.path.exists(filepath):
        print(f"[알림] '{filepath}' 파일 없음 → 기본 단어 리스트 사용")
        return DEFAULT_ENGLISH_WORDS.copy(), DEFAULT_KOREAN_WORDS.copy(), False

    eng_words = []
    kor_words = []
    try:
        # utf-8-sig: 엑셀 CSV의 BOM까지 자동 처리
        with open(filepath, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                language = (row.get("language") or "").strip().lower()
                word = (row.get("word") or "").strip()
                if not word:
                    continue
                if language == "en":
                    eng_words.append(word)
                elif language == "ko":
                    kor_words.append(word)

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
# 7. 게임 초기화 / 전환 함수들
# =====================================================
def init_game():
    """게임 상태값들을 처음 상태로 되돌림 (T 리셋 / 게임오버 R 재시작에도 사용)."""
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

    # 일시정지 누적 시간도 리셋 (새 게임이므로)
    total_paused_time = 0

    now = pygame.time.get_ticks()
    last_spawn_time = now
    game_start_time = now
    last_level_up_time = now
    level_up_index = 0


def start_playing():
    """
    플레이 상태로 진입 (IME 켜기 + 상태 전환).
    → 메뉴에서 언어 선택했을 때, T 리셋했을 때, 게임오버 R 눌렀을 때 호출.
    """
    global game_state
    init_game()
    # IME(한글 입력기) 활성화
    pygame.key.start_text_input()
    input_rect = pygame.Rect(INPUT_X, INPUT_Y, INPUT_WIDTH, INPUT_HEIGHT)
    pygame.key.set_text_input_rect(input_rect)
    game_state = GAME_STATE_PLAYING


def reset_current_game():
    """같은 언어 유지한 채 게임만 재시작 (T 키 / 게임오버 R 키)."""
    start_playing()


def return_to_menu():
    """현재 게임을 버리고 언어 선택 화면으로 이동 (ESC 메뉴의 Q / 게임오버 M)."""
    global game_state, selected_language, word_list, input_text, composition_text
    game_state = GAME_STATE_MENU
    selected_language = None
    word_list = []
    input_text = ""
    composition_text = ""
    # 메뉴에서는 IME 비활성화 (숫자 키만 쓰면 되니까)
    pygame.key.stop_text_input()


def quit_program():
    """프로그램 완전 종료."""
    pygame.quit()
    sys.exit()


# =====================================================
# 8. 단어 생성 / 이동 / 입력 검사
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
            enter_game_over_state()
            break   # 게임오버 됐으니 더 볼 필요 없음


def enter_game_over_state():
    """게임오버 상태로 전환 (IME 끄기 포함)."""
    global game_state
    game_state = GAME_STATE_GAME_OVER
    # ⚠️ 중요: IME 꺼야 한국어 상태에서도 R/M/X 키가 정상 동작!
    pygame.key.stop_text_input()


def check_input():
    """Enter 눌렀을 때: 확정 입력값과 일치하는 단어 삭제."""
    global input_text, composition_text, score
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
# 9. 난이도 조정
# =====================================================
def update_difficulty():
    """게임 시간이 지나면 속도/생성 간격 조절."""
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
# 10. 커서/단어 깜빡임 판정
# =====================================================
def should_show_cursor():
    """커서 표시 여부."""
    if len(input_text) > 0 or len(composition_text) > 0:
        return True
    now = pygame.time.get_ticks()
    return (now // CURSOR_BLINK_MS) % 2 == 0


def should_show_words():
    """
    단어 표시 여부 (레벨 5 미만은 항상 True).
    ⚠️ 위치나 충돌에는 영향 X. 오직 그리기만 영향.
    """
    if level < BLINK_LEVEL_THRESHOLD:
        return True
    now_in_cycle = get_game_time() % BLINK_CYCLE_MS
    return now_in_cycle < BLINK_VISIBLE_MS


# =====================================================
# 11. ESC 메뉴 열고 닫기
# =====================================================
def open_esc_menu():
    """PLAYING 중 ESC 눌렀을 때: ESC 메뉴 열기 + 일시정지 시작."""
    global game_state
    game_state = GAME_STATE_ESC_MENU
    pause_game_timer()
    # 팝업 동안 IME 끄기 (T, Q, X를 기능키로 받기 위해)
    pygame.key.stop_text_input()


def close_esc_menu():
    """ESC 메뉴에서 ESC 눌러 게임으로 복귀: 일시정지 해제 + 상태 복원."""
    global game_state
    resume_game_timer()
    # IME 재활성화 (다시 타자 입력 받기)
    pygame.key.start_text_input()
    input_rect = pygame.Rect(INPUT_X, INPUT_Y, INPUT_WIDTH, INPUT_HEIGHT)
    pygame.key.set_text_input_rect(input_rect)
    game_state = GAME_STATE_PLAYING


# =====================================================
# 12. 그리기 함수들
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
    """게임 플레이 화면 (단어, 정보, 입력창, 커서, 도움말, 안내문구)."""
    screen.fill(BG_COLOR)

    # --- 떨어지는 단어들 (레벨 5+ 는 깜빡임) ---
    show_words = should_show_words()
    for word in words_on_screen:
        if show_words:
            surface = font_word.render(word["text"], True, WORD_COLOR)
            screen.blit(surface, (word["x"], word["y"]))

    # --- 상단 정보 (점수/레벨/시간) ---
    elapsed_sec = (get_game_time() - game_start_time) // 1000
    minutes = elapsed_sec // 60
    seconds = elapsed_sec % 60
    info_text = f"Score: {score}    Level: {level}    Time: {minutes:02d}:{seconds:02d}"
    info_surface = font_info.render(info_text, True, INFO_COLOR)
    screen.blit(info_surface, (10, 10))

    # --- 게임오버 판정선 ---
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

    # 언어 모드 안내 (게임 시작 후 일정 시간만)
    draw_language_announcement(screen)


def draw_help_text(screen):
    """
    화면 구석 조작 안내.
    - PLAYING 중: "ESC: 메뉴" 한 줄만 (Q/T는 이제 기능키 아니므로 표시 안 함)
    - 다른 상태: 숨김 (팝업과 겹침 방지 or 해당 화면에 자체 안내 존재)
    """
    if game_state != GAME_STATE_PLAYING:
        return
    text = "ESC: 메뉴"
    surface = font_help.render(text, True, HELP_COLOR)
    # 오른쪽 위 (정보 텍스트와 겹치지 않게)
    x = WIDTH - 10 - surface.get_width()
    y = 10
    screen.blit(surface, (x, y))


def draw_language_announcement(screen):
    """
    게임 시작 후 ANNOUNCE_DURATION_MS 동안 입력 모드 안내 표시.
    """
    elapsed = get_game_time() - game_start_time
    if elapsed > ANNOUNCE_DURATION_MS:
        return   # 시간 지나면 안 보임

    # 언어별 문구
    if selected_language == "korean":
        text = "한국어 모드입니다. 한글 입력 상태에서 플레이하세요."
    else:
        text = "English mode. Please use English keyboard input."

    # 배경 박스 (연한 노랑)
    surface = font_announce.render(text, True, ANNOUNCE_TEXT)
    padding_x = 16
    padding_y = 8
    box_width = surface.get_width() + padding_x * 2
    box_height = surface.get_height() + padding_y * 2
    box_x = (WIDTH - box_width) // 2
    box_y = 45   # 점수 표시줄(y=10) 아래쪽

    pygame.draw.rect(screen, ANNOUNCE_BG,
                     (box_x, box_y, box_width, box_height), border_radius=6)
    pygame.draw.rect(screen, ANNOUNCE_TEXT,
                     (box_x, box_y, box_width, box_height), 1, border_radius=6)

    screen.blit(surface, (box_x + padding_x, box_y + padding_y))


def draw_popup_box(screen, lines, title_first=True):
    """중앙 팝업 박스 그리는 공통 함수."""
    box_width = 620
    line_height = font_popup.get_height() + 8
    box_height = 40 + len(lines) * line_height + 20
    box_x = (WIDTH - box_width) // 2
    box_y = (HEIGHT - box_height) // 2

    # 그림자
    shadow = pygame.Surface((box_width, box_height))
    shadow.set_alpha(60)
    shadow.fill(POPUP_SHADOW)
    screen.blit(shadow, (box_x + 6, box_y + 6))

    # 박스 본체
    pygame.draw.rect(screen, POPUP_BG,
                     (box_x, box_y, box_width, box_height), border_radius=12)
    pygame.draw.rect(screen, POPUP_BORDER,
                     (box_x, box_y, box_width, box_height), 3, border_radius=12)

    # 글자들
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
    """게임오버 화면 (T/Q/X 선택지 표시)."""
    # 뒤 배경 흐리게
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((255, 255, 255))
    screen.blit(overlay, (0, 0))

    # GAME OVER
    go_surface = font_gameover.render("GAME OVER", True, GAMEOVER_COLOR)
    screen.blit(go_surface, go_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 160)))

    # 최종 점수
    score_text = f"최종 점수 / Final Score: {score}"
    score_surface = font_info.render(score_text, True, TITLE_COLOR)
    screen.blit(score_surface, score_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 70)))

    # 선택 메뉴 (팝업 스타일)
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
# 13. 이벤트 처리 (상태별 분기)
# =====================================================
def handle_event_menu(event):
    """MENU 상태: 1/2로 언어 선택, ESC로 종료."""
    global selected_language, word_list
    # KEYDOWN만 처리 (TEXTINPUT 처리 안 함 → IME 꺼져있음)
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
    """
    PLAYING 상태: 문자 입력 최우선!
    q, t, x, r, m 같은 키들도 그냥 일반 문자로 처리됨.
    기능키로 처리되는 건 오직 Enter, Backspace, ESC 세 개뿐!
    """
    global input_text, composition_text

    # (A) TEXTINPUT: 확정된 글자 (영어 q, t, x 등 모두 여기로 옴)
    if event.type == pygame.TEXTINPUT:
        input_text += event.text
        composition_text = ""
        return

    # (B) TEXTEDITING: 조합 중인 한글
    if event.type == pygame.TEXTEDITING:
        composition_text = event.text
        return

    # (C) KEYDOWN: Enter/Backspace/ESC만 기능키
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_RETURN:
            check_input()
        elif event.key == pygame.K_BACKSPACE:
            if composition_text == "":
                input_text = input_text[:-1]
        elif event.key == pygame.K_ESCAPE:
            open_esc_menu()
        # ⚠️ Q, T, X, R, M 등은 여기서 처리하지 않음!
        #    → TEXTINPUT에서 일반 문자로 처리되기 때문에
        #    → 영어 단어 'quit', 'type', 'text' 등 정상 입력 가능


def handle_event_esc_menu(event):
    """
    ESC_MENU 상태: KEYDOWN만 처리. TEXTINPUT/TEXTEDITING은 무시.
    IME가 꺼져 있으므로 한국어 상태여도 T/Q/X/ESC 키가 정상 인식됨.
    """
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_t:
            # 같은 언어 유지, 게임 리셋
            reset_current_game()
        elif event.key == pygame.K_q:
            # 메인 메뉴로 나가기
            return_to_menu()
        elif event.key == pygame.K_x:
            # 프로그램 종료
            quit_program()
        elif event.key == pygame.K_ESCAPE:
            # 게임으로 복귀
            close_esc_menu()


def handle_event_game_over(event):
    """
    GAME_OVER 상태: KEYDOWN만 처리.
    IME가 꺼져 있어서 한국어 입력 상태라도 T/Q/X가 정상 동작!
    """
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_t:
            # 같은 언어로 재시작
            reset_current_game()
        elif event.key == pygame.K_q:
            # 메인 메뉴로
            return_to_menu()
        elif event.key == pygame.K_x:
            # 프로그램 종료
            quit_program()


# =====================================================
# 14. 메인 루프
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

    # 폰트 준비
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

    # 시작은 메뉴 상태 (IME 꺼두기)
    game_state = GAME_STATE_MENU
    pygame.key.stop_text_input()

    # ======== 메인 루프 ========
    while True:
        # ---- 이벤트 처리 ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_program()

            # 상태별 핸들러로 분기
            if game_state == GAME_STATE_MENU:
                handle_event_menu(event)
            elif game_state == GAME_STATE_PLAYING:
                handle_event_playing(event)
            elif game_state == GAME_STATE_ESC_MENU:
                handle_event_esc_menu(event)
            elif game_state == GAME_STATE_GAME_OVER:
                handle_event_game_over(event)

        # ---- 로직 업데이트 (PLAYING일 때만!) ----
        if game_state == GAME_STATE_PLAYING:
            now = get_game_time()
            # 단어 생성
            if now - last_spawn_time >= current_spawn_ms:
                create_word()
                last_spawn_time = now
            # 단어 이동 & 게임오버 판정
            update_words()
            # 난이도 조정
            update_difficulty()

        # ---- 화면 그리기 ----
        if game_state == GAME_STATE_MENU:
            draw_menu(screen)
        else:
            # PLAYING / ESC_MENU / GAME_OVER 모두 게임 화면 위에 덧씌우는 구조
            draw_game(screen)
            if game_state == GAME_STATE_ESC_MENU:
                draw_esc_menu(screen)
            elif game_state == GAME_STATE_GAME_OVER:
                draw_game_over(screen)

        pygame.display.flip()
        clock.tick(FPS)


# 프로그램 시작점
if __name__ == "__main__":
    main()
