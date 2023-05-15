FROM python:3.8.10-slim-buster

RUN apt-get update; \
    apt-get install -y cmake traceroute\
    ; \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install awsiotsdk numpy dlr Pillow
WORKDIR /app

COPY ./IoTPublisher.py /app/IoTPublisher.py
COPY ./test_X.npy /app/test_X.npy
COPY ./classifier/ /app/classifier/

CMD ["python3", "/app/IoTPublisher.py"]
