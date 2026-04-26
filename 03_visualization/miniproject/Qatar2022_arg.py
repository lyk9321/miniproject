import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib

########## 1. 데이터 전처리 ##########

##### 1-1. 필드 플레이어 데이터 정리하기

# 데이터 불러오기
player_defense = pd.read_excel('player_defense.xlsx')
player_passing = pd.read_excel('player_passing.xlsx')
player_possession = pd.read_excel('player_possession.xlsx')
player_shooting = pd.read_excel('player_shooting.xlsx')
player_stats = pd.read_excel('player_stats.xlsx')

# 데이터 슬라이싱
df_def = player_defense.loc[:, ['player', 'tackles', 'tackles_won', 'dribble_tackles', 'dribble_tackles_pct', 'dribbled_past', 'blocks', 'interceptions', 'tackles_interceptions', 'clearances']]
df_pass = player_passing.loc[:, ['player', 'passes_completed', 'passes', 'passes_pct', 'progressive_passes']]
df_pos = player_possession.loc[:, ['player', 'touches', 'touches_def_pen_area', 'dribbles', 'dribbles_completed_pct', 'miscontrols', 'dispossessed', 'passes_received']]
df_shoot = player_shooting.loc[:, ['player', 'shots', 'shots_on_target']]
df_stats = player_stats.loc[:, ['player', 'position', 'team', 'birth_year', 'minutes_90s', 'goals', 'assists', 'xg']]

# 데이터 합치기
df_total = (df_stats
            .merge(df_def, on='player', how='left')
            .merge(df_pass, on='player', how='left')
            .merge(df_pos, on='player', how='left')
            .merge(df_shoot, on='player', how='left')
)

# 결측치 수 확인
#print(df_total.isna().sum())

# 결측치 0으로 대체하기
df_total.fillna(0, inplace=True)

# 골키퍼 데이터 삭제
df_total = df_total[df_total['position'] != 'GK'].copy()

# 팀, 포지션, 선수 이름으로 오름차순 정렬
df_total.sort_values(by=['team', 'position', 'player'], inplace=True)


##### 1-2. 골키퍼 데이터 정리하기

# 데이터 불러오기
player_keepers = pd.read_excel('player_keepers.xlsx')

# 데이터 슬라이싱
df_keep = player_keepers.loc[:, ['player', 'position', 'team', 'birth_year', 'gk_games', 'gk_minutes', 'minutes_90s', 'gk_goals_against', 'gk_goals_against_per90', 'gk_shots_on_target_against', 'gk_saves', 'gk_save_pct']]

# 결측치 0으로 대체하기
df_keep.fillna(0, inplace=True)

# 팀, 이름으로 오름차순 정렬
df_keep.sort_values(by=['team', 'player'], inplace=True)


########## 2. 수비수 ##########

##### 2-1. 변수 선택, 데이터 만들기

# 수비수, 필요한 컬럼 추출
df_DF = df_total.loc[df_total['position'] == 'DF', 
                     ['team', 'player', 'minutes_90s', 'tackles_won', 'blocks', 'interceptions', 'clearances']].copy()

# 출전 시간 180분 이상(주전/준주전) 선수만 필터링
df_DF = df_DF[df_DF['minutes_90s'] >= 2].copy()

# 팀 별로 묶어서 각 선수들 수치의 합계를 구함 
df_DF_team = df_DF.groupby('team')[['minutes_90s', 'tackles_won', 'blocks', 'interceptions', 'clearances']].sum()

# 팀 별로 90분당 능력치 계산하기(출전시간 가중)
for i in ['tackles_won', 'blocks', 'interceptions', 'clearances']:
    df_DF_team[i + '_per90'] = df_DF_team[i] / df_DF_team['minutes_90s']


##### 2-2. 시각화

# 각 지표별 Top10 데이터
df_DF_bar1 = df_DF_team[['tackles_won_per90']].sort_values('tackles_won_per90', ascending=False)
DF_rank1 = df_DF_bar1.index.get_loc('Argentina') + 1    # 랭킹용 변수 따로 빼두기
df_DF_bar1 = df_DF_bar1.head(10)

df_DF_bar2 = df_DF_team[['blocks_per90']].sort_values('blocks_per90', ascending=False)
DF_rank2 = df_DF_bar2.index.get_loc('Argentina') + 1    # 랭킹용 변수 따로 빼두기
df_DF_bar2 = df_DF_bar2.head(10)

