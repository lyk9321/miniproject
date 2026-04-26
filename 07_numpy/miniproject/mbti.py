# MBTI 설문 조사 데이터 전처리, 판정, 정확도 계산(전체, 각 요소), 회귀분석 모델 생성(전체, 각 요소), 시각화

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import koreanize_matplotlib
import seaborn as sns
from sklearn.linear_model import LogisticRegression as LR
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
from sklearn import tree
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

#################################################################################################################
# 1. 데이터 전처리
#################################################################################################################

# 데이터 불러오기
mbti_data = pd.read_csv('mbti_data.csv')
#print(mbti_data)
#print(mbti_data.info())

# 요소별 질문 컬럼끼리 모아서 DataFrame 만들기
# E/I
df_ei = mbti_data.iloc[:, 6:15]
df_ei.columns = ['e1i7_1', 'e1i7_2', 'e1i7_3', 'e1i7_4', 'e1i7_5', 'e1i7_6', 'e1i7_7', 'e1i7_8', 'e1i7_9']
df_ei['avg_ei'] = df_ei.mean(axis=1)
#print(df_ei.head())

# S/N
df_sn = mbti_data.iloc[:, 15:24]
df_sn.columns = ['s1n7_1', 's1n7_2', 's1n7_3', 's1n7_4', 's1n7_5', 's1n7_6', 's1n7_7', 's1n7_8', 's1n7_9']
df_sn['avg_sn'] = df_sn.mean(axis=1)
#print(df_sn.head())

# T/F
df_tf = mbti_data.iloc[:, 24:33]
df_tf.columns = ['t1f7_1', 't1f7_2', 't1f7_3', 't1f7_4', 't1f7_5', 't1f7_6', 't1f7_7', 't1f7_8', 't1f7_9']
df_tf['avg_tf'] = df_tf.mean(axis=1)
#print(df_tf.head())

# J/P
df_jp = mbti_data.iloc[:, 33:42]
df_jp.columns = ['j1p7_1', 'j1p7_2', 'j1p7_3', 'j1p7_4', 'j1p7_5', 'j1p7_6', 'j1p7_7', 'j1p7_8', 'j1p7_9']
df_jp['avg_jp'] = df_jp.mean(axis=1)
#print(df_jp.head())

# 4가지 지표의 평균값을 모아서 새로운 DataFrame 생성
df_avg = pd.concat([df_ei['avg_ei'], df_sn['avg_sn'], df_tf['avg_tf'], df_jp['avg_jp']], axis=1)
#print(df_avg.head())

#################################################################################################################
# 2. MBTI 판정 (각 지표별로 판정 후 4가지 지표 합치기)
#################################################################################################################

# 각 지표별 평균값으로 MBTI 판정하기 (기준: 4.0)
threshold = 4.0     # 값을 1부터 7까지 선택할 수 있기 때문에 기준은 4.0으로 잡음
predict_ei = np.where(df_avg['avg_ei'] >= threshold, 'I', 'E')  # 값이 4.0 이상이면 I, 미만이면 E
#print(predict_ei)
predict_sn = np.where(df_avg['avg_sn'] >= threshold, 'N', 'S')  # 값이 4.0 이상이면 N, 미만이면 S
#print(predict_sn)
predict_tf = np.where(df_avg['avg_tf'] >= threshold, 'F', 'T')  # 값이 4.0 이상이면 F, 미만이면 T
#print(predict_tf)
predict_jp = np.where(df_avg['avg_jp'] >= threshold, 'P', 'J')  # 값이 4.0 이상이면 P, 미만이면 J
#print(predict_jp)

# 판정을 완료한 각 요소를 합쳐서 하나의 MBTI로 만들기
predict_mbti = predict_ei + predict_sn + predict_tf + predict_jp
#print(predict_mbti)

# 사용자가 실제로 입력한 MBTI를 슬라이싱해서 numpy array로 변환
actual_mbti = mbti_data.iloc[:, 1].to_numpy()

#################################################################################################################
# 3. 정확도 계산 (사용자에게 입력 받은 실제 MBTI와 설문지로 판단한 MBTI 비교)
#################################################################################################################

# '모름/검사 안 해봄' 데이터 제외
valid_value = actual_mbti != '모름/검사 안 해봄'
filtered_predict = predict_mbti[valid_value]    # valid_mask가 Ture인 예측값만 뽑아서 새로운 배열 생성
filtered_user = actual_mbti[valid_value]    # 실제값 중 유효한 값만 뽑아서 새로운 배열 생성
#print(filtered_user)
#print(filtered_predict)

# 예측값과 실제값 비교 (Boolean 배열 생성)
correct_value = (filtered_predict == filtered_user)
#print(correct_value)

# 정확도(%): True는 1, False는 0으로 계산되므로 평균을 구하면 됨
accuracy = np.mean(correct_value) *100
#print(f'정확도: {accuracy:.2f}%')

