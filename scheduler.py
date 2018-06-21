import schedule
import time
from loader import loader


def job():
    loader()


schedule.every(2).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(30)
