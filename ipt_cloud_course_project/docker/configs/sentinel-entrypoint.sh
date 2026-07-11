#!/bin/sh
# Sentrypoint — resolves redis-master IP and starts Sentinel
echo "Resolving redis-master IP..."
REDIS_MASTER_IP=$(getent hosts redis-master | awk '{ print $1 }' | head -n 1)
if [ -z "$REDIS_MASTER_IP" ]; then
    echo "ERROR: Cannot resolve redis-master"
    exit 1
fi
echo "redis-master IP: $REDIS_MASTER_IP"

# Generate sentinel config with actual IP
cat /usr/local/etc/redis/sentinel.conf.template | \
    sed "s/REDIS1_IP/$REDIS_MASTER_IP/g" > /usr/local/etc/redis/sentinel.conf

echo "Starting Redis Sentinel..."
exec redis-sentinel /usr/local/etc/redis/sentinel.conf