# 실제값에서 각 요소별 문자 추출
extract_ei = np.array([mbti[0] for mbti in filtered_user])
extract_sn = np.array([mbti[1] for mbti in filtered_user])
extract_tf = np.array([mbti[2] for mbti in filtered_user])
extract_jp = np.array([mbti[3] for mbti in filtered_user])

# 각 요소별 정확도 계산 (예측값 배열도 valid_value로 필터링)
accuracy_ei = np.mean(extract_ei == predict_ei[valid_value]) * 100
accuracy_sn = np.mean(extract_sn == predict_sn[valid_value]) * 100
accuracy_tf = np.mean(extract_tf == predict_tf[valid_value]) * 100
accuracy_jp = np.mean(extract_jp == predict_jp[valid_value]) * 100
#print(f'E/I: {accuracy_ei:.2f}%\nS/N: {accuracy_sn:.2f}%\nT/F: {accuracy_tf:.2f}%\nJ/P: {accuracy_jp:.2f}%')

#################################################################################################################
# 4-1. 회귀분석 모델 생성 (각 요소별 회귀식, MBTI 전체 판정 회귀식)
#################################################################################################################

# 로지스틱 회귀 분석을 이용한 모델링 함수
def mbti_logistic_regression(df_input, target, label, max_iter=100, is_raw=True):
    # 유효한 데이터만 추출
    if is_raw:
        X = df_input.loc[valid_value].iloc[:, :-1]
    else:
        X = df_input
        
    y = target
    
    # 타겟 라벨 인코딩 (문자 -> 숫자)
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    # 학습용/테스트용 데이터 분리 (8:2)
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=10)

    # 로지스틱 회귀 모델 학습
    model = LR(max_iter=max_iter)
    model.fit(X_train, y_train)  # 학습 데이터로만 학습
    
    # 정확도 출력 (테스트 데이터로 평가)
    score = model.score(X_test, y_test)  # 테스트 데이터로 평가
    #print(f'{label} 회귀 모델 정확도: {score * 100:.2f}%')
    
    return model, le, score

# 요소별 회귀식 생성 + 모델 예측값 추출
model_ei, le_ei, score_ei = mbti_logistic_regression(df_ei, extract_ei, 'E/I')
model_sn, le_sn, score_sn = mbti_logistic_regression(df_sn, extract_sn, 'S/N')
model_tf, le_tf, score_tf = mbti_logistic_regression(df_tf, extract_tf, 'T/F')
model_jp, le_jp, score_jp = mbti_logistic_regression(df_jp, extract_jp, 'J/P')

# 4가지 요소를 모두 합쳐서 1개의 MBTI(16가지 유형)를 예측하는 통합 모델
# 전체 질문 데이터 합치기 (각 df에서 avg 컬럼 제외한 질문 컬럼만 추출)
X_total = pd.concat([
    df_ei.loc[valid_value].iloc[:, :-1],
    df_sn.loc[valid_value].iloc[:, :-1],
    df_tf.loc[valid_value].iloc[:, :-1],
    df_jp.loc[valid_value].iloc[:, :-1]
], axis=1)

y_total = filtered_user  # 실제 MBTI

# 전체 MBTI 회귀식 생성: 16가지 유형을 분류해야 하므로 복잡도가 높아 기본 반복 횟수(100)로는 수렴하지 않을 수 있어 1000으로 상향 조정
_, _, score_total = mbti_logistic_regression(X_total, y_total, '전체 MBTI', max_iter=1000, is_raw=False)

# 각 모델로 전체 데이터 예측 후 원래 레이블로 역변환
reg_predict_ei = le_ei.inverse_transform(model_ei.predict(df_ei.loc[valid_value].iloc[:, :-1]))
reg_predict_sn = le_sn.inverse_transform(model_sn.predict(df_sn.loc[valid_value].iloc[:, :-1]))
reg_predict_tf = le_tf.inverse_transform(model_tf.predict(df_tf.loc[valid_value].iloc[:, :-1]))
reg_predict_jp = le_jp.inverse_transform(model_jp.predict(df_jp.loc[valid_value].iloc[:, :-1]))

#################################################################################################################
# 4-2. 랜덤포레스트 모델 생성 (각 요소별 회귀식, MBTI 전체 판정 회귀식)
#################################################################################################################

# 랜덤 포레스트 모델링 함수
def mbti_random_forest(df_input, target, label, le, max_iter=100, is_raw=True):
    # 유효한 데이터만 추출
    if is_raw:
        X = df_input.loc[valid_value].iloc[:, :-1]
    else:
        X = df_input

    y = target

    # 타겟 라벨 인코딩 (문자 -> 숫자)
    y_encoded = le.transform(y)

    # 학습용/테스트용 데이터 분리 (8:2)
    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=10)

    # 랜덤 포레스트 모델 학습 (트리 100개)
    model = RandomForestClassifier(n_estimators=100, random_state=10)
    model.fit(X_train, y_train)

    # 테스트 데이터로 정확도 평가
    score = model.score(X_test, y_test)
    #print(f'{label} 랜덤 포레스트 정확도: {score * 100:.2f}%')

    return model, score

