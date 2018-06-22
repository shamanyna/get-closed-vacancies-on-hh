
FROM python:3.6

WORKDIR /loader

RUN pip install requests
RUN pip install psycopg2
RUN pip install schedule

COPY . /loader

ARG SCHEDULE_MINUTES_INTERVAL=1
ENV SCHEDULE_MINUTES_INTERVAL=1
ENTRYPOINT ["python", "scheduler.py", "$SCHEDULE_MINUTES_INTERVAL"]
#CMD ["python", "scheduler.py", "$SCHEDULE_MINUTES_INTERVAL"]
