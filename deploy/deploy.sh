#!/bin/sh
# Déploie la stack de production, depuis le dossier de docker-compose.prod.yml.
#   sh deploy/deploy.sh               récupère les images puis déploie
#   sh deploy/deploy.sh --sans-pull   utilise les images déjà présentes
# Échoue si un service n'est pas sain après le déploiement.
set -eu

ENV_FILE="${ENV_FILE:-.env}"
compose() {
  docker compose -f docker-compose.prod.yml --env-file "$ENV_FILE" "$@"
}

if [ "${1:-}" != "--sans-pull" ]; then
  compose pull
fi
compose up -d --wait --wait-timeout 180 --remove-orphans
compose ps