# 요소별 랜덤 포레스트 모델 생성
rf_model_ei, rf_score_ei = mbti_random_forest(df_ei, extract_ei, 'E/I', le_ei)
rf_model_sn, rf_score_sn = mbti_random_forest(df_sn, extract_sn, 'S/N', le_sn)
rf_model_tf, rf_score_tf = mbti_random_forest(df_tf, extract_tf, 'T/F', le_tf)
rf_model_jp, rf_score_jp = mbti_random_forest(df_jp, extract_jp, 'J/P', le_jp)

# 전체 MBTI 랜덤 포레스트 모델 생성
le_total = LabelEncoder()
le_total.fit(y_total)
rf_model_total, rf_score_total = mbti_random_forest(X_total, y_total, '전체 MBTI', le_total, is_raw=False)


#################################################################################################################
# 4-3. (참고) 로지스틱 회귀, SVM, Random Forest 정확도 비교
#################################################################################################################

# 지표별 데이터와 레이블을 리스트로 묶기
indicators = [
    ('E/I', df_ei, extract_ei, le_ei),
    ('S/N', df_sn, extract_sn, le_sn),
    ('T/F', df_tf, extract_tf, le_tf),
    ('J/P', df_jp, extract_jp, le_jp),
]

models = {
    '로지스틱 회귀' : LR(max_iter=1000),    # LogisticRegression: 반복 횟수를 1000으로 늘려 수렴 문제를 줄임
    'SVM'          : SVC(kernel='rbf', probability=True),  # SVM: RBF 커널 사용, probability=True는 predict_proba를 쓰기 위해
    'Random Forest': RandomForestClassifier(n_estimators=100, random_state=10) # 랜덤포레스트: 트리 100개, 재현성 위해 시드 고정
}

# 각 모델별로 결과를 저장할 딕셔너리
results = {name: [] for name in models}

# indicators 리스트를 순회하면서, 지표별(E/I, S/N, ...)로 학습/평가를 수행
for indicator_name, df, extract, le in indicators:  # indicator_name은 'E/I' 같은 이름, df는 해당 지표용 데이터, extract는 정답라벨, le는 인코더
    X = df.loc[valid_value].iloc[:, :-1]
    y = le.transform(extract)   # 정답 라벨(extract)을 레이블 인코더(le)로 숫자(0,1 등)로 변환해서 y로 사용
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=10) # 학습/테스트 데이터 분리, random_state=10: 매번 같은 분할(재현성)
    
    # 같은 지표 데이터에 대해 3개 모델(LR/SVM/RF)을 각각 학습하고 성능을 기록
    for model_name, model in models.items():
        model.fit(X_train, y_train) # 모델 학습(훈련 데이터로 파라미터/트리/경계 등을 맞춤)
        score = model.score(X_test, y_test) * 100   # 기본 score는 accuracy(분류 정확도) -> %로 변환
        results[model_name].append(score)
        #print(f'{model_name} {indicator_name} 정확도: {score:.2f}%')
    #print()  # 지표 구분용 줄바꿈

# 전체 MBTI 추가
for model_name, model in models.items():
    X_train, X_test, y_train, y_test = train_test_split(X_total,    # 전체 특성
                                        LabelEncoder().fit_transform(y_total),  # 전체 타겟을 숫자로 변환(0,1,2,...)
                                        test_size=0.2, random_state=10)
    model.fit(X_train, y_train)     # 전체 데이터 기준으로 모델 학습
    score = model.score(X_test, y_test) * 100   # 전체 데이터 기준 정확도(%) 계산
    results[model_name].append(score)
    #print(f'{model_name} 전체 MBTI 정확도: {score:.2f}%')

# 결과를 표로 출력
index = ['E/I', 'S/N', 'T/F', 'J/P', '전체 MBTI']
df_results = pd.DataFrame(results, index=index)
#print(df_results.round(2))

#################################################################################################################
# 5. 시각화
#################################################################################################################

mpl.rcParams['savefig.dpi'] = 300   # 저장 DPI 기본값
mpl.rcParams['figure.dpi'] = 100    # 화면 표시용

# 5-1. 성별 분포
# 1) 집계
gender_counts = mbti_data.iloc[:, 3].value_counts()
total = gender_counts.sum()
gender_pct = gender_counts / total * 100

# 2) 표시 순서 맞추기
order = ['여성', '남성', '기타/응답 안 함']
idx = [x for x in order if x in gender_counts.index]  # 데이터에 있는 것만
gender_counts = gender_counts.reindex(idx)
gender_pct = gender_pct.reindex(idx)

# 3) 색(사진 톤 유사)
color_map = {
    '기타/응답 안 함': 'lightgrey',
    '여성': 'lightcoral',
    '남성': 'lightskyblue'
}
colors = [color_map.get(x, 'grey') for x in gender_counts.index]

