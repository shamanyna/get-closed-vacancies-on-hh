import requests

import pickle
import logging
import datetime
import threading
import postgresql


logging.basicConfig(filename='log.log', level=logging.INFO)

threads = []
open_vacancies_ids = []
close_vacancies_ids = []
close_vacancies = []
close_vacancies_specializations = []


def logger_inf(msg: str):
    timestamp = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    logging.info(timestamp + '\t' + msg)


def logger_err(msg: str, ex: Exception):
    timestamp = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    logging.error(timestamp + '\t' + msg + '\t' + str(ex))


def get_metro_from_hh(city_id: int) -> list:
    url = 'https://api.hh.ru/metro/' + str(city_id)
    request = requests.get(url).json()

    stations = []
    for line in request['lines']:
        stations.extend([station['id'] for station in line['stations']])

    return stations


def get_open_vacancies_from_hh(metro_id: str) -> list:
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
    return requests.get('https://api.hh.ru/vacancies/' + str(close_vacancy_id)).json()


def get_experience_description() -> str:
    experience = close_vacancy_data['experience']['id']
    return {
        experience == 'noExperience': 'junior',
        experience == 'between1And3': 'middle',
        experience == 'between3And6': 'senior',
        experience == 'moreThan6': 'expert'
    }[True]


def get_close_vacancy_name() -> str:
    return close_vacancy_data['name']


def get_conversion_multiplications() -> float:
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
    return close_vacancy_data['published_at']


def get_close_vacancy_specializations(close_vacancy_id: int) -> list:
    return [{close_vacancy_id: specialization['name']} for specialization in close_vacancy_data['specializations']]


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
    with open('data.open_vacancies_ids', 'rb') as data_old:
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

            data = {
                'id': close_vacancy_id,
                'name': get_close_vacancy_name(),
                'salary_from': get_close_vacancy_salary('from'),
                'salary_to': get_close_vacancy_salary('to'),
                'experience': get_experience_description(),
                'published_at': get_close_vacancy_date()
                # !!!!!!!!!!!
                # data['json'] = close_vacancy_data
            }

            close_vacancies.append(data)
            close_vacancies_specializations.extend(get_close_vacancy_specializations(close_vacancy_id))

        print(close_vacancies)
        print(close_vacancies_specializations)

        logger_inf('1: Save closed vacancies data into database')
        # save _to_db


        logger_inf('Save open vacancies into file')
        with open('data.open_vacancies_ids', 'wb') as data_new:
            pickle.dump(list(sovi), data_new)

            logger_inf('Closed vacancies count: ' + str(len(close_vacancies_ids)))

    # except saveDB:

    except IOError as e:
        logger_err('1: IOError saved open vacancies ids in file: ', e)

    except Exception as e:
        logger_err('Error close vacancies data processing: ', e)
else:
    try:
        logger_inf('2: Save open vacancies into file')
        with open('data.open_vacancies_ids', 'wb') as data_new:
            pickle.dump(list(sovi), data_new)
            logger_inf('No closed vacancies')
    except IOError as e:
        logger_err('2: IOError saved open vacancies ids in file: ', e)

logger_inf('Finish')
