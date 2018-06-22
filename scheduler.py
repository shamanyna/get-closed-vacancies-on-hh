import schedule
import time
from loader import loader


def job():
    loader()


schedule.every(60).seconds.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
