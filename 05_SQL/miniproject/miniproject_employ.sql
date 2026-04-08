use mini;

SET FOREIGN_KEY_CHECKS = 0;

/*
alter table participation_rate add column region_id int first;

update participation_rate
set region_id = case
	when region = '서울특별시' then concat(year,01)
	when region = '부산광역시' then concat(year,02)
	when region = '대구광역시' then concat(year,03)
	when region = '인천광역시' then concat(year,04)
	when region = '광주광역시' then concat(year,05)
	when region = '대전광역시' then concat(year,06)
	when region = '울산광역시' then concat(year,07)
	when region = '세종특별자치시' then concat(year,08)
	when region = '경기도' then concat(year,09)
	when region = '강원특별자치도' then concat(year,10)
	when region = '충청북도' then concat(year,11)
	when region = '충청남도' then concat(year,12)
	when region = '전북특별자치도' then concat(year,13)
	when region = '전라남도' then concat(year,14)
	when region = '경상북도' then concat(year,15)
	when region = '경상남도' then concat(year,16)
	when region = '제주도' then concat(year,17)
end;

alter table employment_rate add column region_id int first;

update employment_rate
set region_id = case
	when region = '서울특별시' then concat(year,01)
	when region = '부산광역시' then concat(year,02)
	when region = '대구광역시' then concat(year,03)
	when region = '인천광역시' then concat(year,04)
	when region = '광주광역시' then concat(year,05)
	when region = '대전광역시' then concat(year,06)
	when region = '울산광역시' then concat(year,07)
	when region = '세종특별자치시' then concat(year,08)
	when region = '경기도' then concat(year,09)
	when region = '강원특별자치도' then concat(year,10)
	when region = '충청북도' then concat(year,11)
	when region = '충청남도' then concat(year,12)
	when region = '전북특별자치도' then concat(year,13)
	when region = '전라남도' then concat(year,14)
	when region = '경상북도' then concat(year,15)
	when region = '경상남도' then concat(year,16)
	when region = '제주도' then concat(year,17)
end;

alter table unemployment_rate add column region_id int first;

update unemployment_rate
set region_id = case
	when region = '서울특별시' then concat(year,01)
	when region = '부산광역시' then concat(year,02)
	when region = '대구광역시' then concat(year,03)
	when region = '인천광역시' then concat(year,04)
	when region = '광주광역시' then concat(year,05)
	when region = '대전광역시' then concat(year,06)
	when region = '울산광역시' then concat(year,07)
	when region = '세종특별자치시' then concat(year,08)
	when region = '경기도' then concat(year,09)
	when region = '강원특별자치도' then concat(year,10)
	when region = '충청북도' then concat(year,11)
	when region = '충청남도' then concat(year,12)
	when region = '전북특별자치도' then concat(year,13)
	when region = '전라남도' then concat(year,14)
	when region = '경상북도' then concat(year,15)
	when region = '경상남도' then concat(year,16)
	when region = '제주도' then concat(year,17)
end;
*/

alter table participation_rate drop column region_id;
alter table employment_rate drop column region_id;
alter table unemployment_rate drop column region_id;
alter table employ_id drop column id;

DROP TABLE employ_id;

DELETE FROM participation_rate WHERE year = 2025;
DELETE FROM employment_rate    WHERE year = 2025;
DELETE FROM unemployment_rate  WHERE year = 2025;

update employ_id
set region='제주특별자치도' where region='제주도';
update participation_rate
set region='제주특별자치도' where region='제주도';
update employment_rate
set region='제주특별자치도' where region='제주도';
update unemployment_rate
set region='제주특별자치도' where region='제주도';

alter table participation_rate add column region_id int first;
update participation_rate
set region_id = case
	when region = '강원특별자치도' then concat(year,01)
	when region = '경기도' then concat(year,02)
	when region = '경상남도' then concat(year,03)
	when region = '경상북도' then concat(year,04)
	when region = '광주광역시' then concat(year,05)
	when region = '대구광역시' then concat(year,06)
	when region = '대전광역시' then concat(year,07)
	when region = '부산광역시' then concat(year,08)
	when region = '서울특별시' then concat(year,09)
	when region = '세종특별자치시' then concat(year,10)
	when region = '울산광역시' then concat(year,11)
	when region = '인천광역시' then concat(year,12)
	when region = '전국' then concat(year,13)
	when region = '전라남도' then concat(year,14)
	when region = '전북특별자치도' then concat(year,15)
	when region = '제주특별자치도' then concat(year,16)
	when region = '충청남도' then concat(year,17)
	when region = '충청북도' then concat(year,18)	
