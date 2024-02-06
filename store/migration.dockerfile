FROM python:3

RUN mkdir -p /opt/src/store
WORKDIR /opt/src/store

COPY ./requirements.txt ./requirements.txt
COPY ./migrate.py ./migrate.py
COPY ./models.py ./models.py
COPY ./configuration.py ./configuration.py
COPY ./solidity/output/Payment.abi ./solidity/output/Payment.abi
COPY ./solidity/output/Payment.bin ./solidity/output/Payment.bin

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/store"

ENTRYPOINT ["python", "./migrate.py"]