# 4) 그래프
plt.figure(figsize=(7, 5))
bars = plt.bar(gender_counts.index, gender_counts.values, color=colors)

plt.title('성별 분포', fontsize=16, fontweight='bold')
plt.ylabel('명')

# 라벨 공간 확보
ymax = gender_counts.max()
plt.ylim(0, ymax * 1.15)

# 5) 데이터 라벨: "n명(p%)" 막대 위에 표시
for bar, cnt, pct in zip(bars, gender_counts.values, gender_pct.values):
    x = bar.get_x() + bar.get_width() / 2
    y = bar.get_height()
    plt.text(
        x, y + ymax * 0.02,
        f'{int(cnt)}명({pct:.1f}%)',
        ha='center', va='bottom', fontsize=13)

plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
#plt.savefig('01_gender', dpi=300, bbox_inches='tight')
plt.show()


# 5-2. 나이대 분포
# 1) 집계
age_counts = mbti_data.iloc[:, 4].value_counts()
total = age_counts.sum()
age_pct = age_counts / total * 100

# 2) 표시 순서 맞추기
order = ['10대', '20대', '30대', '40대 이상']
idx = [x for x in order if x in age_counts.index]  # 데이터에 있는 것만
age_counts = age_counts.reindex(idx)
age_pct = age_pct.reindex(idx)

# 3) 그래프
plt.figure(figsize=(7, 5))
bars = plt.bar(age_counts.index, age_counts.values, color='lightskyblue')

plt.title('나이대 분포', fontsize=16, fontweight='bold')

# 라벨 공간 확보
ymax = age_counts.max()
plt.ylim(0, ymax * 1.15)

# 4) 데이터 라벨: "n명(p%)" 막대 위에 표시
for bar, cnt, pct in zip(bars, age_counts.values, age_pct.values):
    x = bar.get_x() + bar.get_width() / 2
    y = bar.get_height()
    plt.text(
        x, y + ymax * 0.02,
        f'{int(cnt)}명({pct:.1f}%)',
        ha='center', va='bottom', fontsize=13)

plt.grid(axis='y', alpha=0.3)
plt.tight_layout()
#plt.savefig('02_age', dpi=300, bbox_inches='tight')
plt.show()


# 5-3. MBTI 검사 방법
method = mbti_data.iloc[:, 5].astype(str)  # 해당 컬럼만 뽑아서 문자열로 통일

# 원문 -> 짧은 라벨 매핑 (키워드 기반)
def short_label(x):
    x = x.strip() # 앞/뒤 공백 제거
    if '인터넷' in x or '16Personalities' in x or '무료' in x:
        return '무료 테스트'
    if '모름' in x or '관심' in x:
        return '모름/관심 없음'
    if '정식' in x or '공인' in x or '기관' in x:
        return '정식 검사'
    if '친구' in x:
        return '친구 판단'
    if '자가' in x or '자기' in x:
        return '자가진단'
    return '기타'

# 짧은 라벨로 변환 후 집계
short_counts = method.apply(short_label).value_counts()

# 원하는 순서로 정렬
order = ['무료 테스트', '모름/관심 없음', '정식 검사', '친구 판단', '자가진단']
short_counts = short_counts.reindex(order).fillna(0).astype(int) # 지정한 순서대로 재배열 + 없는 라벨은 0으로 채움 + 정수로 변환

total = short_counts.sum()  # 전체 응답 수(막대 위 % 계산에 필요)
short_pct = short_counts / total * 100

# 가로 막대 (위에서부터 큰 값이 나오도록 정렬)
plot_counts = short_counts.sort_values(ascending=True)
plot_pct = short_pct.reindex(plot_counts.index)

plt.figure(figsize=(7, 5))
bars = plt.barh(plot_counts.index, plot_counts.values, color="#84cc98", alpha=0.85)

plt.title('MBTI 검사 방법', fontsize=16, fontweight='bold')
plt.xlabel('명')

xmax = plot_counts.max()  # 가장 긴 막대의 값
plt.xlim(0, xmax * 1.2) # x축 범위: 가장 긴 막대의 값보다 1.2배 길게

# 각 막대(객체) + 개수 + 퍼센트를 한 묶음으로 반복
for bar, cnt, pct in zip(bars, plot_counts.values, plot_pct.values):
    x = bar.get_width()  # 막대의 길이(=개수), 글씨를 막대 끝에 붙이기 위해 사용
    y = bar.get_y() + bar.get_height() / 2  # 막대의 세로 중앙 위치(글씨를 중앙에 정렬)
    plt.text(       # 텍스트(데이터 라벨) 표시
        x + xmax * 0.01, y,
        f'{cnt}명 ({pct:.1f}%)',
        va='center', ha='left', fontsize=12)

plt.grid(axis='x', alpha=0.3)
plt.tight_layout()
#plt.savefig('03_test_method', dpi=300, bbox_inches='tight')
plt.show()


# 5-4. MBTI에 대한 신뢰, 태도 변화
belief = mbti_data.iloc[:, 42]
attitude = mbti_data.iloc[:, 45]

