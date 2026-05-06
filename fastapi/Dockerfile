FROM artifactory.rgs.ru/docker/python:3.10-slim-bullseye
LABEL authors="Arsen Davydov"
LABEL maintainer="arsen_davydov@rgs.ru"
# RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping telnet
ADD app /opt/app
ADD requirements.txt /opt/app/requirements.txt
WORKDIR /opt/app
RUN python3 -m pip install --upgrade --trusted-host artifactory.rgs.ru --index-url https://artifactory.rgs.ru/artifactory/api/pypi/pypi-remote/simple pip
RUN python3 -m pip install --trusted-host artifactory.rgs.ru --index-url https://artifactory.rgs.ru/artifactory/api/pypi/pypi-remote/simple -r /opt/app/requirements.txt 
ENV TZ=Europe/Moscow
# ENV WORKERS_COUNT 15
EXPOSE 5000
CMD pyagent run -- /usr/local/bin/uvicorn alerts:app --workers $WORKERS_COUNT --host 0.0.0.0 --port 5000