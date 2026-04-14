FROM python:3.12-slim-bookworm
LABEL maintainer="Sasha Alimov klimdos@gmail.com"

ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    PIP_NO_CACHE_DIR=1

WORKDIR /src
COPY src/ .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080
ARG FLASK_RUN_PORT=8080
ENV FLASK_RUN_PORT=${FLASK_RUN_PORT}

ARG Build=dev
ENV ARTEFACT_VERSION=${Build}

ENTRYPOINT ["python", "-m", "flask", "run", "--host=0.0.0.0"]
