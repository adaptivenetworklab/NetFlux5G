#!/bin/bash
# Common functions used by container technology comparison tests

# Check if a command exists
check_command() {
  if ! command -v "$1" &> /dev/null; then
    echo "Error: $1 is not installed" >&2
    exit 1
  fi
}

# Clean up containers
cleanup_container() {
  local platform=$1
  local name=$2
  case "$platform" in
    docker)
      docker rm -f "$name" >/dev/null 2>&1
      ;;
    containerd)
      nerdctl rm -f "$name" >/dev/null 2>&1
      ;;
    podman)
      podman rm -f "$name" >/dev/null 2>&1
      ;;
    lxd)
      lxc delete -f "$name" >/dev/null 2>&1
      ;;
  esac
}

# Measure execution time
measure_time() {
  local start_time end_time duration
  start_time=$(date +%s.%N)
  "$@"
  end_time=$(date +%s.%N)
  duration=$(echo "$end_time - $start_time" | bc)
  echo "Execution time: $duration seconds"
}
