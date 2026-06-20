# typing_game_v2.py
# 한컴타자연습 스타일의 파이썬 타자 연습 게임 (개선 버전)
# 실행 방법: python typing_game_v2.py
#
# [이번 버전에서 개선된 점]
#  1. 입력창에 깜빡이는 커서가 생김
#  2. 한국어 조합 중인 글자도 실시간으로 보임 (예: ㅍ → 파 → 파ㅇ → 파이)
#  3. CSV 파일(words.csv)로 단어 목록을 바꿀 수 있음

import pygame   # 게임을 만들기 위한 라이브러리
import random   # 단어나 좌표를 랜덤으로 뽑기 위해 사용
import sys      # 프로그램을 깔끔하게 종료할 때 사용
import csv      # CSV 파일을 읽기 위한 표준 라이브러리
import os       # 파일이 있는지 확인하기 위해 사용


# =====================================================
# 1. 게임 전체에서 사용할 설정값 (상수)
# =====================================================

# --- 화면 크기 ---
WIDTH = 800     # 화면 가로 픽셀
HEIGHT = 600    # 화면 세로 픽셀
FPS = 60        # 1초에 화면을 60번 새로 그린다

# --- 색깔 (RGB: 빨강, 초록, 파랑 0~255) ---
BG_COLOR = (245, 245, 235)        # 배경색 - 연한 베이지
WORD_COLOR = (40, 40, 40)         # 떨어지는 단어색 - 어두운 회색
INPUT_BG = (255, 255, 255)        # 입력창 배경 - 흰색
INPUT_TEXT_COLOR = (0, 0, 0)      # 확정된 입력 글자 - 검정
COMPOSING_COLOR = (100, 100, 200) # 조합 중인 글자 - 파란 회색 (시각적 구분용)
CURSOR_COLOR = (0, 0, 0)          # 커서 색 - 검정
BORDER_COLOR = (120, 120, 120)    # 테두리 - 회색
INFO_COLOR = (60, 80, 140)        # 점수/레벨 정보 - 짙은 파랑
TITLE_COLOR = (40, 60, 120)       # 제목 - 남색
GAMEOVER_COLOR = (200, 40, 40)    # GAME OVER 글자 - 빨강
BUTTON_COLOR = (220, 230, 250)    # 언어 선택 버튼 - 연한 파랑
BUTTON_BORDER = (80, 100, 180)    # 버튼 테두리 - 진한 파랑

# --- 입력창 위치 및 크기 ---
INPUT_HEIGHT = 50                       # 입력창 높이
INPUT_Y = HEIGHT - INPUT_HEIGHT - 10    # 입력창 y좌표
INPUT_X = 10                            # 입력창 x좌표
INPUT_WIDTH = WIDTH - 20                # 입력창 너비
INPUT_PADDING = 10                      # 입력창 안쪽 여백
GAMEOVER_LINE_Y = INPUT_Y               # 이 선에 단어가 닿으면 게임 오버

# --- 커서 관련 설정 ---
CURSOR_BLINK_MS = 500    # 0.5초(500ms)마다 보였다 사라졌다 반복
CURSOR_WIDTH = 2         # 커서 두께 (픽셀)

# --- 기본 단어 리스트 (CSV 파일을 못 읽을 때 쓰는 백업용) ---
DEFAULT_ENGLISH_WORDS = ["apple", "banana", "python", "code", "data",
                         "school", "game", "keyboard", "mouse", "window",
                         "screen", "music", "river", "cloud", "book"]

DEFAULT_KOREAN_WORDS = ["사과", "학교", "파이썬", "게임", "데이터",
                        "키보드", "마우스", "화면", "음악", "구름",
                        "책상", "연습", "공부", "바다", "강아지"]

# --- CSV 파일 경로 ---
CSV_FILENAME = "words.csv"

# --- 난이도 관련 설정 ---
INITIAL_SPEED = 1.0       # 시작 낙하 속도
SPEED_STEP = 0.5          # 레벨 올라갈 때 증가하는 속도
MAX_SPEED = 6.0           # 최대 속도 제한

INITIAL_SPAWN_MS = 2000   # 시작 생성 간격 (2초)
MIN_SPAWN_MS = 800        # 최소 생성 간격 (0.8초)
SPAWN_STEP_MS = 100       # 레벨업마다 줄어드는 생성 간격

