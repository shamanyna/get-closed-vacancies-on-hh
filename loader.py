
import requests
import psycopg2 as pg
import psycopg2.extras as pgex

import pickle
import logging
from _datetime import datetime
import threading
import json


def loader():
    """
    entrypoint
    """
    logging.basicConfig(filename='./loader/data/log.log', level=logging.INFO)

    threads = []
    open_vacancies_ids = []
    close_vacancies_ids = []
    close_vacancies = []
    close_vacancies_specializations = []

    def logger_inf(msg: str):
        """
        write INFO message into log file (append) with timestamp point
        :param msg: - message
        """
        timestamp = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        logging.info(timestamp + '\t' + msg)

    def logger_err(msg: str, ex: Exception):
        """
        write ERROR message into log file (append) with timestamp point
        :param msg: - message
        :param ex: - exception message
        """
        timestamp = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        logging.error(timestamp + '\t' + msg + '\t' + str(ex))

    def get_metro_from_hh(city_id: int) -> list:
        """
        get metro stations ids from api.hh
        :param city_id: - id of Saint-Petersburg city by api.hh dictionary
        :return: list of metro stations ids
        """
        url = 'https://api.hh.ru/metro/' + str(city_id)
        request = requests.get(url).json()

        stations = []
        for line in request['lines']:
            stations.extend([station['id'] for station in line['stations']])

        return stations

    def get_open_vacancies_from_hh(metro_id: str) -> list:
        """
        get open vacancies from api.hh for metro station
        :param metro_id: - metro stations id
        :return: - list of open vacancies ids
        """
        rows_count = rows_on_page = 100
        page = 0
        vacancies = []

        while rows_count == rows_on_page:
            url_parameters = {
                'host': 'hh.ru',
                'area': '2',
                'metro': metro_id,
                'industry': '7',
                'per_page': rows_on_page,
                'page': page
            }
            request = requests.get('https://api.hh.ru/vacancies', params=url_parameters).json()

            ovi = [int(vacancy['id']) for vacancy in request['items']]
            vacancies.extend(ovi)

            rows_count = len(ovi)
            page += 1

        return vacancies

    def get_close_vacancy_from_hh(close_vacancy_id: int) -> object:
        """
        get vacancy data from api.hh by vacancy id (using for get close vacancy by its id)
        :param close_vacancy_id: - close vacancy id
        :return: - vacancy data in json format
        """
        return requests.get('https://api.hh.ru/vacancies/' + str(close_vacancy_id)).json()

    def get_experience_description() -> str:
        """
        get experience description from api.hh and normalise its name by categories
        :return: - experience category name
        """
        experience = close_vacancy_data['experience']['id']
        return {
            experience == 'noExperience': 'junior',
            experience == 'between1And3': 'middle',
            experience == 'between3And6': 'senior',
            experience == 'moreThan6': 'expert'
        }[True]

    def get_close_vacancy_name() -> str:
        """
        get close vacancy name
        """
        return close_vacancy_data['name']

    def get_conversion_multiplications() -> float:
        """
        get conversion multiplier for convert vacancy salary from its currency to RUR
        and deducts tax if vacancy has [gross] attribute is true
        """
        currency = close_vacancy_data['salary']['currency']
        gross = close_vacancy_data['salary']['gross']
        return {
            currency == 'USD': 63,
            currency == 'USD' and gross: 0.87 * 63,
            currency == 'EUR': 73,
            currency == 'EUR' and gross: 0.87 * 73,
            currency == 'RUR': 1,
            currency == 'RUR' and gross: 0.87
        }[True]

    def get_close_vacancy_salary(salary_type: str) -> int:
        """
        calculate vacancy salary with conversion multiplier and rounding up to a whole
        :param salary_type: - one of ('from', 'to') salary type. 'from' type is min salary and 'to' type is max salary.
        """
        if close_vacancy_data['salary'] is not None:
            if salary_type == 'from' and close_vacancy_data['salary']['from'] is not None:
                return int(close_vacancy_data['salary']['from'] * get_conversion_multiplications())
            elif salary_type == 'to' and close_vacancy_data['salary']['to'] is not None:
                return int(close_vacancy_data['salary']['to'] * get_conversion_multiplications())
            else:
                return 0
        else:
            return 0

    def get_close_vacancy_date() -> str:
        """
        get close vacancy published date in YYYY-MM-DD hh:mm:ss+TZ format
        """
        return close_vacancy_data['published_at']

    def get_close_vacancy_specializations(close_vacancy_id: int) -> tuple:
        """
        get close vacancy specializations
        :param close_vacancy_id: - close vacancy id
        :return: list of unique tuples, specializations with vacancy id as key
        """
        return list(set(
            [(close_vacancy_id, specialization['name']) for specialization in close_vacancy_data['specializations']]
        ))

    def save_data_to_database(close_vacancies_specializations: list, close_vacancies: list):
        """
        save close vacancies data to databases
        :param close_vacancies_specializations: - list of tuples [(vacancy_id, specialization)]
        :param close_vacancies:  - list of tuples of vacancy data [((id, name, salary_from, salary_to, experience, published_at, json))]
        """
        with pg.connect(dbname='postgres', user='postgres', host='localhost', port='5432') as conn:
            with conn.cursor() as cur:
                insert_query = 'insert into close_vacancies_specializations ' \
                               '(vacancy_id, vacancy_specialization) ' \
                               'values %s'
                pgex.execute_values(cur, insert_query, close_vacancies_specializations, page_size=100)
            with conn.cursor() as cur:
                insert_query = 'insert into close_vacancies ' \
                               '(' \
                               'vacancy_id, ' \
                               'vacancy_name, ' \
                               'vacancy_salary_from, ' \
                               'vacancy_salary_to, ' \
                               'vacancy_experience, ' \
                               'vacancy_published_at, ' \
                               'vacancy_raw_data' \
                               ') ' \
                               'values %s'
                pgex.execute_values(cur, insert_query, close_vacancies, page_size=100)

        conn.close()


    logger_inf('Start')

    for metro in get_metro_from_hh(2):
        t = threading.Thread(target=open_vacancies_ids.extend(get_open_vacancies_from_hh(metro)))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    logger_inf('Received all open vacancies')

    sovi = set(open_vacancies_ids)

    try:
        with open('./loader/data/data.open_vacancies_ids', 'rb') as data_old:
            open_vacancies_ids_old = pickle.load(data_old)
        close_vacancies_ids = [vacancy_id for vacancy_id in open_vacancies_ids_old if vacancy_id not in sovi]
    except IOError as e:
        logger_err('Can not load saved old open vacancies file: ', e)


    # ---------------------------------------
    if not close_vacancies_ids:
        close_vacancies_ids.append(23696436)
        # salary test
        # close_vacancies_ids.append(26449543)
    # ---------------------------------------

    if close_vacancies_ids:
        try:
            logger_inf('Closed vacancies data processing')

            for close_vacancy_id in close_vacancies_ids:
                close_vacancy_data = get_close_vacancy_from_hh(close_vacancy_id)

                # data = (id, name, salary_from, salary_to, experience, published_at, json)
                data = (
                    close_vacancy_id,
                    get_close_vacancy_name(),
                    get_close_vacancy_salary('from'),
                    get_close_vacancy_salary('to'),
                    get_experience_description(),
                    get_close_vacancy_date(),
                    json.dumps(close_vacancy_data, ensure_ascii=False)
                )

                close_vacancies.append(data)
                close_vacancies_specializations.extend(get_close_vacancy_specializations(close_vacancy_id))

            logger_inf('1: Save closed vacancies data into database')

            save_data_to_database(close_vacancies_specializations, close_vacancies)

            logger_inf('Save open vacancies into file')

            with open('./loader/data/data.open_vacancies_ids', 'wb') as data_new:
                pickle.dump(list(sovi), data_new)

            logger_inf('Closed vacancies count: ' + str(len(close_vacancies_ids)))

        except pg.DatabaseError as e:
            logger_err('Error with database: ', e)
        except IOError as e:
            logger_err('1: IOError saved open vacancies ids in file: ', e)
        except Exception as e:
            logger_err('Error close vacancies data processing: ', e)
    else:
        try:
            logger_inf('2: Save open vacancies into file')
            with open('./loader/data/data.open_vacancies_ids', 'wb') as data_new:
                pickle.dump(list(sovi), data_new)
                logger_inf('No closed vacancies')
        except IOError as e:
            logger_err('2: IOError saved open vacancies ids in file: ', e)

    logger_inf('Finish')

