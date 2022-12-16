
FROM python:slim-buster

LABEL maintainer="Sasha Alimov klimdos@gmail.com"

WORKDIR /app

COPY src .

RUN pip install -r requirements.txt

ARG BUILD

ENV BUILD=$BUILD

EXPOSE 8080

ENTRYPOINT ["python", "-m", "flask", "run", "--host=0.0.0.0"]
