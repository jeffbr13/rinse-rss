FROM python:3.4
ADD . /opt/rinse-rss
WORKDIR /opt/rinse-rss
RUN pip install -r requirements.txt
