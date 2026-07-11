#!/bin/bash
MSG_COLOR="\033[41m"

echo -e "$MSG_COLOR$(hostname): Update package lists\033[0m"
sudo apt-get update

echo -e "$MSG_COLOR$(hostname): Install Apache HTTP Server\033[0m"
sudo apt-get install -y apache2

echo -e "$MSG_COLOR$(hostname): Install PHP 8.1\033[0m"
# Install specific versions of PHP packages
sudo apt install -y --no-install-recommends php8.1

echo -e "$MSG_COLOR$(hostname): Install additional PHP 8.1 modules\033[0m"
sudo apt-get install -y \
    php8.1-cli \
    php8.1-common \
    php8.1-mysql \
    php8.1-pgsql \
    php8.1-pdo \
    php8.1-zip \
    php8.1-gd \
    php8.1-mbstring \
    php8.1-curl \
    php8.1-xml \
    php8.1-bcmath \
    zip \
    unzip

# sudo sh -c 'echo -e "<?php\nphpinfo();\n?>" > /var/www/html/phpinfo.php'

sudo systemctl restart apache2

echo -e "$MSG_COLOR$(hostname): Install PostgreSQL and its PHP extension\033[0m"
# Install specific version of PostgreSQL
sudo apt-get install -y postgresql-14 php-pgsql

# Change to /tmp directory since the next commands will run as "postgres" user
# to avoid could not change directory to "/home/vagrant": Permission denied
cd /tmp

echo -e "$MSG_COLOR$(hostname): Create a new PostgreSQL user and database\033[0m"
sudo -u postgres psql -c "CREATE USER myuser WITH PASSWORD 'mypassword';"
sudo -u postgres psql -c "CREATE DATABASE mydatabase OWNER myuser;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mydatabase TO myuser;"

# peer access to myuser
# sudo sh -c 'echo "local   all             myuser                                  peer" >> /etc/postgresql/14/main/pg_hba.conf'
sudo service postgresql restart

sudo -u postgres psql -d mydatabase -c "DROP TABLE test;"

echo -e "$MSG_COLOR$(hostname): Import dump.sql and set user privileges\033[0m"
# PGPASSWORD=mypassword sudo -u postgres psql -U myuser -h localhost -d mydatabase -f /vagrant/provision/dump.sql # change to ./provision/dump.sql
sudo -u postgres psql -d mydatabase -f /vagrant/provision/dump.sql
sudo -u postgres psql -d mydatabase -c "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE messages TO myuser;" # uneeded?
sudo -u postgres psql -d mydatabase -c "GRANT USAGE, SELECT, UPDATE ON SEQUENCE messages_id_seq TO myuser;"
sudo -u postgres psql -d mydatabase -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO myuser;"
sudo -u postgres psql -d mydatabase -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO myuser;"
sudo -u postgres psql -d mydatabase -c "GRANT ALL PRIVILEGES ON DATABASE mydatabase TO myuser;"

echo -e "$MSG_COLOR$(hostname): View users and databases in PostgreSQL\033[0m"
sudo -u postgres psql -c "\du"
sudo -u postgres psql -c "\list"
sudo -u postgres psql -d mydatabase -c "\dt"

# Change back to the previous folder
cd -

echo -e "$MSG_COLOR$(hostname): Install Composer (PHP)\033[0m"
cd ~
curl -sS https://getcomposer.org/installer -o /tmp/composer-setup.php
sudo php /tmp/composer-setup.php --install-dir=/usr/local/bin --filename=composer

echo -e "$MSG_COLOR$(hostname): Install dependencies for websockets server\033[0m"
cd /vagrant/ws
sudo -u vagrant bash -c 'composer install'

echo -e "$MSG_COLOR$(hostname): Install dependencies for webapp\033[0m"
cd /vagrant/app
sudo -u vagrant bash -c 'composer install'

echo -e "$MSG_COLOR$(hostname): Copy apache config, disable the default site / enable ours\033[0m"
sudo cp /vagrant/provision/projectA.conf /etc/apache2/sites-available/
sudo a2dissite 000-default.conf
sudo a2ensite projectA.conf
sudo systemctl reload apache2

echo -e "$MSG_COLOR$(hostname): Update deploy date @ .env file\033[0m"
cd /vagrant/app
ISO_DATE=$(TZ=Europe/Lisbon date -Iseconds)
sed -i "s/^DEPLOY_DATE=.*/DEPLOY_DATE=\"$ISO_DATE\"/" .env

echo -e "\033[42m$(hostname): Finished! Visit http://192.168.44.10\033[0m"
