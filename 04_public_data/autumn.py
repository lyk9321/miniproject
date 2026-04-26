# 기후변화가 사계절을 알리는 자연 지표에 미치는 영향

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib as mpl
import seaborn as sns
import koreanize_matplotlib
from tabulate import tabulate
from datetime import timedelta

##### 가을(입추~입동 전날): 08/07 -> 11/06 #####

#################################
########## 데이터 전처리 ##########
#################################

##### 1. 단풍, 은행나무 시작 시기 데이터 전처리 #####
df = pd.read_csv('autumn.csv', encoding='euc-kr', header=[0, 1])

df.columns = [
    'year',
    'yellow_start', 'yellow_start_diff',
    'yellow_peak',  'yellow_peak_diff',
    'maple_start',  'maple_start_diff',
    'maple_peak',   'maple_peak_diff',]

df_autumn = df[['year', 'yellow_start', 'maple_start']].copy()

df_autumn['yellow_start'] = pd.to_datetime(df_autumn['yellow_start'])
df_autumn['maple_start']  = pd.to_datetime(df_autumn['maple_start'])
#print(tabulate(df_autumn, headers='keys', tablefmt='psql'))
#print(df_autumn)
#print(df_autumn.info())


##### 2. 기온 데이터 전처리 #####
df2 = pd.read_csv('temp04.csv', encoding='euc-kr')
df2['날짜'] = pd.to_datetime(df2['날짜'])

df_temp = df2[['날짜', '평균기온(℃)']].copy()
df_temp.columns = ['date', 'temp_avg']

# 8/7 ~ 11/6 날짜 설정
m = df_temp['date'].dt.month
d = df_temp['date'].dt.day
autumn_temp_period = ((m == 8) & (d >= 7)) | (m == 9) | (m == 10) | ((m == 11) & (d <= 6))
df_temp_period = df_temp.loc[autumn_temp_period].copy()

# 연도별 평균 기온
yearly_temp_avg = df_temp_period.groupby(df_temp_period['date'].dt.year)['temp_avg'].mean().round(2)
#print(yearly_temp_avg)
#print(yearly_temp_avg.info())

##### 3. 강수량 데이터 전처리 #####
df3 = pd.read_csv('rain02.csv', encoding='euc-kr')
df3['날짜'] = pd.to_datetime(df3['날짜'])

df_rain = df3.drop(columns=['지점']).copy()
df_rain.columns = ['date', 'rain_avg']

# 8/7 ~ 11/6 날짜 설정
m = df_rain['date'].dt.month
d = df_rain['date'].dt.day
autumn_rain_period = ((m == 8) & (d >= 7)) | (m == 9) | (m == 10) | ((m == 11) & (d <= 6))
df_rain_period = df_rain.loc[autumn_rain_period].copy()

# 연도별 평균 강수량
yearly_rain_avg = df_rain_period.groupby(df_rain_period['date'].dt.year)['rain_avg'].mean().round(2)
#print(yearly_rain_avg)
#print(yearly_rain_avg.info())

###############################
########## 데이터 병합 ##########
###############################

##### 1. 기온 + 강수량 = df_year_data #####
df_year_data = pd.merge(yearly_temp_avg, yearly_rain_avg, how='inner', on='date')
df_year_data = df_year_data.reset_index().rename(columns={'date': 'year'})
#print(tabulate(df_year_data, headers='keys', tablefmt='psql'))
#print(df_year_data.info())

# df_autumn에 맞춰 1989년 ~ 2019년 자르기
df_year_data = df_year_data[(df_year_data['year'] >= 1989) & (df_year_data['year'] <= 2019)].sort_values('year')
#print(df_year_data)

##### 2-1. 단풍 + 기온 = df_maple_temp #####
df_maple_temp = pd.merge(df_autumn[['year', 'maple_start']], df_year_data[['year', 'temp_avg']], on='year', how='inner')
#print(df_maple_temp.info())

##### 2-2. 단풍 + 강수량 = df_maple_rain #####
df_maple_rain = pd.merge(df_autumn[['year', 'maple_start']], df_year_data[['year', 'rain_avg']], on='year', how='inner')
#print(df_maple_rain.info())

