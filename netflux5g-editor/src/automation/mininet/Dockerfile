FROM ubuntu:20.04

ENV TZ=Asia/Jakarta
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y \
        git \
        make \
        help2man \
        net-tools \
        aptitude \
        build-essential \
        python3 \
        python3-setuptools \
        python3-dev \
        python3-pip \
        python3-venv \
        pyflakes3 \
        tcpdump \
        wpan-tools \
        software-properties-common \
        ansible \
        curl \
        iptables \
        iputils-ping \
        traceroute \
        nano \
        sudo \
        x11-apps \
        xauth \
        xorg \
        openbox \
        libx11-xcb1 \
        libxcb1 \
        libxcb-xinerama0 \
        libxcb-icccm4 \
        libxcb-image0 \
        libxcb-keysyms1 \
        libxcb-randr0 \
        libxcb-render0 \
        libxcb-render-util0 \
        libxcb-shape0 \
        libxcb-shm0 \
        libxcb-sync1 \
        libxcb-xfixes0 \
        libxcb-xkb1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/neflux5g

RUN git clone https://github.com/intrig-unicamp/mininet-wifi.git
RUN git clone https://github.com/containernet/containernet.git
COPY ./install.sh /app/neflux5g/mininet-wifi/util/install.sh

WORKDIR /app/neflux5g/containernet/ansible
# ENV VIRTUAL_ENV=/opt/venv
# RUN python3 -m venv $VIRTUAL_ENV
# ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN pip install --upgrade pip ansible
RUN ansible-playbook -i "localhost," -c local --skip-tags "notindocker" install.yml

WORKDIR /app/neflux5g/containernet
RUN make install

# tell containernet that it runs in a container
ENV CONTAINERNET_NESTED=1

WORKDIR /app/neflux5g/mininet-wifi

# Run the installation script
RUN util/install.sh -Wlnfv6

WORKDIR /app/neflux5g
RUN git clone https://github.com/adaptivenetworklab/Riset_23-24_SDN.git NetFlux5G
RUN git clone https://github.com/adaptivenetworklab/Riset_23-24_SDN.git

# Set the dafault init to use bash shell
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
