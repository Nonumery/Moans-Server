# syntax=docker/dockerfile:1
FROM python:3.10
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install python3-pip -y
COPY . .
RUN pip install pipenv && pipenv sync
EXPOSE 8000
CMD ["pipenv", "run", "python", "main.py"]