##### 3-1. 은행 + 기온 = df_yellow_temp #####
df_yellow_temp = pd.merge(df_autumn[['year', 'yellow_start']], df_year_data[['year', 'temp_avg']], on='year', how='inner')
#print(df_yellow_temp.info())

##### 3-2. 은행 + 강수량 = df_yellow_rain #####
df_yellow_rain = pd.merge(df_autumn[['year', 'yellow_start']], df_year_data[['year', 'rain_avg']], on='year', how='inner')
#print(df_yellow_rain.info())

##### 4. 기온 + 강수량 + 단풍 + 은행 = df_total #####
df_total = pd.merge(df_autumn, df_year_data, on='year', how='inner')
#print(tabulate(df_total, headers='keys', tablefmt='psql'))


###############################
########## 데이터 분석 ##########
###############################

# df_total로 전체 상관계수 계산하기
df_total_corr = df_total.copy()

# 날짜 -> 연중일수(DOY) 변환
df_total_corr['yellow_doy'] = df_total_corr['yellow_start'].dt.dayofyear
df_total_corr['maple_doy'] = df_total_corr['maple_start'].dt.dayofyear

# 상관계수에 사용할 컬럼만 선택 (숫자)
df_corr_cols = ['temp_avg', 'rain_avg', 'yellow_doy', 'maple_doy']
df_corr = df_total_corr[df_corr_cols].corr()

#print(df_corr)


#################################
########## 데이터 시각화 ##########
#################################

##### 0. 화질 설정: 고화질 #####

mpl.rcParams['figure.dpi'] = 100
mpl.rcParams['savefig.dpi'] = 600

##### 1. 기온(선) + 강수량(막대) 그래프 #####

fig, ax1 = plt.subplots(figsize=(16, 5))

# 기온(선 그래프) - 왼쪽 축
ax1.plot(df_year_data['year'], df_year_data['temp_avg'], label='3개월 평균 기온(℃)', color='indigo', marker='o', linewidth=2)
ax1.set_xlabel('연도')
ax1.set_ylabel('평균 기온(℃)')
ax1.set_xticks(df_year_data['year'])
ax1.set_xlim(df_year_data['year'].min() - 1, df_year_data['year'].max() + 1)
ax1.tick_params(axis="x", labelrotation=90)

# 강수량(막대 그래프) - 오른쪽 축
ax2 = ax1.twinx()
ax2.bar(df_year_data['year'], df_year_data['rain_avg'], label='3개월 평균 강수량(mm)', color='indigo', alpha=0.3)
ax2.set_ylabel('강수량(mm)')

# 범례 합치기
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)

plt.title('가을(입추~입동) 3개월 평균 기온 & 평균 강수량', fontsize=16)
plt.tight_layout()
plt.show()


##### 2-1. 단풍 시작 + 기온 그래프 #####

### 2-1-1. 단풍 시작(선) + 기온(선) 그래프 ###

# df_maple_temp 기준으로 사용
df_maple = df_maple_temp.copy()

# y축에 연도 표시 없애기: 월-일만 남기기 위해 기준연도 부여
base_year = 2001
df_maple['maple_md'] = df_maple['maple_start'].apply(lambda dt: pd.Timestamp(base_year, dt.month, dt.day))

# 2축 선 그래프 그리기
fig, ax1 = plt.subplots(figsize=(16, 5))

ax1.plot(df_maple['year'], df_maple['maple_md'], color='red', marker='o', linewidth=2, label='단풍 시작일')
ax1.set_xlabel('연도')
ax1.set_ylabel('단풍 시작일(월-일)')

# y축 범위(10월 1일 ~ 11월 15일)
start = pd.Timestamp(base_year, 10, 1)
end = pd.Timestamp(base_year, 11, 15)
ax1.set_ylim(start, end)

# y축 ticks: 10월 1일부터 7일 간격으로 표시
ticks = pd.date_range(start, end, freq='7D')
ax1.set_yticks(ticks)
ax1.yaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))

# 보조축: 기온 그래프
ax2 = ax1.twinx()
ax2.plot(df_maple['year'], df_maple['temp_avg'], color='indigo', marker='s', linewidth=2, label='3개월 평균 기온(℃)')
ax2.set_ylabel('평균 기온(℃)')

