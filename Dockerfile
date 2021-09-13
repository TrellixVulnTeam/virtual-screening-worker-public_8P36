FROM python:3.8-slim

ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /usr/bin/tini
RUN chmod +x /usr/bin/tini

RUN apt-get update \
  && apt-get install autodock-vina openbabel -y
COPY requirements.txt requirements.txt
COPY src src
RUN pip3 install -r requirements.txt
ENTRYPOINT ["/usr/bin/tini", "-g", "--", "python", "src/main.py"]