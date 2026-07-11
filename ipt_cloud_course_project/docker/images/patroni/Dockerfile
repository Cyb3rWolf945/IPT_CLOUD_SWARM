# ==========================================
# PostgreSQL 14 + Patroni (Consul DCS)
# Custom image for database HA containers
# ==========================================
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install PostgreSQL 14 and Python dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    lsb-release \
    wget \
    && sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg \
    && apt-get update && apt-get install -y \
    postgresql-14 \
    postgresql-contrib-14 \
    python3 \
    python3-pip \
    python3-psycopg2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Patroni with Consul support
RUN pip3 install "patroni[consul]<4.0.0"

# Create data directory
RUN mkdir -p /var/lib/postgresql/data && \
    chown -R postgres:postgres /var/lib/postgresql && \
    chmod 700 /var/lib/postgresql/data

# Copy entrypoint script and post-bootstrap script
COPY docker/images/patroni/entrypoint.sh /entrypoint.sh
COPY docker/images/patroni/post_bootstrap.sh /post_bootstrap.sh
RUN chmod +x /entrypoint.sh /post_bootstrap.sh

# Copy Patroni config template (will be customized at runtime)
COPY docker/images/patroni/patroni.yml.j2 /etc/patroni/patroni.yml.template

# Expose PostgreSQL and Patroni REST API
EXPOSE 5432 8008

USER root
ENTRYPOINT ["/entrypoint.sh"]
CMD ["patroni", "/etc/patroni/patroni.yml"]
