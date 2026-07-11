# ==========================================
# RatchetPHP WebSocket Server
# Runs the WebSocket server with Redis pub/sub sync
# ==========================================
FROM php:8.1-cli

# Install PHP extensions
RUN apt-get update && apt-get install -y \
    libzip-dev \
    zip \
    unzip \
    git \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Composer
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

# Copy WebSocket server source
COPY ./ws/ /var/www/ws/

# Install Ratchet dependencies from existing composer.json
WORKDIR /var/www/ws
RUN rm -f composer.lock && composer install --no-interaction --no-dev --ignore-platform-req=php 2>&1

# Copy the WebSocket server script
COPY ./docker/images/ratchet-ws/websockets_server.php /var/www/ws/websockets_server.php

EXPOSE 8000

WORKDIR /var/www/ws
CMD ["php", "websockets_server.php"]
