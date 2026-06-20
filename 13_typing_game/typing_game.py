# typing_game.py
# 한컴타자연습 스타일의 파이썬 타자 연습 게임
# 실행 방법: python typing_game.py

import pygame   # 게임을 만들기 위한 라이브러리
import random   # 단어나 좌표를 랜덤으로 뽑기 위해 사용
import sys      # 프로그램을 깔끔하게 종료할 때 사용


# =====================================================
# 1. 게임 전체에서 사용할 설정값 (상수)
# =====================================================

# --- 화면 크기 ---
WIDTH = 800     # 화면 가로 픽셀
HEIGHT = 600    # 화면 세로 픽셀
FPS = 60        # 1초에 화면을 60번 새로 그린다 (부드럽게 보이도록)

# --- 색깔 (RGB: 빨강, 초록, 파랑 0~255) ---
BG_COLOR = (245, 245, 235)        # 배경색 - 연한 베이지
WORD_COLOR = (40, 40, 40)         # 떨어지는 단어색 - 어두운 회색
INPUT_BG = (255, 255, 255)        # 입력창 배경 - 흰색
INPUT_TEXT_COLOR = (0, 0, 0)      # 입력창 글자 - 검정
BORDER_COLOR = (120, 120, 120)    # 테두리 - 회색
INFO_COLOR = (60, 80, 140)        # 점수/레벨 정보 - 짙은 파랑
TITLE_COLOR = (40, 60, 120)       # 제목 - 남색
GAMEOVER_COLOR = (200, 40, 40)    # GAME OVER 글자 - 빨강
BUTTON_COLOR = (220, 230, 250)    # 언어 선택 버튼 - 연한 파랑
BUTTON_BORDER = (80, 100, 180)    # 버튼 테두리 - 진한 파랑

# --- 입력창 위치 및 크기 ---
INPUT_HEIGHT = 50                       # 입력창 높이
INPUT_Y = HEIGHT - INPUT_HEIGHT - 10    # 입력창 y좌표 (맨 아래에서 10px 위)
INPUT_X = 10                            # 입력창 x좌표
INPUT_WIDTH = WIDTH - 20                # 입력창 너비

# --- 게임 오버 판정선 (이 y좌표에 단어가 닿으면 끝) ---
GAMEOVER_LINE_Y = INPUT_Y               # 입력창 바로 위

# --- 단어 리스트 ---
# 영어 단어 리스트
ENGLISH_WORDS = ["apple", "banana", "python", "code", "data",
                 "school", "game", "keyboard", "mouse", "window",
                 "screen", "music", "river", "cloud", "book"]

# 한국어 단어 리스트
KOREAN_WORDS = ["사과", "학교", "파이썬", "게임", "데이터",
                "키보드", "마우스", "화면", "음악", "구름",
                "책상", "연습", "공부", "바다", "강아지"]

# --- 난이도 관련 설정 ---
INITIAL_SPEED = 1.0       # 시작 낙하 속도 (1프레임마다 1픽셀 내려옴)
SPEED_STEP = 0.5          # 레벨 올라갈 때마다 증가하는 속도
MAX_SPEED = 6.0           # 최대 속도 제한 (너무 빨라지지 않게)

INITIAL_SPAWN_MS = 2000   # 시작 생성 간격 (2000ms = 2초)
MIN_SPAWN_MS = 800        # 최소 생성 간격 (0.8초보다는 빨라지지 않음)
SPAWN_STEP_MS = 100       # 레벨업마다 줄어드는 생성 간격 (0.1초씩)

# --- 레벨업 시간 간격 (초 단위) ---
# 1분 → 40초 → 이후 계속 30초
LEVEL_UP_SCHEDULE = [60, 40, 30]


# =====================================================
# 2. 게임 상태를 저장하는 전역 변수
# =====================================================
# 떨어지고 있는 단어들. 각 항목은 {"text": 단어, "x": x좌표, "y": y좌표}
words_on_screen = []

