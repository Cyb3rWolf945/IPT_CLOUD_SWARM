#!/bin/bash
# Patroni Post-Bootstrap script

echo "Running Patroni post-bootstrap script to create initial database..."

RETRIES=15
until psql -U postgres -c "select 1" > /dev/null 2>&1 || [ $RETRIES -eq 0 ]; do
  echo "Waiting for postgres server, $((RETRIES--)) remaining attempts..."
  sleep 2
done

echo "Creating app_user..."
psql -U postgres -d postgres -c "CREATE USER app_user WITH PASSWORD 'app_password';" || echo "User may already exist."

echo "Creating database project_o..."
psql -U postgres -d postgres -c "CREATE DATABASE project_o OWNER app_user;" || echo "Database may already exist."

echo "Creating messages table..."
psql -U postgres -d project_o -c "
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
ALTER TABLE messages OWNER TO app_user;
"

echo "Post-bootstrap script completed."

