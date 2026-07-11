<?php
/**
 * RatchetPHP WebSocket Server — Redis pub/sub + User tracking
 * Docker version — connects to Sentinel services via overlay network
 */

require __DIR__ . '/vendor/autoload.php';

use Ratchet\MessageComponentInterface;
use Ratchet\ConnectionInterface;
use Ratchet\Server\IoServer;
use Ratchet\Http\HttpServer;
use Ratchet\WebSocket\WsServer;

// ─── Redis Sentinel Configuration (Docker service names) ────────
$sentinel_env = getenv('SENTINEL_HOSTS') ?: (getenv('SENTINEL1_HOST') ?: 'tasks.sentinel:26379');
$sentinel_hosts = explode(',', $sentinel_env);

// Ensure all hosts have a port (append default if missing)
$sentinel_hosts = array_map(function($h) {
    return strpos($h, ':') !== false ? trim($h) : trim($h) . ':26379';
}, $sentinel_hosts);
$redis_password = getenv('REDIS_PASSWORD') ?: 'redispass';
$redis_master_name = getenv('REDIS_MASTER_NAME') ?: 'mymaster';

// ─── Discover Redis Master via Sentinel ─────────────────────────
function discover_master($sentinel_hosts, $master_name) {
    foreach ($sentinel_hosts as $host) {
        list($ip, $port) = explode(':', $host);
        try {
            $sentinel = new Redis();
            $sentinel->connect($ip, (int)$port, 2);
            if (getenv('REDIS_PASSWORD')) {
                $sentinel->auth(getenv('REDIS_PASSWORD'));
            }
            $master = $sentinel->rawCommand('SENTINEL', 'get-master-addr-by-name', $master_name);
            if ($master && count($master) === 2) {
                return ['host' => $master[0], 'port' => $master[1]];
            }
        } catch (Exception $e) {
            error_log("Sentinel $host: " . $e->getMessage());
            continue;
        }
    }
    throw new RuntimeException('Could not discover Redis master via Sentinel');
}

echo "=== Ratchet WebSocket Server (Docker) ===\n";
echo "Discovering Redis master via Sentinel...\n";

$master = discover_master($sentinel_hosts, $redis_master_name);
echo "Redis master: {$master['host']}:{$master['port']}\n";

class NotificationServer implements MessageComponentInterface
{
    public $clients;
    public $server_id;
    protected $redis_pub;
    protected $redis_master;
    protected $redis_password;

    public function __construct($redis_master, $redis_password)
    {
        $this->clients = new \SplObjectStorage();
        $this->server_id = gethostname() . ':' . getmypid();
        $this->redis_master = $redis_master;
        $this->redis_password = $redis_password;

        // Publisher — sends messages to Redis channel synchronously (very fast, non-blocking practically)
        $this->redis_pub = new Redis();
        $this->redis_pub->connect($redis_master['host'], (int)$redis_master['port']);
        if ($redis_password) {
            $this->redis_pub->auth($redis_password);
        }
        echo "[{$this->server_id}] Redis pub connected\n";
    }

    private function getUserId(ConnectionInterface $conn) {
        $query = $conn->httpRequest->getUri()->getQuery();
        parse_str($query, $params);
        return $params['user_id'] ?? 'anon';
    }

    public function onOpen(ConnectionInterface $conn)
    {
        $this->clients->attach($conn);
        $user_id = $this->getUserId($conn);
        echo "[{$this->server_id}] New connection: {$conn->resourceId} (user: {$user_id})\n";

        // Store user mapping in Redis
        $this->redis_pub->set("ws:users:{$user_id}_{$conn->resourceId}", json_encode([
            'server' => $this->server_id,
            'resourceId' => $conn->resourceId,
        ]));

        $conn->send(json_encode([
            'type' => 'system',
            'event' => 'connected',
            'message' => 'Connected to WebSocket server.',
            'server' => $this->server_id,
        ]));

        // Broadcast to everyone that a user joined
        $payload = json_encode([
            'type' => 'system',
            'event' => 'user_joined',
            'user_id' => $user_id,
            'online_count' => count($this->clients), // Note: only counts local clients, but good enough for demo
            'server' => $this->server_id,
        ]);
        $this->redis_pub->publish('chat', $payload);
    }

    public function onMessage(ConnectionInterface $from, $msg)
    {
        $data = json_decode($msg, true);
        $user_id = $this->getUserId($from);

        $payload = json_encode([
            'type' => 'message',
            'message' => $data['message'] ?? '',
            'sender_user_id' => $user_id,
            'sender_resourceId' => $from->resourceId,
            'server' => $this->server_id,
            'timestamp' => date('H:i:s'),
        ]);

        // PUBLISH to Redis — all instances receive and broadcast
        $this->redis_pub->publish('chat', $payload);
    }

    public function onClose(ConnectionInterface $conn)
    {
        $user_id = $this->getUserId($conn);
        echo "[{$this->server_id}] Connection closed: {$conn->resourceId} (user: {$user_id})\n";

        $this->redis_pub->del("ws:users:{$user_id}_{$conn->resourceId}");
        $this->clients->detach($conn);

        // Broadcast to everyone that a user left
        $payload = json_encode([
            'type' => 'system',
            'event' => 'user_left',
            'user_id' => $user_id,
            'online_count' => count($this->clients),
            'server' => $this->server_id,
        ]);
        $this->redis_pub->publish('chat', $payload);
    }

    public function onError(ConnectionInterface $conn, \Exception $e)
    {
        echo "[{$this->server_id}] Error: {$e->getMessage()}\n";
        $conn->close();
    }
}

// ─── Start Server ───────────────────────────────────────────────
$server = new NotificationServer($master, $redis_password);

$wsServer = new WsServer($server);
$httpServer = new HttpServer($wsServer);

$port = (int)(getenv('WS_PORT') ?: 8000);
$ioServer = IoServer::factory($httpServer, $port);

echo "Ratchet WebSocket server running on port {$port}\n";
echo "Server ID: {$server->server_id}\n";

// Set up Async Redis Subscriber using the ReactPHP Loop
$loop = $ioServer->loop;
$factory = new Clue\React\Redis\Factory($loop);

$url = "redis://";
if ($redis_password) {
    $url .= ":" . rawurlencode($redis_password) . "@";
}
$url .= $master['host'] . ":" . $master['port'];

$factory->createClient($url)->then(function (Clue\React\Redis\Client $client) use ($server) {
    echo "[{$server->server_id}] Redis async sub connected\n";
    $client->on('message', function ($channel, $message) use ($server) {
        $data = json_decode($message, true);
        // Ensure broadcast payload is serialized back or pass object?
        // Actually, $message is already a JSON string.
        foreach ($server->clients as $clientConn) {
            $clientConn->send($message);
        }
    });
    $client->subscribe('chat');
})->catch(function (Exception $e) {
    echo "Failed to connect async Redis: " . $e->getMessage() . "\n";
});

$ioServer->run();
