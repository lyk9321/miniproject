# 빈집 수에 영향을 미치는 요소

import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib
import pymysql
from tabulate import tabulate

##### 1. 데이터베이스 불러오기 #####
# 데이터 전처리는 MySQL에서 완료
# MySQL 연결
conn = pymysql.connect(host='172.30.1.4',
                       user='lyk',
                       password='1234',
                       database='mini',
                       charset='utf8')

cur = conn.cursor(pymysql.cursors.DictCursor)

### 0. employ_id 불러오기
cur.execute('select * from employ_id')
rows_employ_id = cur.fetchall()
df_employ_id = pd.DataFrame(rows_employ_id)
#print(df_employ_id)

### 1-1-1. participation_rate 불러오기
cur.execute('select * from participation_rate')
rows_participation_rate = cur.fetchall()
df_participation_rate = pd.DataFrame(rows_participation_rate)
#print(df_participation_rate)

### 1-1-2. participation_avg 계산해서 불러오기
q1 = """select year, avg(participation_rate) as participation_avg
from participation_rate
group by year"""
cur.execute(q1)
rows_participation_avg = cur.fetchall()
df_participation_avg = pd.DataFrame(rows_participation_avg)
#print(df_participation_avg)

### 1-2-1. employment_rate 불러오기
cur.execute('select * from employment_rate')
rows_employment_rate = cur.fetchall()
df_employment_rate = pd.DataFrame(rows_employment_rate)
#print(df_employment_rate)

### 1-2-2. employment_avg 계산해서 불러오기
q2 = """select year, avg(employment_rate) as employment_avg
from employment_rate
group by year"""
cur.execute(q2)
rows_employment_avg = cur.fetchall()
df_employment_avg = pd.DataFrame(rows_employment_avg)
#print(df_employment_avg)

### 1-3-1. unemployment_rate 불러오기
cur.execute('select * from unemployment_rate')
rows_unemployment_rate = cur.fetchall()
df_unemployment_rate = pd.DataFrame(rows_unemployment_rate)
#print(df_unemployment_rate)

### 1-3-2. unemployment_avg 계산해서 불러오기
q3 = """select year, avg(unemployment_rate) as unemployment_avg
from unemployment_rate
group by year"""
cur.execute(q3)
rows_unemployment_avg = cur.fetchall()
df_unemployment_avg = pd.DataFrame(rows_unemployment_avg)
#print(df_unemployment_avg)

### 1-4-1. empty2(빈집 데이터) 불러오기
cur.execute('select * from empty2')
rows_empty_house = cur.fetchall()
df_empty_house = pd.DataFrame(rows_empty_house)
#print(df_empty_house)

### 1-4-2. empty_avg 계산해서 불러오기
q4 = """select year, avg(empty_rate) as empty_avg
from empty2
where year between '2018' and '2024'
group by year"""
cur.execute(q4)
rows_empty_avg = cur.fetchall()
df_empty_avg = pd.DataFrame(rows_empty_avg)
print(df_empty_avg)

### 1-5. 전체(빈집, 고용 지표) 합친 데이터
query = """
select emp.region, emp.year, emp.employment_rate, unemp.unemployment_rate, par.participation_rate, empty2.empty_rate
from employment_rate as emp 
	inner join unemployment_rate as unemp on emp.region_id = unemp.region_id
	inner join participation_rate as par on unemp.region_id = par.region_id
	inner join empty2 on par.region_id = empty2.region_id"""

cur.execute(query)
rows_total = cur.fetchall()
total = pd.DataFrame(rows_total) 

# 연결 종료
cur.close()
conn.close()

##### 2. 데이터 분석 #####
# 각 지표들 간 상관계수 계산
total_corr_cols = ['employment_rate', 'unemployment_rate', 'participation_rate', 'empty_rate']
total_corr = total[total_corr_cols].corr()
#print(tabulate(total_corr, headers='keys', tablefmt='psql'))

##### 3. 데이터 시각화 #####
### 0. 화질 설정 ###
mpl.rcParams['figure.dpi'] = 100
mpl.rcParams['savefig.dpi'] = 600

### 3-1. 연도별 빈집 비율 현황 
plt.figure(figsize=(12, 7))
sns.lineplot(x=df_empty_avg['year'], y=df_empty_avg['empty_avg'], linewidth=3, marker='o', markersize=10, color='cornflowerblue')
plt.xlabel('연도', fontsize=14)
plt.ylabel('빈집 비율(%)', fontsize=14)
plt.tick_params(axis='both', labelsize=12)
plt.title('2018-2024 연도별 빈집 비율', fontsize=20)
plt.grid(axis='y', color='gray', alpha=0.3)
plt.tight_layout()
plt.show()

