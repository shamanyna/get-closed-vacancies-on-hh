
FROM python:3.6

WORKDIR /loader

RUN pip install requests
RUN pip install psycopg2
RUN pip install schedule

COPY . /loader
CMD ["python", "scheduler.py", "2"]
