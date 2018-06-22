
FROM python:3.6

WORKDIR /loader

RUN pip install requests
RUN pip install psycopg2
RUN pip install schedule

COPY . /loader

ENV SCHEDULE_MINUTES_INTERVAL=1
CMD python scheduler.py 1
