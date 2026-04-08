'''
작성자: 이유경
최초 작성: 2026.01.07.
최종 수정: 2026.01.11.

갤러리 추가 사항
1. 이미지 이름 출력
2. 이미지 변경(png)
3. 갤러리 배경 넣기
4. 처음, 마지막 사진으로 이동
5. 갤러리 제목 표시
6. 방향 키로 페이지 이동하기(오른쪽: 다음 페이지, 왼쪽: 이전 페이지, 위쪽: 첫 페이지, 아래쪽: 마지막 페이지)
7. 각 사진 장소 설명
'''

from tkinter import *

# 변수 선언 부분
fnameList = []
for i in range(1, 31):    # 추가2. 이미지 변경 시 이미지 파일을 for문을 사용해서 불러옴
    fnameList.append("pic"+str(i)+".png")

fCommentList = []    # 추가7. comment.txt 파일의 내용을 불러와서 각 사진 장소 설명 추가
comment = open("comment.txt", "r", encoding = "utf-8")
for j in comment:
    fCommentList.append(j.strip())
comment.close()

num=0

# 함수 선언 부분
def updatePage():           # 함수의 중복되는 부분을 또 다른 함수로 만들기
    photo=PhotoImage(file="png/"+fnameList[num])
    pLabel.configure(image=photo)
    pLabel.image=photo
    pLabelName.configure(text="< "+fnameList[num]+" >")    # 추가1. 사진이 바뀌면 이름도 바뀜
    pPoint.configure(text=fCommentList[num])    # 추가7. 사진이 바뀌면 설명도 바뀜

def clickPrev():
    global num
    num -= 1
    if num < 0:
        num=29
    updatePage()

def clickNext():
    global num
    num += 1
    if num > 29:
        num=0
    updatePage()

def pagePrev(event):    # 추가6. 오른쪽 방향키로 다음 페이지 이동
    clickNext()

def pageNext(event):    # 추가6. 왼쪽 방향키로 이전 페이지 이동
    clickPrev()

def goStart():    # 추가4. 처음으로 이동하는 함수
    global num
    num = 0
    updatePage()

def goEnd():    # 추가4. 마지막으로 이동하는 함수
    global num
    num = 29
    updatePage()

def pageStart(event):    # 추가6. 위쪽 방향키로 첫 페이지 이동
    goStart()

def pageEnd(event):    # 추가6. 아래쪽 방향키로 마지막 페이지 이동
    goEnd()

# 메인 코드 부분
window = Tk()
window.geometry("1090x750")
window.title("Photo Gallery")
window.configure(bg="#E8E1D9")    # 추가3. 갤러리 배경 넣기

# 버튼 위젯 생성
btnPrev=Button(window, text="◀", bg="#E8E1D9", command=clickPrev)
btnNext=Button(window, text="▶", bg="#E8E1D9", command=clickNext)
btnStart=Button(window, text="◀◀", bg="#E8E1D9", command=goStart)    # 추가4. 처음으로 이동
btnEnd=Button(window, text="▶▶", bg="#E8E1D9", command=goEnd)    # 추가4. 마지막으로 이동

# 추가1. 라벨 위젯으로 사진 파일 이름 생성
pLabelName=Label(window, text="< "+fnameList[0]+" >", font=("Calibri", 13), bg="#E8E1D9")

# 추가5. 갤러리 제목 생성
galleryName=Label(window, text="TRAVEL ARCHIVE", font=("Calibri", 35, "bold"), fg="#111827", bg="#E8E1D9")

# 추가7. 각 사진 장소 설명 생성
pPoint=Label(window, text=fCommentList[0], font=("Calibri", 13), bg="#E8E1D9")

# 라벨 위젯으로 이미지 생성
photo=PhotoImage(file="png/"+fnameList[0])
pLabel=Label(window, image=photo)
pLabel.configure(bg="white")    # 이미지 배경을 흰색으로 설정해서 테두리처럼 보이게 함

# 위젯 디스플레이
btnPrev.place(x=150, y=700)
btnNext.place(x=900, y=700)
btnStart.place(x=50, y=700)
btnEnd.place(x=1000, y=700)
pLabel.place(x=30, y=100)
pLabelName.place(x=350, y=700)    # 추가1. 사진 파일 이름
galleryName.place(x=30, y=30)    # 추가5. 갤러리 제목
pPoint.place(x=470, y=700)    # 추가7. 사진 장소

# 추가6. 방향키로 페이지 이동
window.bind("<Right>", pagePrev)
window.bind("<Left>", pageNext)
window.bind("<Up>", pageStart)
window.bind("<Down>", pageEnd)

window.mainloop()