# --- 레벨업 시간 간격 (초 단위) ---
LEVEL_UP_SCHEDULE = [30, 20, 15]


# =====================================================
# 2. 게임 상태를 저장하는 전역 변수
# =====================================================
words_on_screen = []          # 떨어지는 단어들 (딕셔너리 목록)

# 입력창 관련 변수 (새로 분리됨!)
input_text = ""               # 확정된(입력이 끝난) 글자. 예: "파이"
composition_text = ""         # 조합 중인(아직 확정 안 된) 글자. 예: "ㅆ"

score = 0                             # 점수
level = 1                             # 현재 레벨
current_speed = INITIAL_SPEED         # 현재 낙하 속도
current_spawn_ms = INITIAL_SPAWN_MS   # 현재 단어 생성 간격
last_spawn_time = 0                   # 마지막 단어 생성 시각(ms)
game_start_time = 0                   # 게임 시작 시각(ms)
last_level_up_time = 0                # 마지막 레벨업 시각(ms)
level_up_index = 0                    # 레벨업 스케줄 인덱스
game_over = False                     # 게임 오버 여부
selected_language = None              # "english" 또는 "korean"
word_list = []                        # 현재 사용 중인 단어 리스트

# --- 폰트 (main에서 초기화됨) ---
font_word = None
font_input = None
font_info = None
font_title = None
font_gameover = None


# =====================================================
# 3. 한글 폰트 가져오기
# =====================================================
def get_font(size):
    """한글을 표시할 수 있는 폰트를 찾아 돌려주는 함수."""
    # 운영체제별로 설치돼 있을 법한 한글 폰트 후보
    korean_font_candidates = [
        'malgungothic',     # 윈도우 - 맑은 고딕
        'applegothic',      # 맥 - 애플고딕
        'applesdgothicneo', # 맥 - Apple SD Gothic Neo
        'nanumgothic',      # 리눅스 - 나눔고딕
        'notosanscjkkr',    # 구글 노토 산스
        'gulim',            # 윈도우 - 굴림
        'dotum',            # 윈도우 - 돋움
        'batang',           # 윈도우 - 바탕
    ]
    available = pygame.font.get_fonts()   # 설치된 폰트 목록
    # 후보 중 있는 것부터 사용
    for name in korean_font_candidates:
        if name in available:
            return pygame.font.SysFont(name, size)
    # 한글 폰트가 전혀 없으면 기본 폰트 (한글이 네모로 보일 수 있음)
    return pygame.font.SysFont(None, size)


# =====================================================
# 4. CSV에서 단어 목록 불러오기
# =====================================================
def load_words_from_csv(filename):
    """
    CSV 파일에서 단어들을 읽어와 영어/한국어 두 리스트로 나눠서 돌려준다.
    성공하면 (영어 단어들, 한국어 단어들, True) 튜플을 돌려주고,
    실패하면 (기본 영어 단어들, 기본 한국어 단어들, False)를 돌려준다.

    CSV 예시:
        language,word,difficulty,category
        en,apple,1,common
        ko,사과,1,일상
    """
    # 파일이 존재하지 않으면 바로 기본 목록 사용
    if not os.path.exists(filename):
        print(f"[알림] '{filename}' 파일이 없어서 기본 단어 리스트를 사용합니다.")
        return DEFAULT_ENGLISH_WORDS.copy(), DEFAULT_KOREAN_WORDS.copy(), False

    english_words = []   # 영어 단어를 넣을 빈 리스트
    korean_words = []    # 한국어 단어를 넣을 빈 리스트

    try:
        # 'utf-8-sig'는 엑셀에서 저장한 CSV의 BOM 문자도 자동으로 처리해줌
        with open(filename, mode="r", encoding="utf-8-sig", newline="") as f:
            # csv.DictReader: 첫 번째 줄을 헤더(열 이름)로 인식하고
            # 각 행을 딕셔너리로 만들어줌. 예: {"language": "en", "word": "apple", ...}
            reader = csv.DictReader(f)
            # 한 줄씩 반복
            for row in reader:
                # .get()은 키가 없거나 값이 None이면 빈 문자열을 돌려줌 (안전장치)
                language = (row.get("language") or "").strip().lower()  # 소문자로 통일
                word = (row.get("word") or "").strip()                  # 앞뒤 공백 제거
                # 단어가 비어있으면 건너뜀
                if not word:
                    continue
                # 언어에 따라 올바른 리스트에 추가
                if language == "en":
                    english_words.append(word)
                elif language == "ko":
                    korean_words.append(word)
                # 그 외 언어는 무시 (필요하면 나중에 추가 가능)

        # 만약 파일은 읽었는데 단어가 하나도 없으면 기본 리스트로 폴백
        if not english_words and not korean_words:
            print(f"[알림] '{filename}'에 유효한 단어가 없어서 기본 리스트를 씁니다.")
            return DEFAULT_ENGLISH_WORDS.copy(), DEFAULT_KOREAN_WORDS.copy(), False

        # 한쪽 언어만 비어 있으면 그 쪽만 기본 리스트로 채움
        if not english_words:
            english_words = DEFAULT_ENGLISH_WORDS.copy()
        if not korean_words:
            korean_words = DEFAULT_KOREAN_WORDS.copy()

        print(f"[OK] CSV에서 영어 {len(english_words)}개, 한국어 {len(korean_words)}개 로드")
        return english_words, korean_words, True

    except Exception as e:
        # 파일이 손상됐거나 형식이 잘못됐을 때의 예외 처리
        print(f"[오류] CSV 읽기 실패 ({e}). 기본 단어 리스트를 사용합니다.")
        return DEFAULT_ENGLISH_WORDS.copy(), DEFAULT_KOREAN_WORDS.copy(), False