# Q42: 숫자형 변환 및 결측 제거
q42 = pd.to_numeric(belief, errors='coerce').dropna().astype(int)

# Q45: 범주형 응답 빈도수 계산
q45_counts = attitude.dropna().astype(str).value_counts().sort_values(ascending=False)

# 색상 설정
hist_color = '#87cefa'
bar_color = '#ff7f7f'

# 그래프 생성
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('MBTI에 대한 신뢰도 분석', fontsize=18, fontweight='bold')

# Q42: MBTI에 대한 신뢰도
ax1 = axes[0]
bins = np.arange(0.5, 8.5, 1)
ax1.hist(q42, bins=bins, color=hist_color, edgecolor='white')
mean_q42 = q42.mean()
ax1.axvline(mean_q42, color='red', linestyle='--', linewidth=2)
ax1.text(mean_q42 + 0.1, ax1.get_ylim()[1]*0.9, f'평균: {mean_q42:.2f}', color='red', fontsize=12)
ax1.set_title('MBTI 신뢰도', fontsize=16, fontweight='bold')
ax1.set_xlabel('신뢰도 (1=안믿음 / 7=정확)', fontsize=13)
ax1.set_ylabel('빈도', fontsize=13)
ax1.set_xticks(range(1, 8))

# Q45: 상대방의 MBTI를 알고 난 후 태도 변화
ax2 = axes[1]

yt_labels = ['바뀌지 않음', '약간 바뀜', 'MBTI 관심 없음', '많이 바뀜']

# 가로 막대그래프
y_pos = np.arange(len(q45_counts))
ax2.barh(y_pos, q45_counts.values, color=bar_color)
ax2.set_yticks(y_pos)
ax2.set_yticklabels(yt_labels, fontsize=12)  # 여기서 원하는 텍스트로 교체
ax2.invert_yaxis()
ax2.set_xlabel('', fontsize=13)
ax2.set_title('MBTI를 알고난 후 태도 변화', fontsize=16, fontweight='bold')

# 데이터 라벨 추가
for i, v in enumerate(q45_counts.values):
    ax2.text(v + max(q45_counts.values)*0.01, i, f'{int(v)}명', va='center', fontsize=11)

plt.tight_layout(rect=[0, 0, 1, 0.95])
#plt.savefig('04_perception.png', dpi=300, bbox_inches='tight')
plt.show()


# 5-5. MBTI 유형 분포: 자기보고 vs 설문 산출
# 16가지 MBTI 유형 목록
mbti_types = ['ISTJ', 'ISFJ', 'INFJ', 'INTJ',
              'ISTP', 'ISFP', 'INFP', 'INTP',
              'ESTP', 'ESFP', 'ENFP', 'ENTP',
              'ESTJ', 'ESFJ', 'ENFJ', 'ENTJ']

# 각 유형별 빈도 계산
user_counts = pd.Series(filtered_user).value_counts().reindex(mbti_types, fill_value=0)
pred_counts = pd.Series(filtered_predict).value_counts().reindex(mbti_types, fill_value=0)

# 자기보고 기준 내림차순 정렬
sorted_by_user = user_counts.sort_values(ascending=True)
sorted_pred = pred_counts.reindex(sorted_by_user.index)

# 색상 팔레트 (유형별 고유 색상)
colors = plt.cm.tab20.colors  # 20가지 색상
color_map = {mbti: colors[i] for i, mbti in enumerate(mbti_types)}
user_colors = [color_map[m] for m in sorted_by_user.index]
pred_colors = [color_map[m] for m in sorted_pred.index]

# 그래프 그리기
fig, axes = plt.subplots(1, 2, figsize=(13, 8))
fig.suptitle('MBTI 유형 분포: 자기보고 vs 설문 산출', fontsize=16, fontweight='bold', y=1.01)

# 왼쪽: 자기보고 MBTI
axes[0].barh(sorted_by_user.index, sorted_by_user.values, color=user_colors)
axes[0].set_title('자기보고 MBTI', fontsize=14, fontweight='bold')
axes[0].set_xlabel('인원수')
axes[0].set_xlim(0, max(user_counts.max(), pred_counts.max()) + 2)
axes[0].grid(axis='x', linestyle='--', alpha=0.5)
axes[0].spines[['top', 'right']].set_visible(False)

# 오른쪽: 설문 산출 MBTI (설문 산출 기준 내림차순 정렬)
sorted_pred_desc = pred_counts.sort_values(ascending=True)
pred_colors_right = [color_map[m] for m in sorted_pred_desc.index]

axes[1].barh(sorted_pred_desc.index, sorted_pred_desc.values, color=pred_colors_right)
axes[1].set_title('설문 산출 MBTI', fontsize=14, fontweight='bold')
axes[1].set_xlabel('인원수')
axes[1].set_xlim(0, max(user_counts.max(), pred_counts.max()) + 2)
axes[1].grid(axis='x', linestyle='--', alpha=0.5)
axes[1].spines[['top', 'right']].set_visible(False)