### 3-2. 고용 지표 현황 막대 그래프
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
ax1, ax2, ax3 = axes

# 고용률
sns.barplot(x=df_employment_avg['year'], y=df_employment_avg['employment_avg'], ax=ax1, color='salmon', alpha=0.7)
ax1.set_title('고용률 현황')
ax1.set_xlabel('연도')
ax1.set_ylabel('고용률(%)')
ax1.set_ylim(df_employment_avg['employment_avg'].min() - 1, df_employment_avg['employment_avg'].max() + 1)

# 실업률
sns.barplot(x=df_unemployment_avg['year'], y=df_unemployment_avg['unemployment_avg'], ax=ax2, color='forestgreen', alpha=0.7)
ax2.set_title('실업률 현황')
ax2.set_xlabel('연도')
ax2.set_ylabel('실업률(%)')
ax2.set_ylim(df_unemployment_avg['unemployment_avg'].min() - 1, df_unemployment_avg['unemployment_avg'].max() + 1)

# 경제활동참가율
sns.barplot(x=df_participation_avg['year'], y=df_participation_avg['participation_avg'], ax=ax3, color='indigo', alpha=0.7)
ax3.set_title('경제활동참가율 현황')
ax3.set_xlabel('연도')
ax3.set_ylabel('경제활동참가율(%)')
ax3.set_ylim(df_participation_avg['participation_avg'].min() - 1, df_participation_avg['participation_avg'].max() + 1)

fig.suptitle('2018-2024년 고용 지표 현황', fontsize=20)
plt.tight_layout()
plt.show()

### 3-3. 빈집 비율-고용률 산점도 ###
emp_plot_df = total[['region', 'empty_rate', 'employment_rate']]
plt.figure(figsize=(7, 7))

# 지역별 색 산점도
sns.scatterplot(data=emp_plot_df, x='empty_rate', y='employment_rate', hue='region', palette='tab20', alpha=0.7, s=60)

# 전체 추세선
sns.regplot(data=emp_plot_df, x='empty_rate', y='employment_rate', scatter=False, ci=95, line_kws={'linewidth': 3, 'color': 'gray'})

plt.title('빈집 비율-고용률 산점도', fontsize=20)
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=4)
plt.tight_layout()
plt.show()

### 3-4. 빈집 비율-실업률 산점도 ###
emp_plot_df = total[['region', 'empty_rate', 'unemployment_rate']]
plt.figure(figsize=(7, 7))

# 지역별 색 산점도
sns.scatterplot(data=emp_plot_df, x='empty_rate', y='unemployment_rate', hue='region', palette='tab20', alpha=0.7, s=60)

# 전체 추세선
sns.regplot(data=emp_plot_df, x='empty_rate', y='unemployment_rate', scatter=False, ci=95, line_kws={'linewidth': 3, 'color': 'gray'})

plt.title('빈집 비율-실업률 산점도', fontsize=20)
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=4)
plt.tight_layout()
plt.show()

### 3-5. 빈집 비율-경제활동참가율 산점도 ###
emp_plot_df = total[['region', 'empty_rate', 'participation_rate']]
plt.figure(figsize=(7, 7))

# 지역별 색 산점도
sns.scatterplot(data=emp_plot_df, x='empty_rate', y='participation_rate', hue='region', palette='tab20', alpha=0.7, s=60)

# 전체 추세선
sns.regplot(data=emp_plot_df, x='empty_rate', y='participation_rate', scatter=False, ci=95, line_kws={'linewidth': 3, 'color': 'gray'})

plt.title('빈집 비율-경제활동참가율 산점도', fontsize=20)
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=4)
plt.tight_layout()
plt.show()

# 3-6. 상관계수 히트맵
# 한글 라벨 매핑
label = {'employment_rate': '고용률',
         'unemployment_rate': '실업률',
         'participation_rate': '경제활동참가율',
         'empty_rate': '빈집 비율'}

# df_corr의 인덱스/컬럼명을 한글로 바꿈
total_corr_heat = total_corr.rename(index=label, columns=label)

plt.figure(figsize=(7, 6))
sns.heatmap(total_corr_heat, annot=True, fmt='.2f', vmin=-1, vmax=1, center=0, cmap='RdBu_r', square=True, linewidths=0.5)

plt.title('빈집 비율-고용 지표 상관계수', fontsize=16)
plt.tight_layout()
plt.show()
