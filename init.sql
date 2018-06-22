create table if not exists close_vacancies
(
  id serial primary key,
  vacancy_id integer,
  vacancy_name varchar(500),
  vacancy_salary_from integer,
  vacancy_salary_to integer,
  vacancy_experience varchar(6),
  vacancy_published_at timestamptz,
  vacancy_closed_at timestamptz default current_timestamp,
  vacancy_raw_data json
);

create table if not exists close_vacancies_specializations
(
  id serial primary key,
  vacancy_id integer,
  vacancy_specialization varchar(1000)
);