df_DF_bar3 = df_DF_team[['interceptions_per90']].sort_values('interceptions_per90', ascending=False)
DF_rank3 = df_DF_bar3.index.get_loc('Argentina') + 1    # 랭킹용 변수 따로 빼두기
df_DF_bar3 = df_DF_bar3.head(10)

df_DF_bar4 = df_DF_team[['clearances_per90']].sort_values('clearances_per90', ascending=False)
DF_rank4 = df_DF_bar4.index.get_loc('Argentina') + 1    # 랭킹용 변수 따로 빼두기
df_DF_bar4 = df_DF_bar4.head(10)

### 2-2-1. 순위별 Top 10 그래프
# subplots 언팩
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 10))

# 아르헨티나 색상 강조
HIGHLIGHT_TEAM = 'Argentina'
highlight_color = 'orangered'   # 아르헨티나 색상 막대
base_color = 'lightgrey'          # 나머지 막대

# tackles_won_per90
sns.barplot(x=df_DF_bar1["tackles_won_per90"], y=df_DF_bar1.index, orient="h", 
            palette=[highlight_color if c == HIGHLIGHT_TEAM else base_color for c in df_DF_bar1.index], ax=ax1)
ax1.set_title('태클 성공 (개/90min)')
ax1.set_xlabel('tackles_won_per90')
ax1.set_ylabel('')

# blocks_per90
sns.barplot(x=df_DF_bar2["blocks_per90"], y=df_DF_bar2.index, orient="h", 
            palette=[highlight_color if c == HIGHLIGHT_TEAM else base_color for c in df_DF_bar2.index], ax=ax2)
ax2.set_title('블록 (개/90min)')
ax2.set_xlabel('blocks_per90')
ax2.set_ylabel('')

# interceptions_per90
sns.barplot(x=df_DF_bar3["interceptions_per90"], y=df_DF_bar3.index, orient="h", 
            palette=[highlight_color if c == HIGHLIGHT_TEAM else base_color for c in df_DF_bar3.index], ax=ax3)
ax3.set_title('인터셉션 (개/90min)')
ax3.set_xlabel('interceptions_per90')
ax3.set_ylabel('')

# clearances_per90
sns.barplot(x=df_DF_bar4["clearances_per90"], y=df_DF_bar4.index, orient="h", 
            palette=[highlight_color if c == HIGHLIGHT_TEAM else base_color for c in df_DF_bar4.index], ax=ax4)
ax4.set_title('클리어링 (개/90min)')
ax4.set_xlabel('clearances_per90')
ax4.set_ylabel('')

# 전체 제목 설정 및 출력
fig.suptitle('Argentina DF 관련 지표', fontsize=20)
plt.tight_layout()
plt.show()

### 2-2-2. Argentina DF 지표별 순위 선그래프
# 라벨, 값 설정
DF_labels = ['tackles_won', 'blocks', 'interceptions', 'clearances']
DF_ranks  = [DF_rank1, DF_rank2, DF_rank3, DF_rank4]

# 선 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 10))
ax.plot(DF_labels, DF_ranks, color=highlight_color, linewidth=3, marker='o', markersize=8)
ax.set_title('Argentina DF 지표별 순위', fontsize=20)
ax.set_ylabel('Rank')
ax.set_ylim(1, 32)
ax.invert_yaxis()  # 1등이 위로 오게 축 뒤집기
ax.set_yticks([1, 5, 10, 15, 20, 25, 30])   # 축 레이블 설정

# 데이터레이블 출력
for x, y in zip(DF_labels, DF_ranks):   # 두 리스트를 하나로 묶기
    ax.annotate(
        f'{y}', (x, y),     # DF_ranks의 숫자를 x, y 좌표에 배치
        textcoords="offset points", xytext=(0, 10),     # 좌표에서 포인트 단위로 이동하기
        ha='center'     # 글자를 가운데 정렬하기
    )

# 배경 무늬 설정 및 출력
plt.grid(True, axis='y', alpha=0.5)
plt.tight_layout()
plt.show()


########## 3. 미드필더 ##########

##### 3-1. 변수 선택, 데이터 만들기

