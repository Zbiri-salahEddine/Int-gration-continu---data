#!/bin/sh
# Démarre SeaweedFS avec les clés S3 reçues par l'environnement.
set -eu
umask 077
cat > /tmp/s3.json <<EOF
{
  "identities": [
    {
      "name": "pipeline",
      "credentials": [{"accessKey": "$S3_ACCESS_KEY", "secretKey": "$S3_SECRET_KEY"}],
      "actions": ["Admin", "Read", "List", "Write", "Tagging"]
    }
  ]
}
EOF
exec weed server -dir=/data -ip=127.0.0.1 -ip.bind=0.0.0.0 -volume.max=10 -master.volumeSizeLimitMB=64 \
  -s3 -s3.port=8333 -s3.config=/tmp/s3.json
