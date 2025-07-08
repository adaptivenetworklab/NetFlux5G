# Mininet-WiFi & Containernet Docker Environment

This repository provides a Dockerized environment for running [Mininet-WiFi](https://github.com/intrig-unicamp/mininet-wifi) and [Containernet](https://github.com/containernet/containernet) with support for GUI applications via X11 forwarding.

---

## Features

- **Mininet-WiFi** and **Containernet** pre-installed
- X11 forwarding for GUI apps (e.g., `xterm`, `wireshark`)
- Privileged access for kernel modules and network namespaces
- Ready for advanced wireless and container-based network emulation

---

## Prerequisites

- **Docker** installed on your host system
- **Linux host** (kernel module access required)
- X11 server running on your host (for GUI apps)
- `mac80211_hwsim` kernel module loaded on the host

---

## Building the Docker Image

Clone this repository and build the Docker image:

```sh
docker build --build-context netflux5g=../netflux5g-editor -t netflux5g:latest .
```

---

## Preparing the Host

1. **Load the `mac80211_hwsim` kernel module with enough radios:**

   ```sh
   sudo modprobe mac80211_hwsim
   ```

2. **Allow X11 connections from local root (for GUI apps):**

   ```sh
   xhost +local:root
   ```

---

## Running the Container

Run the container with the following command:

```sh
docker run -it --rm --privileged --pid='host' --net='host' \
  --name netflux5g-dockerized \
  --env DISPLAY=$DISPLAY --env QT_X11_NO_MITSHM=1 --env NO_AT_BRIDGE=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /sys/:/sys \
  -v /lib/modules:/lib/modules \
  -v /sys/kernel/debug:/sys/kernel/debug \
  -v /var/run/netns:/var/run/netns \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /app/netflux5g/NetFlux5G/export/mininet/:/app/netflux5g/NetFlux5G/export/mininet/ \
  -v /logging/:/logging/ \
  netflux5g:latest
```

---

## Usage

- The container will start with a bash shell by default.
- To run Mininet-WiFi:

  ```sh
  sudo mn --wifi
  ```

- To test GUI apps (e.g., `xterm`):

  ```sh
  xterm
  ```

---

## Notes & Troubleshooting

- **mac80211_hwsim errors:**  
  Ensure the kernel module is loaded on the host **before** starting the container.
- **X11 errors:**  
  Make sure you ran `xhost +local:root` on the host and that your `$DISPLAY` variable is set.
- **Docker socket:**  
  The container expects `/var/run/docker.sock` to be mounted for Containernet support.

---

## File Structure

- `Dockerfile` – Docker build instructions
- `install.sh` – Mininet-WiFi and dependencies installer
- `entrypoint.sh` – Container entrypoint script

---

## License

See individual project repositories for license details.