# 미드필더, 필요한 컬럼 추출
df_MF = df_total.loc[df_total['position'] == 'MF', 
                     ['team', 'player', 'minutes_90s', 'passes', 'passes_completed', 'progressive_passes', 'dribbles_completed_pct'] ].copy()

# 출전시간 180분 이상(주전/준주전) 선수만 필터링
df_MF = df_MF[df_MF['minutes_90s'] >= 2].copy()

# 팀 별로 묶어서 각 선수들 수치의 합계를 구함 (dribbles_completed_pct 제외)
df_MF_team = df_MF.groupby('team')[['minutes_90s', 'passes', 'passes_completed', 'progressive_passes']].sum()

# passes_per90: 팀 per90
df_MF_team['passes_per90'] = df_MF_team['passes'] / df_MF_team['minutes_90s']

# passes_pct: 팀 비율
df_MF_team['passes_pct'] = (df_MF_team['passes_completed'] / df_MF_team['passes']) * 100

# progressive_passes: 팀 per90
df_MF_team['progressive_passes_per90'] = df_MF_team['progressive_passes'] / df_MF_team['minutes_90s']

# dribbles_completed_pct: 출전시간 가중평균
df_MF_team['dribbles_completed_pct'] = (df_MF.groupby('team').apply(lambda x: (x['dribbles_completed_pct'] * x['minutes_90s']).sum() / x['minutes_90s'].sum()))


##### 3-2. 시각화

# 각 지표별 Top10 데이터
df_MF_bar1 = df_MF_team[['passes_per90']].sort_values('passes_per90', ascending=False)
MF_rank1 = df_MF_bar1.index.get_loc('Argentina') + 1
df_MF_bar1 = df_MF_bar1.head(10)

df_MF_bar2 = df_MF_team[['passes_pct']].sort_values('passes_pct', ascending=False)
MF_rank2 = df_MF_bar2.index.get_loc('Argentina') + 1
df_MF_bar2 = df_MF_bar2.head(10)

df_MF_bar3 = df_MF_team[['progressive_passes_per90']].sort_values('progressive_passes_per90', ascending=False)
MF_rank3 = df_MF_bar3.index.get_loc('Argentina') + 1
df_MF_bar3 = df_MF_bar3.head(10)

df_MF_bar4 = df_MF_team[['dribbles_completed_pct']].sort_values('dribbles_completed_pct', ascending=False)
MF_rank4 = df_MF_bar4.index.get_loc('Argentina') + 1
df_MF_bar4 = df_MF_bar4.head(10)


### 3-2-1. 순위별 Top 10 그래프
# subplots 언팩
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 10))

# 아르헨티나 색상 강조
HIGHLIGHT_TEAM = 'Argentina'
highlight_color = 'orangered'
base_color = 'lightgrey'

# passes_per90
sns.barplot(x=df_MF_bar1["passes_per90"], y=df_MF_bar1.index, orient="h", 
            palette=[highlight_color if c == HIGHLIGHT_TEAM else base_color for c in df_MF_bar1.index], ax=ax1)
ax1.set_title('패스 시도 (회/90min)')
ax1.set_xlabel('passes_per90')
ax1.set_ylabel('')

# passes_pct
sns.barplot(x=df_MF_bar2["passes_pct"], y=df_MF_bar2.index, orient="h", 
            palette=[highlight_color if c == HIGHLIGHT_TEAM else base_color for c in df_MF_bar2.index], ax=ax2)
ax2.set_title('패스 성공률 (%)')
ax2.set_xlabel('passes_pct')
ax2.set_ylabel('')

# progressive_passes_per90
sns.barplot(x=df_MF_bar3["progressive_passes_per90"], y=df_MF_bar3.index, orient="h", 
            palette=[highlight_color if c == HIGHLIGHT_TEAM else base_color for c in df_MF_bar3.index], ax=ax3)
ax3.set_title('전진 패스 (개/90min)')
ax3.set_xlabel('progressive_passes_per90')
ax3.set_ylabel('')

# dribbles_completed_pct
sns.barplot(x=df_MF_bar4["dribbles_completed_pct"], y=df_MF_bar4.index, orient="h", 
            palette=[highlight_color if c == HIGHLIGHT_TEAM else base_color for c in df_MF_bar4.index], ax=ax4)
ax4.set_title('드리블 성공률 (%)')
ax4.set_xlabel('dribbles_completed_pct')
ax4.set_ylabel('')