user_input = ""                       # 사용자가 현재 입력창에 친 글자
score = 0                             # 점수
level = 1                             # 현재 레벨
current_speed = INITIAL_SPEED         # 현재 단어 낙하 속도
current_spawn_ms = INITIAL_SPAWN_MS   # 현재 단어 생성 간격
last_spawn_time = 0                   # 마지막으로 단어를 만든 시각(ms)
game_start_time = 0                   # 게임이 시작된 시각(ms)
last_level_up_time = 0                # 마지막으로 레벨업한 시각(ms)
level_up_index = 0                    # 레벨업 스케줄에서 몇 번째 간격을 쓰는지
game_over = False                     # 게임 오버 여부
selected_language = None              # 선택한 언어 ("english" 또는 "korean")
word_list = []                        # 실제 게임에서 사용할 단어 리스트

# --- 폰트 (main 함수에서 초기화) ---
font_word = None        # 떨어지는 단어용 폰트
font_input = None       # 입력창 글자용 폰트
font_info = None        # 점수/레벨 정보 폰트
font_title = None       # 제목용 폰트
font_gameover = None    # GAME OVER용 큰 폰트


# =====================================================
# 3. 한글 폰트 가져오기
# =====================================================
def get_font(size):
    """한글을 표시할 수 있는 폰트를 찾아서 돌려주는 함수."""
    # 운영체제별로 설치돼 있을 법한 한글 폰트 이름 목록
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
    # 현재 시스템에 설치된 폰트 이름 목록 가져오기
    available = pygame.font.get_fonts()
    # 후보 중에 설치돼 있는 첫 번째 한글 폰트 사용
    for name in korean_font_candidates:
        if name in available:
            return pygame.font.SysFont(name, size)
    # 한글 폰트가 아예 없으면 기본 폰트 사용 (한글이 네모로 보일 수 있음)
    return pygame.font.SysFont(None, size)


# =====================================================
# 4. 게임 초기화
# =====================================================
def init_game():
    """게임 상태를 처음 상태로 되돌리는 함수 (새 게임 시작 시)."""
    # 아래 변수들은 전역 변수를 바꾸겠다고 선언
    global words_on_screen, user_input, score, level
    global current_speed, current_spawn_ms
    global last_spawn_time, game_start_time, last_level_up_time, level_up_index
    global game_over

    words_on_screen = []                   # 떨어지는 단어 목록 비우기
    user_input = ""                        # 입력창 비우기
    score = 0                              # 점수 0
    level = 1                              # 레벨 1부터 시작
    current_speed = INITIAL_SPEED          # 속도 초기값
    current_spawn_ms = INITIAL_SPAWN_MS    # 생성 간격 초기값

    now = pygame.time.get_ticks()          # 현재 시각(ms)
    last_spawn_time = now                  # 마지막 생성 시각 = 지금
    game_start_time = now                  # 게임 시작 시각 = 지금
    last_level_up_time = now               # 마지막 레벨업 시각 = 지금
    level_up_index = 0                     # 첫 번째 간격(120초)부터 시작
    game_over = False                      # 아직 게임 오버 아님