plt.tight_layout()
#plt.savefig('05_act_pred.png', dpi=300, bbox_inches='tight')
plt.show()


# 5-6. 요소별+전체 회귀분석 예측률
labels = ['E/I', 'S/N', 'T/F', 'J/P', '전체 MBTI']
scores = [score_ei * 100, score_sn * 100, score_tf * 100, score_jp * 100, score_total * 100]
bar_colors = ['#4C72B0', '#DD8452', '#55A868', '#C44E52', '#8172B2']

fig, ax = plt.subplots(figsize=(9, 6))

bars = ax.bar(labels, scores, color=bar_colors, width=0.5, edgecolor='white', linewidth=0.8)

# 막대 위에 수치 표시
for bar, score in zip(bars, scores):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.5,
        f'{score:.2f}%',
        ha='center', va='bottom', fontsize=11
    )

ax.set_title('로지스틱 회귀 모델 예측 정확도', fontsize=15, fontweight='bold', pad=15)
ax.set_ylabel('정확도(%)', fontsize=12)
ax.set_ylim(0, 110)
ax.grid(axis='y', linestyle='--', alpha=0.5)
ax.spines[['top', 'right']].set_visible(False)

plt.tight_layout()
#plt.savefig('06_regression_accuracy.png', dpi=300, bbox_inches='tight')
plt.show()


# 5-7. 요소별 예측-실제 비율 가로 누적 막대그래프
fig, axes = plt.subplots(2, 2, figsize=(14, 8))
fig.suptitle('MBTI 지표별 실제-예측 비율', fontsize=16, fontweight='bold')

# 각 요소별 설정을 튜플 리스트로 정의 (축, 예측값, 실제값, 레이블, 색상, 제목)
configs = [
    (axes[0, 0], reg_predict_ei, extract_ei, ['I', 'E'], ['#F4A7A3', '#7DB8DC'], 'E / I'),
    (axes[0, 1], reg_predict_sn, extract_sn, ['S', 'N'], ['#A8D8A8', '#F4C07A'], 'S / N'),
    (axes[1, 0], reg_predict_tf, extract_tf, ['F', 'T'], ['#F4F0A0', '#C4A8DC'], 'T / F'),
    (axes[1, 1], reg_predict_jp, extract_jp, ['J', 'P'], ['#F4A8C0', '#A8C8F0'], 'J / P'),
]

# 각 지표별 서브플롯 순회
for ax, pred, actual, labels, colors, title in configs:
    # 예측값(Predict)과 실제값(Actual) 두 행을 순서대로 처리
    for data, row_label in zip([pred, actual], ['Predict', 'Actual']):
        # 전체 데이터 수 (비율 계산 분모)
        total = len(data)
        # 누적 막대의 시작 위치 (왼쪽부터 쌓아나감)
        left = 0
        # 각 레이블 별로 누적 막대 그리기
        for label, color in zip(labels, colors):
            # 해당 레이블의 비율 계산
            ratio = np.sum(data == label) / total
            # 누적 가로 막대 그리기
            ax.barh(row_label, ratio, left=left, color=color, edgecolor='white', linewidth=0.5, height=0.5)
            # 막대가 너무 좁으면 텍스트가 겹치므로 5% 이상일 때만 수치 표시
            if ratio > 0.05:
                ax.text(left + ratio / 2, row_label, f'{ratio * 100:.1f}%',
                        ha='center', va='center', fontsize=11, fontweight='bold')
            
            # 다음 레이블의 시작 위치를 현재 비율만큼 오른쪽으로 이동
            left += ratio

    ax.set_title(title, fontsize=12)
    ax.set_xlim(0, 1)
    # 위/오른쪽/왼쪽 테두리 제거
    #ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.tick_params(left=False)
    ax.legend(labels, loc='center right', bbox_to_anchor=(1.0, 0.5),
              framealpha=0.8, fontsize=9)

plt.tight_layout()
#plt.savefig('07_mbti_ratio.png', dpi=300, bbox_inches='tight')
plt.show()


# 5-8. 요소별 로지스틱 회귀 결과

# 요소별 설정 리스트 (평균값 컬럼, 실제 레이블, 모델, 인코더, x축 레이블, 제목, 저장 파일명)
element_configs = [
    (df_avg.loc[valid_value, 'avg_ei'], extract_ei, model_ei, le_ei, 'E/I 평균 점수', 'E/I 로지스틱 회귀 결과', '08_regression_ei.png'),
    (df_avg.loc[valid_value, 'avg_sn'], extract_sn, model_sn, le_sn, 'S/N 평균 점수', 'S/N 로지스틱 회귀 결과', '08_regression_sn.png'),
    (df_avg.loc[valid_value, 'avg_tf'], extract_tf, model_tf, le_tf, 'T/F 평균 점수', 'T/F 로지스틱 회귀 결과', '08_regression_tf.png'),
    (df_avg.loc[valid_value, 'avg_jp'], extract_jp, model_jp, le_jp, 'J/P 평균 점수', 'J/P 로지스틱 회귀 결과', '08_regression_jp.png'),
]

