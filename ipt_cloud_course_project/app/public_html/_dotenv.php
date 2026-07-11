<?php
error_reporting(E_ALL & ~E_DEPRECATED);
ini_set('display_errors', '1');

if (file_exists('/opt/app/vendor/autoload.php')) {
    require_once '/opt/app/vendor/autoload.php'; // Vagrant environment
} else {
    require_once __DIR__ . '/../vendor/autoload.php'; // Docker environment
}

$dotenv = Dotenv\Dotenv::createImmutable(__DIR__ . '/../');
$dotenv->load();

$badge = $_ENV['BADGE'];
$deploy_date = $_ENV['DEPLOY_DATE'];
$db_host = $_ENV['DB_HOST'];
$db_port = $_ENV['DB_PORT'];
$db_user = $_ENV['DB_USER'];
$db_pass = $_ENV['DB_PASS'];
$db_name = $_ENV['DB_NAME'];
$ws_host = $_ENV['WS_HOST'];
$ws_port = $_ENV['WS_PORT'];
// Use the $badge variable in your page
?>