# 전체 제목 설정 및 출력
fig.suptitle('Argentina MF 관련 지표', fontsize=20)
plt.tight_layout()
plt.show()


### 3-2-2. Argentina MF 지표별 순위 선그래프
# 라벨, 값 설정
MF_labels = ['passes_per90', 'passes_pct', 'progressive_passes', 'dribbles_completed_pct']
MF_ranks = [MF_rank1, MF_rank2, MF_rank3, MF_rank4]

# 선 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 10))
ax.plot(MF_labels, MF_ranks, color=highlight_color, linewidth=3, marker='o', markersize=8)
ax.set_title('Argentina MF 지표별 순위', fontsize=20)
ax.set_ylabel('Rank')
ax.set_ylim(1, 32)
ax.invert_yaxis()
ax.set_yticks([1, 5, 10, 15, 20, 25, 30])

# 데이터레이블 출력
for x, y in zip(MF_labels, MF_ranks):
    ax.annotate(
    f'{y}', (x, y),
    textcoords="offset points", xytext=(0, 10),
    ha='center'
    )

# 배경 무늬 설정 및 출력
plt.grid(True, axis='y', alpha=0.5)
plt.tight_layout()
plt.show()


########## 4. 공격수 ##########

##### 4-1. 변수 선택, 데이터 만들기

# 공격수, 필요한 컬럼 추출
df_FW = df_total.loc[df_total['position'] == 'FW',
                     ['team', 'player', 'minutes_90s', 'shots', 'shots_on_target', 'xg', 'goals']].copy()

# 출전시간 180분 이상(주전/준주전) 선수만 필터링
df_FW = df_FW[df_FW['minutes_90s'] >= 2].copy()

# 팀 별로 묶어서 각 선수들 수치의 합계를 구함 
df_FW_team = df_FW.groupby('team')[['minutes_90s', 'shots', 'shots_on_target', 'xg', 'goals']].sum()

# 팀 per90 지표 생성
for j in ['shots', 'shots_on_target', 'xg', 'goals']:
    df_FW_team[j + '_per90'] = df_FW_team[j] / df_FW_team['minutes_90s']


##### 4-2. 시각화

# 각 지표별 Top10 데이터
df_FW_bar1 = df_FW_team[['shots_per90']].sort_values('shots_per90', ascending=False)
FW_rank1 = df_FW_bar1.index.get_loc('Argentina') + 1
df_FW_bar1 = df_FW_bar1.head(10)

df_FW_bar2 = df_FW_team[['shots_on_target_per90']].sort_values('shots_on_target_per90', ascending=False)
FW_rank2 = df_FW_bar2.index.get_loc('Argentina') + 1
df_FW_bar2 = df_FW_bar2.head(10)

df_FW_bar3 = df_FW_team[['xg_per90']].sort_values('xg_per90', ascending=False)
FW_rank3 = df_FW_bar3.index.get_loc('Argentina') + 1
df_FW_bar3 = df_FW_bar3.head(10)

df_FW_bar4 = df_FW_team[['goals_per90']].sort_values('goals_per90', ascending=False)
FW_rank4 = df_FW_bar4.index.get_loc('Argentina') + 1
df_FW_bar4 = df_FW_bar4.head(10)

### 4-2-1. 순위별 Top 10 그래프
# subplots 언팩
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 10))

# 아르헨티나 색상 강조
HIGHLIGHT_TEAM = 'Argentina'
highlight_color = 'orangered'
base_color = 'lightgrey'

# shots_per90
sns.barplot(x=df_FW_bar1["shots_per90"], y=df_FW_bar1.index, orient="h", 
            palette=[highlight_color if c == HIGHLIGHT_TEAM else base_color for c in df_FW_bar1.index], ax=ax1)
ax1.set_title('슈팅 (개/90min)')
ax1.set_xlabel('shots_per90')
ax1.set_ylabel('')

# shots_on_target_per90
sns.barplot(x=df_FW_bar2["shots_on_target_per90"], y=df_FW_bar2.index, orient="h", 
            palette=[highlight_color if c == HIGHLIGHT_TEAM else base_color for c in df_FW_bar2.index], ax=ax2)
ax2.set_title('유효슈팅 (개/90min)')
ax2.set_xlabel('shots_on_target_per90')
ax2.set_ylabel('')