# 요소별 그래프 (4장)
for avg_col, actual, model, le, xlabel, title, filename in element_configs:

    # 실제 레이블을 숫자로 인코딩 (예: E=0, I=1)
    y_encoded = le.transform(actual)

    # 평균 점수를 2D 배열로 변환 (모델 입력 형식)
    X_avg = avg_col.values.reshape(-1, 1)

    # 시그모이드 곡선을 부드럽게 그리기 위한 x 범위 생성 (1~7 사이 300개 점)
    x_line = np.linspace(1, 7, 300).reshape(-1, 1)

    # 단일 평균값으로 예측 확률 계산 (양성 클래스 확률, 인덱스 1)
    # 단, 모델은 9개 문항으로 학습됐으므로 avg만으로는 predict_proba 불가 -> 회귀계수로 직접 계산
    # 대신 평균 점수 1개짜리 별도 단순 로지스틱 회귀 모델을 새로 학습해서 시각화용으로 사용
    
    # 시각화 전용 단순 모델 (평균값 1개로 학습)
    simple_model = LR(max_iter=1000)
    simple_model.fit(X_avg, y_encoded)

    # x_line에 대한 예측 확률 (시그모이드 곡선)
    y_prob = simple_model.predict_proba(x_line)[:, 1]

    # 그래프 생성
    fig, ax = plt.subplots(figsize=(8, 6))

    # 실제 데이터 산점도 (파란 점)
    ax.scatter(avg_col, y_encoded, color='blue', label='실제 데이터', zorder=3, alpha=0.6)

    # 시그모이드 예측 곡선 (빨간 선)
    ax.plot(x_line, y_prob, color='red', label='예측값 (확률)', linewidth=2)

    # 그래프 제목 및 축 레이블 설정
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel('예측 확률', fontsize=12)

    # x축 범위 설정 (설문 응답 범위 1~7)
    ax.set_xlim(0.5, 7.5)

    # y축 범위 설정 (확률 0~1)
    ax.set_ylim(-0.1, 1.1)

    # y축 눈금 레이블을 인코딩된 클래스명으로 표시 (예: 0=E, 1=I)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(le.classes_)

    # 범례 표시
    ax.legend(fontsize=11, loc='right')

    # 위/오른쪽 테두리 제거
    ax.spines[['top', 'right']].set_visible(False)

    # 그리드 추가 (y축 방향)
    ax.grid(axis='y', linestyle='--', alpha=0.4)

    plt.tight_layout()
    #plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()

    
# 5-9. 전체 MBTI 회귀 결과

# 전체 MBTI 모델도 별도로 저장 (시각화용)
model_total, le_total, score_total = mbti_logistic_regression(X_total, y_total, '전체 MBTI', max_iter=1000, is_raw=False)

# 전체 데이터에 대한 예측값 (16가지 유형)
reg_predict_total = le_total.inverse_transform(model_total.predict(X_total))

# 실제값과 예측값을 숫자로 인코딩
y_total_encoded = le_total.transform(y_total)
y_total_pred_encoded = model_total.predict(X_total)

# 샘플 인덱스 (x축)
sample_index = np.arange(len(y_total))

# 실제값 기준으로 정렬 (시각적으로 패턴 파악 용이)
sorted_idx = np.argsort(y_total_encoded)

fig, ax = plt.subplots(figsize=(12, 6))

# 실제 데이터 산점도 (파란 점)
ax.scatter(sample_index, y_total_encoded[sorted_idx], color='blue', label='실제 데이터', s=30, alpha=0.6, zorder=3)

# 예측값 산점도 (빨간 점, 선으로 연결)
ax.plot(sample_index, y_total_pred_encoded[sorted_idx], color='red', label='예측값', linewidth=1.5, alpha=0.8)

# 그래프 제목 및 축 레이블 설정
ax.set_title('전체 MBTI 로지스틱 회귀 결과', fontsize=14, fontweight='bold')
ax.set_xlabel('샘플 인덱스 (실제값 기준 정렬)', fontsize=12)
ax.set_ylabel('MBTI 유형', fontsize=12)

# y축 눈금을 MBTI 유형명으로 표시
ax.set_yticks(range(len(le_total.classes_)))
ax.set_yticklabels(le_total.classes_, fontsize=9)

# 범례 표시
ax.legend(fontsize=11)

# 위/오른쪽 테두리 제거
ax.spines[['top', 'right']].set_visible(False)

# 그리드 추가
ax.grid(axis='y', linestyle='--', alpha=0.4)

plt.tight_layout()
#plt.savefig('09_regression_total.png', dpi=300, bbox_inches='tight')
plt.show()


# 5-10. 랜덤 포레스트 모델: 요소별 변수 중요도 (Feature Importance)

