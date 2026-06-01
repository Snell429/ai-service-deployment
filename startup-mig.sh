#!/bin/bash
set -euxo pipefail

exec > >(tee -a /var/log/startup-script.log) 2>&1

APP_DIR="/opt/ai-service"
IMAGE_URI="europe-west9-docker.pkg.dev/ai-flan-project/ai-service-repo/flan-t5-api:latest"
MODEL_NAME="google/flan-t5-base"
MAX_NEW_TOKENS="50"

apt-get update
apt-get install -y ca-certificates curl gnupg lsb-release

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl restart docker

mkdir -p "${APP_DIR}"
cd "${APP_DIR}"

ACCESS_TOKEN=$(curl -fsSL -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" | \
  python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")

echo "${ACCESS_TOKEN}" | docker login -u oauth2accesstoken --password-stdin https://europe-west9-docker.pkg.dev

cat > docker-compose.yml <<EOF
services:
  app:
    image: ${IMAGE_URI}
    container_name: flan-t5-api
    ports:
      - "8000:8000"
    environment:
      MODEL_NAME: ${MODEL_NAME}
      MAX_NEW_TOKENS: "${MAX_NEW_TOKENS}"
    restart: unless-stopped
EOF

docker compose pull
docker compose up -d

until curl --fail --silent http://localhost:8000/health; do
  sleep 10
done
