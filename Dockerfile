
FROM python:slim-buster
LABEL maintainer="Sasha Alimov klimdos@gmail.com"
WORKDIR /src
COPY src/ .
RUN pip install -r requirements.txt
ARG BUILD
ENV BUILD=$BUILD
EXPOSE 5000
ENTRYPOINT ["python", "-m", "flask", "run", "--host=0.0.0.0"]