# 요소별 설정 (모델, 컬럼명, 제목, 저장 파일명)
rf_configs = [
    (rf_model_ei, df_ei.iloc[:, :-1].columns, 'E/I', '10_rf_importance_ei.png'),
    (rf_model_sn, df_sn.iloc[:, :-1].columns, 'S/N', '10_rf_importance_sn.png'),
    (rf_model_tf, df_tf.iloc[:, :-1].columns, 'T/F', '10_rf_importance_tf.png'),
    (rf_model_jp, df_jp.iloc[:, :-1].columns, 'J/P', '10_rf_importance_jp.png'),
]

for model, columns, label, filename in rf_configs:

    # 변수 중요도 추출 후 내림차순 정렬
    importances = pd.Series(model.feature_importances_, index=columns)
    importances = importances.sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(8, 6))

    # 변수 중요도 가로 막대 그래프 (중요도 높을수록 진한 색)
    colors = plt.cm.Blues(np.linspace(0.3, 0.9, len(importances)))
    bars = ax.barh(importances.index, importances.values, color=colors)

    # 막대 끝에 수치 표시
    for bar, val in zip(bars, importances.values):
        ax.text(bar.get_width() + 0.002, bar.get_y() + bar.get_height() / 2,
                f'{val:.3f}', va='center', fontsize=10)

    # 그래프 제목 및 축 설정
    ax.set_title(f'{label} 변수 중요도 (Random Forest)', fontsize=14, fontweight='bold')
    ax.set_xlabel('중요도', fontsize=12)
    ax.set_xlim(0, importances.max() + 0.05)
    ax.spines[['top', 'right']].set_visible(False)

    plt.tight_layout()
    #plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.show()


# 5-11. 랜덤 포레스트 모델: 전체 MBTI 혼동 행렬

# 전체 데이터로 예측
y_true_total = le_total.transform(y_total)
y_pred_total = rf_model_total.predict(X_total)

# 혼동 행렬 계산
cm_total = confusion_matrix(y_true_total, y_pred_total)

fig, ax = plt.subplots(figsize=(12, 10))

# 히트맵으로 시각화 (16x16 행렬)
sns.heatmap(cm_total, annot=True, fmt='d', cmap='Blues',
            xticklabels=le_total.classes_,
            yticklabels=le_total.classes_,
            ax=ax)

ax.set_title('전체 MBTI 혼동 행렬 (Random Forest)', fontsize=15, fontweight='bold')
ax.set_xlabel('예측값', fontsize=12)
ax.set_ylabel('실제값', fontsize=12)

# x축 레이블 45도 회전 (16가지 유형이라 겹침 방지)
plt.xticks(rotation=45)
plt.yticks(rotation=0)

plt.tight_layout()
#plt.savefig('11_rf_cm_total.png', dpi=300, bbox_inches='tight')
plt.show()


# 5-12. 랜덤 포레스트 모델: 트리
plt.figure(figsize=(14, 6))
tree.plot_tree(
    rf_model_ei.estimators_[0],  # 0번째 트리 한 개만
    feature_names=df_ei.loc[valid_value].iloc[:, :-1].columns,
    class_names=le_ei.classes_,
    filled=True,
    max_depth=3,   # 너무 깊으면 보기 힘들어서 3 정도 추천
    fontsize=8
)
plt.title('E/I 랜덤포레스트 - 트리 1개 미리보기', fontweight='bold')
#plt.savefig('12_rf_tree.png', dpi=300, bbox_inches='tight')
plt.tight_layout()
plt.show()


# 5-13. 랜덤 포레스트 모델: 요소별 + 전체 MBTI 정확도
# 지표명과 정확도 리스트 정리
labels = ['E/I', 'S/N', 'T/F', 'J/P', '전체 MBTI']
scores = [rf_score_ei * 100, rf_score_sn * 100, rf_score_tf * 100, rf_score_jp * 100, rf_score_total * 100]

# 막대별 색상 (로지스틱 회귀 그래프와 동일한 색상 팔레트 사용)
bar_colors = ['#4C72B0', '#DD8452', '#55A868', '#C44E52', '#8172B2']

fig, ax = plt.subplots(figsize=(9, 6))

# 막대 그래프 생성
bars = ax.bar(labels, scores, color=bar_colors, width=0.5, edgecolor='white', linewidth=0.8)

# 막대 위에 정확도 수치 표시
for bar, score in zip(bars, scores):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.5,
        f'{score:.2f}%',
        ha='center', va='bottom', fontsize=11, fontweight='bold'
    )

# 그래프 제목 및 축 설정
ax.set_title('랜덤 포레스트 모델 예측 정확도', fontsize=15, fontweight='bold', pad=15)
ax.set_ylabel('정확도 (%)', fontsize=12)
ax.set_ylim(0, 110)
ax.grid(axis='y', linestyle='--', alpha=0.5)
ax.spines[['top', 'right']].set_visible(False)

plt.tight_layout()
#plt.savefig('13_rf_accuracy.png', dpi=300, bbox_inches='tight')
plt.show()