# xg_per90
sns.barplot(x=df_FW_bar3["xg_per90"], y=df_FW_bar3.index, orient="h", 
            palette=[highlight_color if c == HIGHLIGHT_TEAM else base_color for c in df_FW_bar3.index], ax=ax3)
ax3.set_title('xG (90min 기준)')
ax3.set_xlabel('xg_per90')
ax3.set_ylabel('')

# goals_per90
sns.barplot(x=df_FW_bar4["goals_per90"], y=df_FW_bar4.index, orient="h", 
            palette=[highlight_color if c == HIGHLIGHT_TEAM else base_color for c in df_FW_bar4.index], ax=ax4)
ax4.set_title('득점 (개/90min)')
ax4.set_xlabel('goals_per90')
ax4.set_ylabel('')

# 전체 제목 설정 및 출력
fig.suptitle('Argentina FW 관련 지표', fontsize=20)
plt.tight_layout()
plt.show()

### 4-2-2. Argentina FW 지표별 순위 선그래프
# 라벨, 값 설정
FW_labels = ['shots', 'shots_on_target', 'xg', 'goals']
FW_ranks = [FW_rank1, FW_rank2, FW_rank3, FW_rank4]

# 선 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 10))
ax.plot(FW_labels, FW_ranks, color=highlight_color, linewidth=3, marker='o', markersize=8)
ax.set_title('Argentina FW 지표별 순위', fontsize=20)
ax.set_ylabel('Rank')
ax.set_ylim(1, 32)
ax.invert_yaxis()
ax.set_yticks([1, 5, 10, 15, 20, 25, 30])

# 데이터레이블 출력
for x, y in zip(FW_labels, FW_ranks):
    ax.annotate(
    f'{y}', (x, y),
    textcoords="offset points", xytext=(0, -20),
    ha='center'
    )

# 배경 무늬 설정 및 출력
plt.grid(True, axis='y', alpha=0.5)
plt.tight_layout()
plt.show()


########## 5. 골키퍼 ##########

##### 5-1. 변수 선택, 데이터 만들기

# 골키퍼, 필요한 컬럼 추출
df_GK = df_keep.loc[:, ['team', 'player', 'minutes_90s', 'gk_goals_against', 'gk_shots_on_target_against', 'gk_saves']].copy()

# 출전시간 180분 이상(주전/준주전) 필터링
df_GK = df_GK[df_GK['minutes_90s'] >= 2].copy()

# 팀 별로 묶어서 각 선수들 수치의 합계를 구함 (분자/분모용)
df_GK_team = df_GK.groupby('team')[['minutes_90s','gk_goals_against','gk_shots_on_target_against','gk_saves']].sum()

# 팀 per90 지표 생성
for k in ['gk_goals_against', 'gk_shots_on_target_against', 'gk_saves']:
    df_GK_team[k + '_per90'] = df_GK_team[k] / df_GK_team['minutes_90s']

# save_pct: 팀 비율
df_GK_team['save_pct'] = (df_GK_team['gk_saves'] / df_GK_team['gk_shots_on_target_against']) * 100


##### 5-2. 시각화

# 각 지표별 Top10 데이터
df_GK_bar1 = df_GK_team[['save_pct']].sort_values('save_pct', ascending=False)
GK_rank1 = df_GK_bar1.index.get_loc('Argentina') + 1
df_GK_bar1 = df_GK_bar1.head(10)

df_GK_bar2 = df_GK_team[['gk_goals_against_per90']].sort_values('gk_goals_against_per90', ascending=True) # 낮을수록 좋음
GK_rank2 = df_GK_bar2.index.get_loc('Argentina') + 1
df_GK_bar2 = df_GK_bar2.head(10)

df_GK_bar3 = df_GK_team[['gk_shots_on_target_against_per90']].sort_values('gk_shots_on_target_against_per90', ascending=True) # 낮을수록 좋음
GK_rank3 = df_GK_bar3.index.get_loc('Argentina') + 1
df_GK_bar3 = df_GK_bar3.head(10)

df_GK_bar4 = df_GK_team[['gk_saves_per90']].sort_values('gk_saves_per90', ascending=False)
GK_rank4 = df_GK_bar4.index.get_loc('Argentina') + 1
df_GK_bar4 = df_GK_bar4.head(10)

### 5-2-1. 순위별 Top 10 그래프
# subplots 언팩
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 10))

