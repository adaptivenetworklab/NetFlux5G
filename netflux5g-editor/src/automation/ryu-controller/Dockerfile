FROM python:3.9-bullseye
WORKDIR /usr/src/app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    net-tools \
    iputils-ping \
    gcc python-dev libffi-dev libssl-dev libxml2-dev libxslt1-dev zlib1g-dev \
    git && \
    rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/faucetsdn/ryu.git

RUN pip install --upgrade pip
RUN pip install --root-user-action=ignore requests

WORKDIR /usr/src/app/ryu
RUN pip install .

EXPOSE 8080
EXPOSE 6633
EXPOSE 6653

CMD ["ryu-manager", "ryu.app.simple_switch_stp_13"]