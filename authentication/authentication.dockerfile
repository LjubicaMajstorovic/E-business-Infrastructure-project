FROM python:3

RUN mkdir -p /opt/src/authentication
WORKDIR /opt/src/authentication

COPY ./requirements.txt ./requirements.txt
COPY ./application.py ./application.py
COPY ./models.py ./models.py
COPY ./configuration.py ./configuration.py

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/authentication"

ENTRYPOINT ["python", "./application.py"]