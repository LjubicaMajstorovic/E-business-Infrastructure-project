FROM python:3

RUN mkdir -p /opt/src/store
WORKDIR /opt/src/store

COPY ./requirements.txt ./requirements.txt
COPY customer_application.py ./customer_application.py
COPY ./models.py ./models.py
COPY ./configuration.py ./configuration.py

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/store"

ENTRYPOINT ["python", "./customer_application.py"]