import sys
import schedule
import time
from loader import loader

if len(sys.argv) > 1:
    schedule_interval = sys.argv[1]
else:
    schedule_interval = 1


def job():
    loader()


schedule.every(schedule_interval).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