# =====================================================
# 5. 게임 초기화
# =====================================================
def init_game():
    """새 게임을 시작할 때 상태를 초기값으로 되돌림."""
    global words_on_screen, input_text, composition_text, score, level
    global current_speed, current_spawn_ms
    global last_spawn_time, game_start_time, last_level_up_time, level_up_index
    global game_over

    words_on_screen = []                   # 떨어지는 단어 비우기
    input_text = ""                        # 확정 입력값 비우기
    composition_text = ""                  # 조합 입력값 비우기
    score = 0                              # 점수 리셋
    level = 1                              # 레벨 리셋
    current_speed = INITIAL_SPEED          # 속도 리셋
    current_spawn_ms = INITIAL_SPAWN_MS    # 생성 간격 리셋

    now = pygame.time.get_ticks()          # 현재 시각
    last_spawn_time = now                  # 타이머 리셋
    game_start_time = now
    last_level_up_time = now
    level_up_index = 0
    game_over = False


# =====================================================
# 6. 언어 선택 화면
# =====================================================
def select_language_screen(screen, clock):
    """언어 선택 화면. 1 키: 영어, 2 키: 한국어."""
    # 언어 선택 화면에서는 IME(텍스트 입력)를 꺼둔다.
    # → 숫자 키만 쓰면 되므로 한글 조합 이벤트가 필요 없음.
    pygame.key.stop_text_input()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "english"   # 1 → 영어
                elif event.key == pygame.K_2:
                    return "korean"    # 2 → 한국어
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # --- 화면 그리기 ---
        screen.fill(BG_COLOR)

        # 제목
        title_surface = font_title.render("Typing Game / 타자 연습", True, TITLE_COLOR)
        screen.blit(title_surface, title_surface.get_rect(center=(WIDTH // 2, 120)))

        # 안내
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

        pygame.display.flip()
        clock.tick(FPS)


# =====================================================
# 7. 새 단어 생성
# =====================================================
def create_word():
    """단어 리스트에서 랜덤으로 하나 골라 화면 맨 위에 생성."""
    text = random.choice(word_list)                          # 랜덤 단어
    word_surface = font_word.render(text, True, WORD_COLOR)  # 폭 계산용 렌더
    word_width = word_surface.get_width()                    # 단어 가로 폭
    x = random.randint(0, WIDTH - word_width)                # 화면 안에 들어오는 x
    y = 0                                                    # 맨 위
    words_on_screen.append({"text": text, "x": x, "y": y})   # 목록에 추가


# =====================================================
# 8. 단어 위치 업데이트
# =====================================================
def update_words():
    """모든 단어를 아래로 이동. 바닥에 닿으면 게임 오버."""
    global game_over
    for word in words_on_screen:
        word["y"] += current_speed                # 아래로 이동
        if word["y"] >= GAMEOVER_LINE_Y:          # 입력창 위 선에 닿으면
            game_over = True                      # 게임 오버!


# =====================================================
# 9. 입력 단어 검사 (Enter 키 눌렀을 때)
# =====================================================
def check_input():
    """확정된 입력값(input_text)과 같은 단어를 화면에서 삭제."""
    global input_text, composition_text, score

    # ⚠️ 핵심: 조합 중인 글자(composition_text)는 비교에 쓰지 않는다!
    # 확정된 input_text만 기준으로 삼는다.
    typed = input_text.strip()
    # 비어있으면 그냥 입력창만 비우고 끝
    if typed == "":
        input_text = ""
        composition_text = ""
        return

    # 같은 단어 중 가장 아래에 있는 것 찾기
    matched_index = -1
    max_y = -1
    for i, word in enumerate(words_on_screen):
        if word["text"] == typed and word["y"] > max_y:
            max_y = word["y"]
            matched_index = i

    # 일치하는 단어가 있으면 삭제하고 점수 +10
    if matched_index >= 0:
        words_on_screen.pop(matched_index)
        score += 10

    # 확정/조합 모두 비우기 (다음 단어를 위해)
    input_text = ""
    composition_text = ""


# =====================================================
# 10. 난이도 조정
# =====================================================
def update_difficulty():
    """시간 흐름에 따라 속도와 생성 간격을 조절."""
    global current_speed, current_spawn_ms, level
    global last_level_up_time, level_up_index

    now = pygame.time.get_ticks()
    elapsed_since_levelup = now - last_level_up_time

    # 다음 레벨업까지 필요한 시간(초) 결정
    if level_up_index < len(LEVEL_UP_SCHEDULE):
        interval_seconds = LEVEL_UP_SCHEDULE[level_up_index]
    else:
        interval_seconds = 30   # 스케줄 소진 후엔 30초 고정

    # 시간이 됐으면 레벨업
    if elapsed_since_levelup >= interval_seconds * 1000:
        level += 1
        current_speed = min(current_speed + SPEED_STEP, MAX_SPEED)
        current_spawn_ms = max(current_spawn_ms - SPAWN_STEP_MS, MIN_SPAWN_MS)
        last_level_up_time = now
        # 다음 스케줄로 이동 (마지막 인덱스면 그대로 유지 → 30초 고정)
        if level_up_index < len(LEVEL_UP_SCHEDULE) - 1:
            level_up_index += 1


# =====================================================
# 11. 커서 표시 여부 계산
# =====================================================
def should_show_cursor():
    """
    지금 커서를 그려야 하는지(True/False) 결정.
    규칙:
      - 게임 중에 입력된 글자(확정+조합)가 있으면 → 항상 보임
      - 입력이 완전히 비어 있으면 → 500ms마다 깜빡임
    """
    # 확정된 글자나 조합 중인 글자가 있으면 항상 표시
    if len(input_text) > 0 or len(composition_text) > 0:
        return True

    # 둘 다 없으면 시간에 따라 깜빡
    # 예) 지금 시각이 1234ms 라면 1234 // 500 = 2 (짝수)
    #     지금 시각이 1800ms 라면 1800 // 500 = 3 (홀수)
    # → 짝수일 때만 보이게 하면 0.5초 간격으로 깜빡깜빡
    now = pygame.time.get_ticks()
    return (now // CURSOR_BLINK_MS) % 2 == 0


# =====================================================
# 12. 게임 화면 그리기
# =====================================================
def draw_screen(screen):
    """게임 진행 중 화면 전체 그리기 (단어들 + 입력창 + 커서)."""
    # 배경
    screen.fill(BG_COLOR)

    # 떨어지는 단어들
    for word in words_on_screen:
        surface = font_word.render(word["text"], True, WORD_COLOR)
        screen.blit(surface, (word["x"], word["y"]))

    # 상단 정보 (점수, 레벨, 경과 시간)
    elapsed_sec = (pygame.time.get_ticks() - game_start_time) // 1000
    minutes = elapsed_sec // 60
    seconds = elapsed_sec % 60
    info_text = f"Score: {score}    Level: {level}    Time: {minutes:02d}:{seconds:02d}"
    info_surface = font_info.render(info_text, True, INFO_COLOR)
    screen.blit(info_surface, (10, 10))

    # 게임 오버 판정선
    pygame.draw.line(screen, BORDER_COLOR,
                     (0, GAMEOVER_LINE_Y), (WIDTH, GAMEOVER_LINE_Y), 1)

    # 입력창 배경과 테두리
    pygame.draw.rect(screen, INPUT_BG,
                     (INPUT_X, INPUT_Y, INPUT_WIDTH, INPUT_HEIGHT))
    pygame.draw.rect(screen, BORDER_COLOR,
                     (INPUT_X, INPUT_Y, INPUT_WIDTH, INPUT_HEIGHT), 3)

    # --- 입력 글자 그리기 ---
    # 시작 좌표 (입력창 안쪽 여백만큼 띄움)
    text_x = INPUT_X + INPUT_PADDING
    text_y = INPUT_Y + INPUT_PADDING

    # (1) 확정된 글자(input_text)를 검정색으로 그림
    if input_text:
        confirmed_surface = font_input.render(input_text, True, INPUT_TEXT_COLOR)
        screen.blit(confirmed_surface, (text_x, text_y))
        # 확정 글자 너비만큼 x를 오른쪽으로 밀기 (다음 글자 위치 계산용)
        confirmed_width = confirmed_surface.get_width()
    else:
        confirmed_width = 0   # 확정 글자가 없으면 너비 0

    # (2) 조합 중인 글자(composition_text)를 구분되는 색으로 그림
    if composition_text:
        composing_surface = font_input.render(composition_text, True, COMPOSING_COLOR)
        screen.blit(composing_surface, (text_x + confirmed_width, text_y))
        # 조합 글자 아래 밑줄을 그어서 "아직 확정 안 됐음"을 시각적으로 알림
        underline_y = text_y + composing_surface.get_height() - 2
        pygame.draw.line(screen, COMPOSING_COLOR,
                         (text_x + confirmed_width, underline_y),
                         (text_x + confirmed_width + composing_surface.get_width(), underline_y),
                         2)
        composing_width = composing_surface.get_width()
    else:
        composing_width = 0

    # (3) 커서 그리기
    # 커서는 (확정글자 + 조합글자) 바로 오른쪽에 나타나야 함
    if should_show_cursor():
        cursor_x = text_x + confirmed_width + composing_width   # 글자 뒤
        cursor_y_top = text_y + 2                               # 살짝 위 여백
        cursor_y_bottom = text_y + font_input.get_height() - 2  # 살짝 아래 여백
        pygame.draw.line(screen, CURSOR_COLOR,
                         (cursor_x, cursor_y_top),
                         (cursor_x, cursor_y_bottom),
                         CURSOR_WIDTH)


# =====================================================
# 13. 게임 오버 화면 그리기
# =====================================================
def draw_game_over(screen):
    """GAME OVER 화면을 기존 화면 위에 덧씌움."""
    # 반투명 흰색 레이어로 배경을 흐리게
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((255, 255, 255))
    screen.blit(overlay, (0, 0))

    # GAME OVER 큰 글자
    go_surface = font_gameover.render("GAME OVER", True, GAMEOVER_COLOR)
    screen.blit(go_surface, go_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 70)))

    # 최종 점수
    score_text = f"최종 점수 / Final Score: {score}"
    score_surface = font_info.render(score_text, True, TITLE_COLOR)
    screen.blit(score_surface, score_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10)))

    # 재시작/종료 안내
    restart_text = "R: 재시작 (언어 선택으로)      ESC: 종료"
    restart_surface = font_info.render(restart_text, True, INFO_COLOR)
    screen.blit(restart_surface, restart_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70)))


