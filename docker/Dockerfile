FROM netflux5g
FROM ubuntu:22.04

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
        libxrender1 \
        libgl1 \
        libglx0 \
        libgl1-mesa-glx \
        libqt5gui5 \
        qtbase5-dev \
        qt5-qmake \
        libqt5core5a \
        libqt5dbus5 \
        dbus-x11 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/netflux5g

RUN git clone https://github.com/intrig-unicamp/mininet-wifi.git
RUN git clone https://github.com/ramonfontes/containernet.git

WORKDIR /app/netflux5g/mininet-wifi

# Run the installation script
RUN git checkout 69c6251d06f01840276dee14fd6c7819b232e13f
RUN apt-get update && util/install.sh -Wlnfv6

WORKDIR /app/netflux5g/containernet
COPY ./containernet-install.sh /app/netflux5g/containernet/util/install.sh
RUN apt-get update && util/install.sh -W

# tell containernet that it runs in a container
ENV CONTAINERNET_NESTED=1

WORKDIR /app/netflux5g

RUN mkdir NetFlux5G

COPY --from=netflux5g ./requirements.txt NetFlux5G
RUN pip3 install -r NetFlux5G/requirements.txt

COPY --from=netflux5g ./src/ NetFlux5G

WORKDIR /app/netflux5g/NetFlux5G

# Set the dafault init to use bash shell
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/bash"]
