FROM python:3.6.6-stretch

ENV PYTHONUNBUFFERED=1
ENV WEBAPP_DIR=/app/Refresher
RUN mkdir app
RUN mkdir $WEBAPP_DIR
WORKDIR $WEBAPP_DIR

RUN apt-get update
RUN apt-get install -y python-dev libldap2-dev libsasl2-dev libssl-dev vim default-jdk

ADD requirements.txt $WEBAPP_DIR/
ADD jtds.jar $WEBAPP_DIR/
RUN pip install -r requirements.txt
RUN pip install flower
RUN pip install JayDeBeApi

ADD . $WEBAPP_DIR/

