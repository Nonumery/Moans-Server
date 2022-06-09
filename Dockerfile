# syntax=docker/dockerfile:1
FROM ubuntu:20.04
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install python3.10 -y && apt-get install python3-pip -y
COPY . .
RUN pip install pipenv && pipenv sync
EXPOSE 8000
CMD ["pipenv", "run", "python", "main.py"]