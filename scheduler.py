import schedule
import time
from closed_vacancies_loader import loader


def job():
    loader()


schedule.every(1).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
