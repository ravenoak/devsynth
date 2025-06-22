set -exo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y \
  build-essential python3-dev python3-venv cmake pkg-config git \
  libssl-dev libffi-dev libxml2-dev libargon2-dev libblas-dev \
  liblapack-dev libopenblas-dev liblmdb-dev libz3-dev libcurl4-openssl-dev
apt-get clean
rm -rf /var/lib/apt/lists/*

poetry sync --all-groups --all-extras