# =====================================================
# 14. 메인 루프
# =====================================================
def main():
    """전체 실행: 언어 선택 → 게임 → 게임 오버 → R로 다시 언어 선택."""
    global input_text, composition_text, last_spawn_time
    global selected_language, word_list
    global font_word, font_input, font_info, font_title, font_gameover

    pygame.init()                                          # pygame 시스템 초기화
    screen = pygame.display.set_mode((WIDTH, HEIGHT))      # 창 생성
    pygame.display.set_caption("Typing Game - 타자 연습")  # 창 제목
    clock = pygame.time.Clock()                            # FPS 제어용 시계

    # 폰트 준비
    font_word = get_font(32)
    font_input = get_font(28)
    font_info = get_font(24)
    font_title = get_font(48)
    font_gameover = get_font(72)

    # CSV에서 단어 불러오기 (없으면 기본 리스트 사용)
    english_words, korean_words, csv_loaded = load_words_from_csv(CSV_FILENAME)

    # 입력창 영역을 미리 사각형으로 정의 (IME 위치 설정에 씀)
    input_box_rect = pygame.Rect(INPUT_X, INPUT_Y, INPUT_WIDTH, INPUT_HEIGHT)

    # 바깥 루프: 언어 선택 → 게임 → 게임 오버 → (R) → 다시 언어 선택
    while True:
        # --- 1) 언어 선택 ---
        selected_language = select_language_screen(screen, clock)
        if selected_language == "english":
            word_list = english_words
        else:
            word_list = korean_words

        # --- 2) 게임 초기화 ---
        init_game()

        # --- 3) 텍스트 입력 모드 ON ---
        # 게임 플레이 중에는 IME(한글 입력기)가 작동하도록 텍스트 입력 모드를 켠다.
        pygame.key.start_text_input()
        # IME 후보창(한자/이모지 등)이 뜰 위치를 입력창으로 지정
        pygame.key.set_text_input_rect(input_box_rect)

        # --- 4) 게임 플레이 루프 ---
        restart_requested = False
        while not restart_requested:
            # ----- 이벤트 처리 -----
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                # (A) TEXTINPUT: 확정된 글자가 들어왔을 때
                #    영어 'a', 숫자 '1', 완성된 한글 '파' 등 IME가 확정시킨 글자가 여기로 옴
                elif event.type == pygame.TEXTINPUT:
                    if not game_over:
                        # 확정 글자를 input_text 끝에 붙임
                        input_text += event.text
                        # 글자가 확정됐으니 조합 중 텍스트는 비움
                        composition_text = ""

                # (B) TEXTEDITING: IME가 조합 중인 글자를 알려줄 때
                #    예) 한글 타자 중 'ㅍ', '파', '파ㅇ' 같은 중간 상태
                elif event.type == pygame.TEXTEDITING:
                    if not game_over:
                        # 조합 중 텍스트 저장 (완전히 새로 덮어씀)
                        composition_text = event.text

                # (C) KEYDOWN: 특수키만 처리 (문자 입력은 TEXTINPUT이 담당!)
                elif event.type == pygame.KEYDOWN:
                    if game_over:
                        # 게임 오버 상태에서는 R / ESC만 처리
                        if event.key == pygame.K_r:
                            restart_requested = True
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()
                    else:
                        if event.key == pygame.K_RETURN:
                            # Enter: 입력 단어 검사
                            check_input()
                        elif event.key == pygame.K_BACKSPACE:
                            # Backspace: 확정 입력값에서 마지막 글자만 지움
                            # ⚠️ 주의: 조합 중인 글자가 있을 때의 Backspace는
                            #         IME(운영체제 입력기)가 먼저 처리해서
                            #         "조합 중 글자를 한 자씩 지우기"로 동작하고,
                            #         그땐 KEYDOWN 이벤트가 우리한테 오지 않거나
                            #         조합이 남아있는 상태로 오기 때문에
                            #         여기서는 확정 글자만 건드리면 됨 → 중복 삭제 방지!
                            if composition_text == "":
                                input_text = input_text[:-1]
                            # composition_text가 있으면 아무것도 안 함
                            # (IME가 알아서 조합 글자를 지워줌)
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()

            # ----- 게임 로직 업데이트 -----
            if not game_over:
                now = pygame.time.get_ticks()
                # 단어 생성
                if now - last_spawn_time >= current_spawn_ms:
                    create_word()
                    last_spawn_time = now
                # 단어 이동 및 게임오버 검사
                update_words()
                # 난이도 조정
                update_difficulty()

            # ----- 화면 그리기 -----
            draw_screen(screen)
            if game_over:
                draw_game_over(screen)

            pygame.display.flip()
            clock.tick(FPS)


# 프로그램 시작점
if __name__ == "__main__":
    main()
