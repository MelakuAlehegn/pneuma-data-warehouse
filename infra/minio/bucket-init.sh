#!/bin/sh
# One-shot init: waits for MinIO to be reachable, then creates the raw bucket.
# Runs in the official mc (MinIO client) image alongside the MinIO server.
set -eu

echo "Waiting for MinIO to be reachable..."
until mc alias set local "http://minio:9000" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1; do
  sleep 1
done

echo "Ensuring bucket '${MINIO_BUCKET_RAW}' exists..."
mc mb --ignore-existing "local/${MINIO_BUCKET_RAW}"

echo "Bucket ready."
