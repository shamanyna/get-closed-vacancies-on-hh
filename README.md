# get-closed-vacancies-on-hh
get closed vacancies on hh.ru and save it into postgresql for analysis

in work directory will create two folders:
- loader/data  for data file and log file of service
- postgresql/data for database that saving close vacancies data

postgresql has default database an user (without password)

in database create two tables:

- close_vacancies_specializations
    - id primary key,
    - vacancy_id integer, -- vacancy id from hh
    - vacancy_specialization -- vacancy specialization from hh dictionary

- close_vacancies
    - id serial primary key,
    - vacancy_id, -- vacancy id from hh
    - vacancy_name, -- vacancy name from hh
    - vacancy_salary_from, -- min salary (convert to RUR currency and net from gross and rounded to the nearest whole)
    - vacancy_salary_to, -- max salary (convert to RUR currency and net from gross and rounded to the nearest whole)
    - vacancy_experience, -- category of experience
    - vacancy_published_at, -- date published on hh
    - vacancy_closed_at, -- date close vacancy (as date save to database)
    - vacancy_raw_data -- raw vacancy data as json

vacancies data database located in host in ./postgresql/data folder

loader service execute with scheduler in minutes interval
default interval = 1 minute
the interval can be specified as the environment variable at startup:

example of default behavior:
- docker-compose up --build

example set environment variable (loader will run with 2 minutes interval):
- SCHEDULE_MINUTES_INTERVAL=2 docker-compose up --build
