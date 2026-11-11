#!/bin/sh
# Construit l'image du service de traitement et déploie la stack de production,
# depuis le dossier de docker-compose.prod.yml :
#   sh deploy/deploy.sh
# Échoue si un service n'est pas sain après le déploiement.
set -eu

ENV_FILE="${ENV_FILE:-.env}"
compose() {
  docker compose -f docker-compose.prod.yml --env-file "$ENV_FILE" "$@"
}

compose up -d --build --wait --wait-timeout 180 --remove-orphans
compose ps