# x축 설정
ax1.set_xticks(df_maple['year'])
ax1.tick_params(axis='x', labelrotation=90)
ax1.set_xlim(df_maple['year'].min() - 1, df_maple['year'].max() + 1)

# 배경 격자 무늬 설정
ax1.grid( axis='y', color='gray', linestyle='-', alpha=0.3)

# 범례: 하단 중앙 바깥
h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=2)

plt.title('단풍 시작일 - 가을 평균 기온', fontsize=16)
plt.tight_layout()
plt.show()

### 2-1-2. 단풍 시작 + 기온 산점도 그래프 ###
plt.figure(figsize=(7, 5))
sns.regplot(data=df_total_corr, x='temp_avg', y='maple_doy', scatter_kws={'alpha': 0.7, 'color': 'tomato'}, line_kws={'linewidth': 2, 'color': 'darkred'})
plt.title('단풍 시작 시기 vs 평균 기온', fontsize=16)
plt.xlabel('평균 기온(℃)')
plt.ylabel('단풍 시작시기(DOY)')
plt.tight_layout()
plt.show()


##### 2-2. 단풍 시작 + 강수량 그래프 #####
### 2-2-1. 단풍 시작(선) + 강수량(선) 그래프 ###

df_maple = df_maple_rain.copy()

base_year = 2001
df_maple['maple_md'] = df_maple['maple_start'].apply(lambda dt: pd.Timestamp(base_year, dt.month, dt.day))

fig, ax1 = plt.subplots(figsize=(16, 5))

ax1.plot(df_maple['year'], df_maple['maple_md'], color='red', marker='o', linewidth=2, label='단풍 시작일')
ax1.set_xlabel('연도')
ax1.set_ylabel('단풍 시작일(월-일)')

start = pd.Timestamp(base_year, 10, 1)
end = pd.Timestamp(base_year, 11, 15)
ax1.set_ylim(start, end)

ticks = pd.date_range(start, end, freq='7D')
ax1.set_yticks(ticks)
ax1.yaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))

ax2 = ax1.twinx()
ax2.plot(df_maple['year'], df_maple['rain_avg'], color='indigo', marker='s', linewidth=2, label='3개월 평균 강수량(mm)')
ax2.set_ylabel('강수량(mm)')

ax1.set_xticks(df_maple['year'])
ax1.tick_params(axis='x', labelrotation=90)
ax1.set_xlim(df_maple['year'].min() - 1, df_maple['year'].max() + 1)

ax1.grid( axis='y', color='gray', linestyle='-', alpha=0.3)

h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=2)

plt.title('단풍 시작일 - 가을 평균 강수량', fontsize=16)
plt.tight_layout()
plt.show()

### 2-2-2. 단풍 시작 + 강수량 산점도 그래프 ###
plt.figure(figsize=(7, 5))
sns.regplot(data=df_total_corr, x='rain_avg', y='maple_doy', scatter_kws={'alpha': 0.7, 'color': 'tomato'}, line_kws={'linewidth': 2, 'color': 'darkred'})
plt.title('단풍 시작 시기 vs 평균 강수량', fontsize=16)
plt.xlabel('평균 강수량(mm)')
plt.ylabel('단풍 시작 시기(DOY)')
plt.tight_layout()
plt.show()


##### 3-1. 은행 시작 + 기온 그래프 #####
### 3-1-1. 은행 시작(선) + 기온(선) 그래프 ##3
df_yellow = df_yellow_temp.copy()

base_year = 2001
df_yellow['yellow_md'] = df_yellow['yellow_start'].apply(lambda dt: pd.Timestamp(base_year, dt.month, dt.day))

fig, ax1 = plt.subplots(figsize=(16, 5))

ax1.plot(df_yellow['year'], df_yellow['yellow_md'], color='darkgoldenrod', marker='o', linewidth=2, label='은행 시작일')
ax1.set_xlabel('연도')
ax1.set_ylabel('은행 시작일(월-일)')

start = pd.Timestamp(base_year, 10, 1)
end = pd.Timestamp(base_year, 11, 15)
ax1.set_ylim(start, end)

ticks = pd.date_range(start, end, freq='7D')
ax1.set_yticks(ticks)
ax1.yaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))

