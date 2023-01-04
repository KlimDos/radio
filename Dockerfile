
FROM python:slim-buster
LABEL maintainer="Sasha Alimov klimdos@gmail.com"
WORKDIR /src
COPY src/ .
RUN pip install -r requirements.txt
EXPOSE 8080
ARG FLASK_RUN_PORT=8080
ENV FLASK_RUN_PORT=${FLASK_RUN_PORT} 
ENTRYPOINT ["python", "-m", "flask", "run", "--host=0.0.0.0"]
