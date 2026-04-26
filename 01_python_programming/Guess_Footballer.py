'''
축구 선수 이름 맞히기

작성자: 이유경
최초 작성: 2026.01.11.
최종 수정: 2026.01.12.

-게임 설명-
1. 프로그램을 실행시키면 축구 선수 사진이 뜨고 이름을 입력해서 맞힐 수 있음
2. 사용자가 답을 입력하고 엔터키 또는 제출 버튼을 누름
3. 사용자가 입력한 답과 실제 정답을 비교
4. 정답, 오답을 판별하여 개수 카운트
5. 총 10문제를 풀고 나면 게임이 끝남(전체 DB는 50개 정도)
6. 게임이 끝나고 나면 결과에 따라 안내 메시지가 뜸

-나중에 수정하고 싶은 사항-
1. 디자인 예쁘게
2. 문제 푸는 시간 추가
3. 다른 주제로도 만들어보기(ex; 미술 작품 맞히기, 캐릭터 이름 맞히기, 노래 제목 맞히기 등)
'''

from tkinter import *
from tkinter import messagebox
import random

###################### 변수 선언 부분 ######################
# 사진 파일 불러오기
name_list = []      # 사진을 불러올 때 사용할 리스트
for i in range(1, 51):      # 반복문으로 사진 파일 불러오기
    name_list.append(str(i) + ".png")
#print(name_list)

# 전체 정답 저장 해두기
total_answer_list = []    # 전체 정답을 저장해 놓을 리스트
total_answer = open("player_name.txt", "r", encoding = "utf-8")   # txt 파일 불러오기
for player_name_kor in total_answer:      # total_answer_list에 불러온 txt 파일 추가
    total_answer_list.append(player_name_kor.strip())   # strip()으로 혹시 있을지 모르는 공백 제거
total_answer.close()  # txt 파일 닫기
#print(total_answer_list)
#print(len(total_answer_list))

# 문제 랜덤 뽑기(10문제)
question_list = random.sample(name_list, 10)
#print(question_list)

#  랜덤으로 뽑힌 문제의 정답을 전체 정답 리스트에서 뽑아와서 저장
answer_list = []    # 랜덤 문제의 정답을 저장해 놓을 리스트
for file_name in question_list:     # file_name이라는 변수로 question_list를 확인
    file_number = int(file_name.replace(".png", "")) # file_name의 확장자 부분을 replace() 함수로 없애고 숫자로 변환
    answer = total_answer_list[file_number -1]      # 해당 문제의 정답을 파일 이름(숫자) 인덱스로 접근해서 가져오기
    answer_list.append(answer)  # 가져온 정답을 answer_list에 추가
#    print(file_number)
#print(answer_list)

# answer_list의 인덱스 변수 선언
# answer_list에 저장된 정답을 인덱스로 접근해서 사용자가 입력한 정답과 비교하기 위함
answer_list_index = 0
#print(answer_list[answer_list_index])

# 정답 개수 세기: 정답, 오답 개수
correct_answer = 0
wrong_answer = 0

###################### 함수 선언 부분 ######################
# 사용자에게 답을 입력받고 정답과 비교하는 함수
def check_answer():
    global correct_answer, wrong_answer, answer_list_index
    user_answer = answer_entry.get().strip()    # 입력 받은 답의 비교를 위해 변수에 저장, strip()으로 혹시 있을지 모르는 공백 제거
    
    # 사용자에게 입력 받은 답과 정답을 비교
    if user_answer == answer_list[answer_list_index]:   # 비교해서 같으면
        correct_answer += 1    # 정답 변수 +1
        correct_num.configure(text= f"정답: {correct_answer}개")   # 정답 개수 +1 출력
    else:   # 비교해서 다르면
        wrong_answer += 1    # 오답 변수 +1
        wrong_num.configure(text= f"오답: {wrong_answer}개")     # 오답 개수 +1 출력

    answer_list_index += 1    # 정답 비교가 끝나면 다음 문제 정답으로 업데이트

    # 만약에 10문제를 다 풀었을 경우 게임 종료(finish_game() 함수 실행)
    if answer_list_index == 10:
        finish_game()
        return
    
    # 다음 문제 사진 출력    
    photo = PhotoImage(file = "player_DB/"+question_list[answer_list_index]) # photo에 다음 문제 사진 넣기
    p_label.configure(image = photo)    # 사진 수정
    p_label.image = photo

    answer_entry.delete(0, END)     # 정답 입력칸 비우기

# 엔터키로 사용자의 답을 입력하기
def enter_submit(event):
    check_answer()

# 게임 종료 시 결과 팝업을 띄우는 함수
def finish_game():
    if correct_answer >= 8:     # 정답 개수가 8개 이상일 때
        msg = "축하합니다. 당신은 진정한 축잘알"
    elif correct_answer >= 6:   # 정답 개수가 6개 이상일 때
        msg = "좋아요. 당신은 조금 더 노력하면 조만간 축잘알"
    elif correct_answer >= 4:   # 정답 개수가 4개 이상일 때
        msg = "아쉬워요. 더 잘 할 수 있었을거라 믿었는데..."
    else:   # 그 이하일 때
        msg = "당신을 축알못으로 임명합니다."

    # 맞힌 개수, 결과 메시지를 팝업 창으로 출력
    messagebox.showinfo("게임 결과", f"맞힌 개수: {correct_answer}\n\n{msg}")

###################### 메인 코드 부분 ######################
window = Tk()
window.geometry("1200x700")
window.title("Guess Footballer")
window.configure(bg="white")

# 라벨 위젯으로 게임 제목 출력
game_name = Label(window, text = "축구 선수 이름 맞히기!", font=("한컴고딕", 30, "bold"), bg="white")

# 라벨 위젯으로 메인 사진 출력
photo = PhotoImage(file = "player_DB/"+question_list[answer_list_index])
p_label = Label(window, image = photo, bg="white")

# 라벨 위젯으로 문제 출력
game_question = Label(window, text = "이 선수의 이름은?\n(한글로 입력하세요. 예: 위르겐 클롭)\n(입력 후 엔터 또는 제출 버튼) ", font=("한컴고딕", 18, "bold"), bg="white", justify="left")

# 정답 입력 칸
answer_entry = Entry(window, font=("한컴고딕", 16), bg="white")

# 정답 제출
answer_submit = Button(window, text="제출", font=("한컴고딕", 14), bg="white", command=check_answer)

# 라벨 위젯으로 문제 수 출력
question_num = len(question_list)
total_question = Label(window, text = f"총 {question_num}문제", font=("한컴고딕", 20, "bold"), bg="white")

# 라벨 위젯으로 정답 개수 출력
correct_num = Label(window, text= f"정답: {correct_answer}개", font=("한컴고딕", 20, "bold"), bg="white")

# 라벨 위젯으로 오답 개수 출력
wrong_num = Label(window, text= f"오답: {wrong_answer}개", font=("한컴고딕", 20, "bold"), bg="white")

# 위젯 디스플레이
game_name.place(x=50, y=40)
p_label.place(x=50, y=130)
game_question.place(x=710, y=130)
answer_entry.place(x=710, y=280, width=330, height=35)
answer_entry.focus()    # 커서가 정답 입력 칸에 자동으로 들어감
answer_submit.place(x=1050, y=280)
total_question.place(x=710, y=380)
correct_num.place(x=710, y=480)
wrong_num.place(x=710, y=560)

# 엔터키로 사용자의 답 입력
answer_entry.bind("<Return>", enter_submit)

window.mainloop()