ax2 = ax1.twinx()
ax2.plot(df_yellow['year'], df_yellow['temp_avg'], color='indigo', marker='s', linewidth=2, label='3개월 평균 기온(℃)')
ax2.set_ylabel('평균 기온(℃)')

ax1.set_xticks(df_yellow['year'])
ax1.tick_params(axis='x', labelrotation=90)
ax1.set_xlim(df_yellow['year'].min() - 1, df_yellow['year'].max() + 1)

ax1.grid( axis='y', color='gray', linestyle='-', alpha=0.3)

h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=2)

plt.title('은행 시작일 - 가을 평균 기온', fontsize=16)
plt.tight_layout()
plt.show()


### 3-1-2. 은행 시작 + 기온 산점도 그래프 ###
plt.figure(figsize=(7, 5))
sns.regplot(data=df_total_corr, x='temp_avg', y='yellow_doy', scatter_kws={'alpha': 0.7, 'color': 'darkgoldenrod'}, line_kws={'linewidth': 2, 'color': 'goldenrod'})
plt.title('은행 시작 시기 vs 평균 기온', fontsize=16)
plt.xlabel('평균 기온(℃)')
plt.ylabel('은행 시작 시기(DOY)')
plt.tight_layout()
plt.show()


##### 3-2. 은행 시작 + 강수량 그래프 #####
### 3-2-1. 은행 시작(선) + 강수량(선) 그래프 ###
df_yellow = df_yellow_rain.copy()

base_year = 2001
df_yellow['yellow_md'] = df_yellow['yellow_start'].apply(lambda dt: pd.Timestamp(base_year, dt.month, dt.day))

fig, ax1 = plt.subplots(figsize=(16, 5))

ax1.plot(df_yellow['year'], df_yellow['yellow_md'], color='darkgoldenrod', marker='o', linewidth=2, label='은행 시작일')
ax1.set_xlabel('연도')
ax1.set_ylabel('은행 시작일(월-일)')

start = pd.Timestamp(base_year, 10, 1)
end = pd.Timestamp(base_year, 11, 15)
ax1.set_ylim(start, end)

ticks = pd.date_range(start, end, freq='7D')
ax1.set_yticks(ticks)
ax1.yaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))

ax2 = ax1.twinx()
ax2.plot(df_yellow['year'], df_yellow['rain_avg'], color='indigo', marker='s', linewidth=2, label='3개월 평균 강수량(mm)')
ax2.set_ylabel('강수량(mm)')

ax1.set_xticks(df_yellow['year'])
ax1.tick_params(axis='x', labelrotation=90)
ax1.set_xlim(df_yellow['year'].min() - 1, df_yellow['year'].max() + 1)

ax1.grid( axis='y', color='gray', linestyle='-', alpha=0.3)

h1, l1 = ax1.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=2)

plt.title('은행 시작일 - 가을 평균 강수량', fontsize=16)
plt.tight_layout()
plt.show()


### 3-2-2. 은행 시작 + 강수량 산점도 그래프 ###
plt.figure(figsize=(7, 5))
sns.regplot(data=df_total_corr, x='rain_avg', y='yellow_doy', scatter_kws={'alpha': 0.7, 'color': 'darkgoldenrod'}, line_kws={'linewidth': 2, 'color': 'goldenrod'})
plt.title('은행 시작 시기 vs 평균 강수량', fontsize=16)
plt.xlabel('평균 강수량(mm)')
plt.ylabel('은행 시작 시기(DOY)')
plt.tight_layout()
plt.show()


##### 4. 상관계수 히트맵 #####

# 한글 라벨 매핑
label = {
    'temp_avg': '평균 기온',
    'rain_avg': '평균 강수량',
    'yellow_doy': '은행 시작일',
    'maple_doy': '단풍 시작일'
}

# df_corr의 인덱스/컬럼명을 한글로 바꿈
df_corr_kr = df_corr.rename(index=label, columns=label)

plt.figure(figsize=(7, 6))
sns.heatmap(df_corr_kr, annot=True, fmt='.2f', vmin=-1, vmax=1, center=0, cmap='RdBu_r', square=True, linewidths=0.5)

plt.title('가을 기후 지표, 자연 지표 상관계수', fontsize=16)
plt.tight_layout()
plt.show()