end;

alter table employment_rate add column region_id int first;
update employment_rate
set region_id = case
	when region = '강원특별자치도' then concat(year,01)
	when region = '경기도' then concat(year,02)
	when region = '경상남도' then concat(year,03)
	when region = '경상북도' then concat(year,04)
	when region = '광주광역시' then concat(year,05)
	when region = '대구광역시' then concat(year,06)
	when region = '대전광역시' then concat(year,07)
	when region = '부산광역시' then concat(year,08)
	when region = '서울특별시' then concat(year,09)
	when region = '세종특별자치시' then concat(year,10)
	when region = '울산광역시' then concat(year,11)
	when region = '인천광역시' then concat(year,12)
	when region = '전국' then concat(year,13)
	when region = '전라남도' then concat(year,14)
	when region = '전북특별자치도' then concat(year,15)
	when region = '제주특별자치도' then concat(year,16)
	when region = '충청남도' then concat(year,17)
	when region = '충청북도' then concat(year,18)	
end;

alter table unemployment_rate add column region_id int first;
update unemployment_rate
set region_id = case
	when region = '강원특별자치도' then concat(year,01)
	when region = '경기도' then concat(year,02)
	when region = '경상남도' then concat(year,03)
	when region = '경상북도' then concat(year,04)
	when region = '광주광역시' then concat(year,05)
	when region = '대구광역시' then concat(year,06)
	when region = '대전광역시' then concat(year,07)
	when region = '부산광역시' then concat(year,08)
	when region = '서울특별시' then concat(year,09)
	when region = '세종특별자치시' then concat(year,10)
	when region = '울산광역시' then concat(year,11)
	when region = '인천광역시' then concat(year,12)
	when region = '전국' then concat(year,13)
	when region = '전라남도' then concat(year,14)
	when region = '전북특별자치도' then concat(year,15)
	when region = '제주특별자치도' then concat(year,16)
	when region = '충청남도' then concat(year,17)
	when region = '충청북도' then concat(year,18)	
end;

alter table employ_id add column region_id int first;
update employ_id
set region_id = case
	when region = '강원특별자치도' then concat(year,01)
	when region = '경기도' then concat(year,02)
	when region = '경상남도' then concat(year,03)
	when region = '경상북도' then concat(year,04)
	when region = '광주광역시' then concat(year,05)
	when region = '대구광역시' then concat(year,06)
	when region = '대전광역시' then concat(year,07)
	when region = '부산광역시' then concat(year,08)
	when region = '서울특별시' then concat(year,09)
	when region = '세종특별자치시' then concat(year,10)
	when region = '울산광역시' then concat(year,11)
	when region = '인천광역시' then concat(year,12)
	when region = '전국' then concat(year,13)
	when region = '전라남도' then concat(year,14)
	when region = '전북특별자치도' then concat(year,15)
	when region = '제주특별자치도' then concat(year,16)
	when region = '충청남도' then concat(year,17)
	when region = '충청북도' then concat(year,18)	
end;

select emp.region, emp.year, emp.employment_rate, unemp.unemployment_rate, par.participation_rate, empty2.empty_rate
from employment_rate as emp 
	inner join unemployment_rate as unemp on emp.region_id = unemp.region_id
	inner join participation_rate as par on unemp.region_id = par.region_id
	inner join empty2 on par.region_id = empty2.region_id;

alter table mini.employment_rate drop primary key;
alter table mini.unemployment_rate drop primary key;
alter table mini.participation_rate drop primary key;

select year, avg(employment_rate) as employment_avg
from employment_rate
group by year;

select year, avg(unemployment_rate) as unemployment_avg
from unemployment_rate
group by year;

select year, avg(participation_rate) as participation_avg
from participation_rate
group by year;

select year, avg(empty_rate) as empty_avg
from empty2
where year between '2018' and '2024'
group by year;
