# ==========================================
# PHP + Apache Application Server
# Serves the Project O web application
# ==========================================
FROM php:8.1-apache

# Install PHP extensions for PostgreSQL and Redis
RUN apt-get update && apt-get install -y \
    libpq-dev \
    libzip-dev \
    zip \
    unzip \
    git \
    && docker-php-ext-install pdo pdo_pgsql pgsql zip \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Enable Apache mod_rewrite
RUN a2enmod rewrite

# Install Composer
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

# Copy application source code
COPY --chown=www-data:www-data ./app/ /var/www/html/

# Install PHP dependencies via Composer
WORKDIR /var/www/html
RUN composer install --no-dev --no-interaction --optimize-autoloader 2>/dev/null || true

# Copy Apache VirtualHost config
COPY ./docker/configs/apache.conf /etc/apache2/sites-available/000-default.conf

# Configure PHP to use Redis for session storage
RUN echo "session.save_handler = redis" >> /usr/local/etc/php/conf.d/redis-sessions.ini && \
    echo "session.save_path = \"tcp://tasks.haproxy:6379?auth=redispass&timeout=2\"" >> /usr/local/etc/php/conf.d/redis-sessions.ini

# Copy application .env file (will be populated from Docker environment)
COPY ./docker/configs/app.env.template /var/www/html/.env.template

EXPOSE 80

# Entrypoint: generate .env from template, then start Apache
COPY ./docker/images/php-app/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["apache2-foreground"]