# 아르헨티나 색상 강조
HIGHLIGHT_TEAM = 'Argentina'
highlight_color = 'orangered'
base_color = 'lightgrey'

# save_pct
sns.barplot(x=df_GK_bar1["save_pct"], y=df_GK_bar1.index, orient="h", 
            palette=[highlight_color if c == HIGHLIGHT_TEAM else base_color for c in df_GK_bar1.index], ax=ax1)
ax1.set_title('선방률 (%)')
ax1.set_xlabel('save_pct')
ax1.set_ylabel('')

# goals_against_per90
sns.barplot(x=df_GK_bar2["gk_goals_against_per90"], y=df_GK_bar2.index, orient="h", 
            palette=[highlight_color if c == HIGHLIGHT_TEAM else base_color for c in df_GK_bar2.index], ax=ax2)
ax2.set_title('실점 (개/90min) ↓')
ax2.set_xlabel('gk_goals_against_per90')
ax2.set_ylabel('')

# shots_on_target_against_per90
sns.barplot(x=df_GK_bar3["gk_shots_on_target_against_per90"], y=df_GK_bar3.index, orient="h", 
            palette=[highlight_color if c == HIGHLIGHT_TEAM else base_color for c in df_GK_bar3.index], ax=ax3)
ax3.set_title('유효슈팅 허용 (개/90min) ↓')
ax3.set_xlabel('gk_shots_on_target_against_per90')
ax3.set_ylabel('')

# saves_per90
sns.barplot(x=df_GK_bar4["gk_saves_per90"], y=df_GK_bar4.index, orient="h", 
            palette=[highlight_color if c == HIGHLIGHT_TEAM else base_color for c in df_GK_bar4.index], ax=ax4)
ax4.set_title('선방 (개/90min)')
ax4.set_xlabel('gk_saves_per90')
ax4.set_ylabel('')

# 전체 제목 설정 및 출력
fig.suptitle('Argentina GK 관련 지표', fontsize=20)
plt.tight_layout()
plt.show()


### 5-2-2. Argentina GK 지표별 순위 선그래프
# 라벨, 값 설정
GK_labels = ['save_pct', 'goals_against(↓)', 'shots_on_target_against(↓)', 'saves']
GK_ranks = [GK_rank1, GK_rank2, GK_rank3, GK_rank4]

# 선 그래프 그리기
fig, ax = plt.subplots(figsize=(10, 10))
ax.plot(GK_labels, GK_ranks, color=highlight_color, linewidth=3, marker='o', markersize=8)
ax.set_title('Argentina GK 지표별 순위', fontsize=20)
ax.set_ylabel('Rank')
ax.set_ylim(1, 32)
ax.invert_yaxis()
ax.set_yticks([1, 5, 10, 15, 20, 25, 30])

# 데이터레이블 출력
for x, y in zip(GK_labels, GK_ranks):
    ax.annotate(
    f'{y}', (x, y),
    textcoords="offset points", xytext=(0, 10),
    ha='center'
    )

# 배경 무늬 설정 및 출력
plt.grid(True, axis='y', alpha=0.5)
plt.tight_layout()
plt.show()



########## 6. 파일 내보내기 ##########
# 6-1. 전체 데이터
df_total.to_csv('df_total.csv', index=False, encoding='utf-8-sig')
df_keep.to_csv('df_keep.csv', index=False, encoding='utf-8-sig')

# 6-2. 수비수 데이터
df_DF.to_csv('df_DF.csv', index=False, encoding='utf-8-sig')
df_DF_team.to_csv('df_DF_team.csv', index=False, encoding='utf-8-sig')

# 6-3. 미드필더 데이터
df_MF.to_csv('df_MF.csv', index=False, encoding='utf-8-sig')
df_MF_team.to_csv('df_MF_team.csv', index=False, encoding='utf-8-sig')

# 6-4. 공격수 데이터
df_FW.to_csv('df_FW.csv', index=False, encoding='utf-8-sig')
df_FW_team.to_csv('df_FW_team.csv', index=False, encoding='utf-8-sig')

# 6-5. 골키퍼 데이터
df_GK.to_csv('df_GK.csv', index=False, encoding='utf-8-sig')
df_GK_team.to_csv('df_GK_team.csv', index=False, encoding='utf-8-sig')