# =====================================================
# 5. 언어 선택 화면
# =====================================================
def select_language_screen(screen, clock):
    """언어 선택 화면. 1 키 누르면 영어, 2 키 누르면 한국어를 리턴."""
    # 사용자가 선택할 때까지 무한 반복
    while True:
        # 이벤트(키 입력, 창 닫기 등) 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # 창의 X 버튼을 눌렀을 때
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                # 키를 눌렀을 때
                if event.key == pygame.K_1:
                    # 1 키: 영어 선택
                    return "english"
                elif event.key == pygame.K_2:
                    # 2 키: 한국어 선택
                    return "korean"
                elif event.key == pygame.K_ESCAPE:
                    # ESC 키: 프로그램 종료
                    pygame.quit()
                    sys.exit()

        # --- 화면 그리기 ---
        screen.fill(BG_COLOR)  # 배경 칠하기

        # 제목 그리기
        title_surface = font_title.render("Typing Game / 타자 연습", True, TITLE_COLOR)
        title_rect = title_surface.get_rect(center=(WIDTH // 2, 120))
        screen.blit(title_surface, title_rect)

        # 안내 문구
        guide = font_info.render("언어를 선택하세요 / Select Language", True, INFO_COLOR)
        guide_rect = guide.get_rect(center=(WIDTH // 2, 200))
        screen.blit(guide, guide_rect)

        # --- 버튼 1: English ---
        btn1_rect = pygame.Rect(WIDTH // 2 - 150, 280, 300, 70)  # 버튼 사각형 영역
        pygame.draw.rect(screen, BUTTON_COLOR, btn1_rect, border_radius=10)       # 배경
        pygame.draw.rect(screen, BUTTON_BORDER, btn1_rect, 3, border_radius=10)   # 테두리
        btn1_text = font_info.render("[ 1 ]  English", True, TITLE_COLOR)         # 글자
        screen.blit(btn1_text, btn1_text.get_rect(center=btn1_rect.center))       # 가운데 표시

        # --- 버튼 2: 한국어 ---
        btn2_rect = pygame.Rect(WIDTH // 2 - 150, 370, 300, 70)
        pygame.draw.rect(screen, BUTTON_COLOR, btn2_rect, border_radius=10)
        pygame.draw.rect(screen, BUTTON_BORDER, btn2_rect, 3, border_radius=10)
        btn2_text = font_info.render("[ 2 ]  한국어", True, TITLE_COLOR)
        screen.blit(btn2_text, btn2_text.get_rect(center=btn2_rect.center))

        # 하단 안내 (ESC 종료)
        info = font_info.render("ESC: 종료 / Quit", True, (120, 120, 120))
        info_rect = info.get_rect(center=(WIDTH // 2, 520))
        screen.blit(info, info_rect)

        pygame.display.flip()  # 화면 업데이트
        clock.tick(FPS)        # 프레임 속도 유지


# =====================================================
# 6. 새 단어 생성
# =====================================================
def create_word():
    """단어 리스트에서 랜덤으로 하나 골라 화면 맨 위에 생성."""
    # 현재 언어 리스트에서 랜덤으로 하나 선택
    text = random.choice(word_list)
    # 단어를 폰트로 렌더링해서 가로 너비를 구함 (화면 밖으로 안 나가게 하기 위해)
    word_surface = font_word.render(text, True, WORD_COLOR)
    word_width = word_surface.get_width()
    # x좌표는 0 ~ (WIDTH - word_width) 범위에서 랜덤
    x = random.randint(0, WIDTH - word_width)
    # y좌표는 맨 위 (0)
    y = 0
    # 단어 정보를 딕셔너리로 만들어 화면 단어 목록에 추가
    words_on_screen.append({"text": text, "x": x, "y": y})


# =====================================================
# 7. 단어 위치 업데이트 (아래로 이동)
# =====================================================
def update_words():
    """모든 단어를 속도만큼 아래로 이동. 바닥에 닿으면 게임 오버."""
    global game_over
    # 모든 단어를 반복하면서 y좌표를 속도만큼 증가
    for word in words_on_screen:
        word["y"] += current_speed
        # 단어가 게임 오버 라인(입력창 위)에 닿으면 게임 오버
        if word["y"] >= GAMEOVER_LINE_Y:
            game_over = True


# =====================================================
# 8. 입력 단어 검사
# =====================================================
def check_input():
    """Enter 눌렀을 때, 입력값과 같은 단어가 화면에 있으면 삭제."""
    global user_input, score
    # 앞뒤 공백 제거
    typed = user_input.strip()
    # 빈 문자열이면 입력창만 비우고 리턴
    if typed == "":
        user_input = ""
        return
    # 같은 단어 중 가장 아래에 있는 것을 찾는다
    matched_index = -1   # 일치한 단어의 인덱스 (없으면 -1)
    max_y = -1           # 지금까지 찾은 가장 큰(=아래쪽) y값
    # 화면의 모든 단어를 하나씩 확인
    for i, word in enumerate(words_on_screen):
        # 단어 내용이 입력값과 완전히 일치하고, y좌표가 지금까지 중 가장 크면
        if word["text"] == typed and word["y"] > max_y:
            max_y = word["y"]
            matched_index = i
    # 일치하는 단어가 있었으면 삭제 + 점수 추가
    if matched_index >= 0:
        words_on_screen.pop(matched_index)   # 해당 단어 삭제
        score += 10                          # 점수 10점 추가
    # 일치하든 안 하든 입력창은 비우기
    user_input = ""


# =====================================================
# 9. 난이도 조정
# =====================================================
def update_difficulty():
    """시간이 흐르면 속도와 생성 간격을 조절 (레벨업)."""
    global current_speed, current_spawn_ms, level
    global last_level_up_time, level_up_index
    # 현재 시각
    now = pygame.time.get_ticks()
    # 마지막 레벨업 이후 흐른 시간(ms)
    elapsed_since_levelup = now - last_level_up_time
    # 이번 레벨업까지 걸리는 시간(초)을 스케줄에서 가져옴
    if level_up_index < len(LEVEL_UP_SCHEDULE):
        interval_seconds = LEVEL_UP_SCHEDULE[level_up_index]
    else:
        # 스케줄을 다 쓴 뒤에는 계속 30초마다
        interval_seconds = 30
    # 그만큼 시간이 지났으면 레벨업 실행
    if elapsed_since_levelup >= interval_seconds * 1000:
        level += 1                                            # 레벨 +1
        current_speed = min(current_speed + SPEED_STEP, MAX_SPEED)         # 속도 증가 (최대 제한)
        current_spawn_ms = max(current_spawn_ms - SPAWN_STEP_MS, MIN_SPAWN_MS)  # 생성 간격 감소 (최소 제한)
        last_level_up_time = now                              # 시각 갱신
        # 다음 스케줄로 이동 (마지막이면 그대로 유지 → 계속 30초)
        if level_up_index < len(LEVEL_UP_SCHEDULE) - 1:
            level_up_index += 1


# =====================================================
# 10. 게임 화면 그리기
# =====================================================
def draw_screen(screen):
    """게임 진행 중 화면 전체 그리기."""
    # 배경 채우기
    screen.fill(BG_COLOR)

    # 떨어지는 단어들 그리기
    for word in words_on_screen:
        surface = font_word.render(word["text"], True, WORD_COLOR)
        screen.blit(surface, (word["x"], word["y"]))

    # 상단 정보 (점수, 레벨, 경과 시간)
    elapsed_sec = (pygame.time.get_ticks() - game_start_time) // 1000   # 경과 초
    minutes = elapsed_sec // 60                                          # 분
    seconds = elapsed_sec % 60                                           # 초
    info_text = f"Score: {score}    Level: {level}    Time: {minutes:02d}:{seconds:02d}"
    info_surface = font_info.render(info_text, True, INFO_COLOR)
    screen.blit(info_surface, (10, 10))

    # 게임 오버 라인 (시각적 표시)
    pygame.draw.line(screen, BORDER_COLOR,
                     (0, GAMEOVER_LINE_Y), (WIDTH, GAMEOVER_LINE_Y), 1)

    # 입력창 배경 (흰색)
    pygame.draw.rect(screen, INPUT_BG,
                     (INPUT_X, INPUT_Y, INPUT_WIDTH, INPUT_HEIGHT))
    # 입력창 테두리
    pygame.draw.rect(screen, BORDER_COLOR,
                     (INPUT_X, INPUT_Y, INPUT_WIDTH, INPUT_HEIGHT), 3)
    # 입력창에 현재 입력 중인 글자 표시
    input_surface = font_input.render(user_input, True, INPUT_TEXT_COLOR)
    screen.blit(input_surface, (INPUT_X + 10, INPUT_Y + 10))


# =====================================================
# 11. 게임 오버 화면 그리기
# =====================================================
def draw_game_over(screen):
    """GAME OVER 화면을 게임 화면 위에 덧씌우기."""
    # 반투명한 흰색 레이어를 얹어서 배경을 흐리게
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)               # 0~255 (투명도)
    overlay.fill((255, 255, 255))        # 흰색
    screen.blit(overlay, (0, 0))

    # GAME OVER 큰 글자
    go_surface = font_gameover.render("GAME OVER", True, GAMEOVER_COLOR)
    go_rect = go_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 70))
    screen.blit(go_surface, go_rect)

    # 최종 점수
    score_text = f"최종 점수 / Final Score: {score}"
    score_surface = font_info.render(score_text, True, TITLE_COLOR)
    score_rect = score_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10))
    screen.blit(score_surface, score_rect)

    # 재시작/종료 안내
    restart_text = "R: 재시작 (언어 선택으로)      ESC: 종료"
    restart_surface = font_info.render(restart_text, True, INFO_COLOR)
    restart_rect = restart_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70))
    screen.blit(restart_surface, restart_rect)


# =====================================================
# 12. 메인 루프
# =====================================================
def main():
    """게임 전체 실행. 언어 선택 → 게임 진행 → 게임 오버 → R로 다시 언어 선택."""
    # 전역 변수 사용 선언
    global user_input, last_spawn_time
    global selected_language, word_list
    global font_word, font_input, font_info, font_title, font_gameover

    pygame.init()                                        # pygame 시스템 초기화
    pygame.key.start_text_input()                        # 텍스트 입력 모드 켜기 (IME/한글 지원)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))    # 창 만들기
    pygame.display.set_caption("Typing Game - 타자 연습") # 창 제목
    clock = pygame.time.Clock()                          # FPS 제어용 시계

    # 폰트 준비 (한글 지원 폰트)
    font_word = get_font(32)        # 떨어지는 단어
    font_input = get_font(28)       # 입력창
    font_info = get_font(24)        # 점수/레벨 정보
    font_title = get_font(48)       # 제목
    font_gameover = get_font(72)    # GAME OVER

    # 바깥 루프: 언어 선택 → 게임 → 게임 오버 → R로 다시 처음으로
    while True:
        # --- 1) 언어 선택 화면 ---
        selected_language = select_language_screen(screen, clock)
        # 선택한 언어에 맞는 단어 리스트 지정
        if selected_language == "english":
            word_list = ENGLISH_WORDS
        else:
            word_list = KOREAN_WORDS

        # --- 2) 게임 초기화 ---
        init_game()

        # --- 3) 게임 플레이 루프 ---
        restart_requested = False   # R이 눌렸는지 확인하는 플래그
        while not restart_requested:
            # 이벤트 처리
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # 창의 X 버튼을 눌렀을 때
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    # 키를 눌렀을 때
                    if game_over:
                        # 게임 오버 상태에서는 R, ESC만 처리
                        if event.key == pygame.K_r:
                            restart_requested = True   # 재시작 요청
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit()
                            sys.exit()
                    else:
                        # 게임 중일 때
                        if event.key == pygame.K_RETURN:
                            # Enter: 입력 단어 검사
                            check_input()
                        elif event.key == pygame.K_BACKSPACE:
                            # Backspace: 마지막 글자 지우기
                            user_input = user_input[:-1]
                        elif event.key == pygame.K_ESCAPE:
                            # ESC: 종료
                            pygame.quit()
                            sys.exit()
                elif event.type == pygame.TEXTINPUT:
                    # 텍스트 입력 이벤트 (한글 조합 완성, 영문 타자 등)
                    if not game_over:
                        # \n, \r 같은 특수문자는 걸러내고 일반 글자만 추가
                        if event.text.isprintable():
                            user_input += event.text

            # 게임 진행 중이면 로직 업데이트
            if not game_over:
                now = pygame.time.get_ticks()
                # 마지막 생성 이후 시간이 충분히 지났으면 새 단어 생성
                if now - last_spawn_time >= current_spawn_ms:
                    create_word()
                    last_spawn_time = now
                # 단어들 아래로 이동
                update_words()
                # 난이도 체크 (필요하면 레벨업)
                update_difficulty()

            # 화면 그리기
            draw_screen(screen)
            if game_over:
                # 게임 오버 상태면 오버레이도 그림
                draw_game_over(screen)

            pygame.display.flip()   # 화면에 실제로 반영
            clock.tick(FPS)         # 초당 FPS 프레임 유지


# 프로그램 시작점
if __name__ == "__main__":
    main()
