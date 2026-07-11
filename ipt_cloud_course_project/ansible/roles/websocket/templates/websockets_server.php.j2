<?php
/**
 * RatchetPHP WebSocket Server — Redis pub/sub + User tracking
 * 
 * Runs on both web1 and web2. Messages sync via Redis pub/sub.
 * User→connection mapping stored in Redis for cross-instance visibility.
 */

require '/opt/ws/vendor/autoload.php';

use Ratchet\MessageComponentInterface;
use Ratchet\ConnectionInterface;
use Ratchet\Server\IoServer;
use Ratchet\Http\HttpServer;
use Ratchet\WebSocket\WsServer;

// ─── Redis Sentinel Configuration ───────────────────────────────
$sentinel_hosts = [
    '192.168.44.41:26379',
    '192.168.44.42:26379',
    '192.168.44.43:26379',
];
$redis_password = 'redispass';
$redis_master_name = 'mymaster';

// ─── Discover Redis Master via Sentinel ─────────────────────────
function discover_master($sentinel_hosts, $master_name) {
    foreach ($sentinel_hosts as $host) {
        list($ip, $port) = explode(':', $host);
        try {
            $sentinel = new Redis();
            $sentinel->connect($ip, $port, 2);
            $master = $sentinel->rawCommand('SENTINEL', 'get-master-addr-by-name', $master_name);
            if ($master && count($master) === 2) {
                return ['host' => $master[0], 'port' => $master[1]];
            }
        } catch (Exception $e) {
            continue;
        }
    }
    throw new RuntimeException('Could not discover Redis master via Sentinel');
}

$master = discover_master($sentinel_hosts, $redis_master_name);

class NotificationServer implements MessageComponentInterface
{
    public $clients;
    protected $redis_pub;
    protected $redis_sub;
    protected $server_id;

    public function __construct($redis_master, $redis_password)
    {
        $this->clients = new \SplObjectStorage();
        $this->server_id = gethostname() . ':' . getmypid();

        // Publisher — sends messages to Redis channel
        $this->redis_pub = new Redis();
        $this->redis_pub->connect($redis_master['host'], $redis_master['port']);
        if ($redis_password) {
            $this->redis_pub->auth($redis_password);
        }

        // Subscriber — receives messages from Redis channel (blocking, runs in separate process)
        // We'll fork a child process for the subscriber
        $pid = pcntl_fork();
        if ($pid == 0) {
            // Child: Redis subscriber
            $sub = new Redis();
            $sub->connect($redis_master['host'], $redis_master['port']);
            if ($redis_password) {
                $sub->auth($redis_password);
            }
            $sub->subscribe(['chat'], function ($redis, $channel, $message) {
                // Forward to parent via stdout pipe or shared memory
                // For simplicity, we write to stdout and parent reads
                echo "REDIS_MSG:" . $message . "\n";
            });
            exit(0);
        }

        echo "[{$this->server_id}] WebSocket server started with Redis pub/sub\n";
    }

    public function onOpen(ConnectionInterface $conn)
    {
        // Parse user_id from query string
        $query_string = $conn->httpRequest->getUri()->getQuery();
        parse_str($query_string, $params);
        $user_id = $params['user_id'] ?? 'anon_' . $conn->resourceId;

        $this->clients->attach($conn);

        // Store in Redis: user → connection info
        $info = json_encode([
            'server'     => $this->server_id,
            'resourceId' => $conn->resourceId,
            'user_id'    => $user_id,
            'connected_at' => date('c'),
        ]);
        $this->redis_pub->hSet('ws:connections', $conn->resourceId, $info);
        $this->redis_pub->hSet('ws:users', $user_id, $conn->resourceId);
        $this->redis_pub->expire('ws:users', 86400);

        echo "[{$this->server_id}] New connection: {$conn->resourceId} (user: {$user_id})\n";

        // Notify everyone about the new user
        $this->broadcast([
            'type'       => 'system',
            'event'      => 'user_joined',
            'user_id'    => $user_id,
            'online_count' => $this->redis_pub->hLen('ws:connections'),
            'timestamp'  => date('Y-m-d H:i:s'),
        ]);
    }

    public function onMessage(ConnectionInterface $from, $message)
    {
        $data = json_decode($message, true);
        if (!$data) return;

        $data['timestamp'] = date('Y-m-d H:i:s');
        $data['sender_resourceId'] = $from->resourceId;

        // Get user_id from Redis
        $info = $this->redis_pub->hGet('ws:connections', $from->resourceId);
        if ($info) {
            $conn_info = json_decode($info, true);
            $data['sender_user_id'] = $conn_info['user_id'] ?? 'unknown';
        }

        // Sanitize message
        if (isset($data['message'])) {
            $data['message'] = htmlspecialchars($data['message'], ENT_QUOTES, 'UTF-8');
        }

        // Publish to Redis → all server instances receive it
        $this->redis_pub->publish('chat', json_encode($data));
    }

    public function onClose(ConnectionInterface $conn)
    {
        // Get user info before cleanup
        $info = $this->redis_pub->hGet('ws:connections', $conn->resourceId);
        $user_id = 'unknown';
        if ($info) {
            $conn_info = json_decode($info, true);
            $user_id = $conn_info['user_id'] ?? 'unknown';
        }

        $this->clients->detach($conn);

        // Cleanup Redis
        $this->redis_pub->hDel('ws:connections', $conn->resourceId);
        $this->redis_pub->hDel('ws:users', $user_id);

        echo "[{$this->server_id}] Connection {$conn->resourceId} disconnected (user: {$user_id})\n";

        // Notify everyone
        $this->broadcast([
            'type'       => 'system',
            'event'      => 'user_left',
            'user_id'    => $user_id,
            'online_count' => $this->redis_pub->hLen('ws:connections'),
            'timestamp'  => date('Y-m-d H:i:s'),
        ]);
    }

    public function onError(ConnectionInterface $conn, \Exception $e)
    {
        echo "[{$this->server_id}] Error: {$e->getMessage()}\n";
        $conn->close();
    }

    /**
     * Broadcast a message to ALL local clients (used for system messages)
     */
    private function broadcast(array $data)
    {
        $json = json_encode($data);
        foreach ($this->clients as $client) {
            $client->send($json);
        }
    }
}

/**
 * Redis subscriber tick — called on each event loop iteration
 * Reads from the forked child's output to receive pub/sub messages
 *
 * Since pcntl_fork in Ratchet is tricky, we use a simpler approach:
 * Poll Redis SUBSCRIBE in a non-blocking way inside the event loop.
 */
class RedisSubscriber
{
    protected $redis;
    protected $server;

    public function __construct($redis_master, $redis_password, NotificationServer $server)
    {
        $this->server = $server;
        $this->redis = new Redis();
        $this->redis->connect($redis_master['host'], $redis_master['port']);
        if ($redis_password) {
            $this->redis->auth($redis_password);
        }
        // Sadly, phpredis subscribe is blocking — we use a tick-based approach
        // For simplicity, we use a separate thread via pcntl_fork + pipe
    }
}

// ─── Start the Server ───────────────────────────────────────────
$notification_server = new NotificationServer($master, $redis_password);

// Start Redis subscriber as a forked process reading from pub/sub
$sub_pid = pcntl_fork();
if ($sub_pid == 0) {
    // Child: subscribe to Redis and forward to parent via pipe
    $sub = new Redis();
    $sub->connect($master['host'], $master['port']);
    if ($redis_password) {
        $sub->auth($redis_password);
    }
    $sub->setOption(Redis::OPT_READ_TIMEOUT, -1); // no timeout
    $sub->subscribe(['chat'], function ($redis, $channel, $message) {
        // Write to stdout with a marker, parent's event loop will pick it up
        // Actually, we use file-based IPC: write to a temp file
        file_put_contents('/tmp/ratchet_pubsub_' . getmypid(), $message . "\n", FILE_APPEND);
    });
    exit(0);
}

// Register a tick function in the Ratchet event loop to check for incoming Redis messages
$loop = \React\EventLoop\Factory::create();

// Periodic timer: check for messages from Redis subscriber child
$loop->addPeriodicTimer(0.05, function () use ($notification_server) {
    // Read messages forwarded by child process
    $files = glob('/tmp/ratchet_pubsub_*');
    foreach ($files as $file) {
        $content = @file_get_contents($file);
        if ($content) {
            @unlink($file);
            foreach (explode("\n", trim($content)) as $msg) {
                if ($msg) {
                    foreach ($notification_server->clients as $client) {
                        $client->send($msg);
                    }
                }
            }
        }
    }
});

$server = IoServer::factory(
    new HttpServer(
        new WsServer($notification_server)
    ),
    8000,
    '0.0.0.0'
);

$server->loop->addPeriodicTimer(0.05, function () use ($notification_server) {
    $files = glob('/tmp/ratchet_pubsub_*');
    foreach ($files as $file) {
        $content = @file_get_contents($file);
        if ($content) {
            @unlink($file);
            foreach (explode("\n", trim($content)) as $msg) {
                if ($msg) {
                    foreach ($notification_server->clients as $client) {
                        $client->send($msg);
                    }
                }
            }
        }
    }
});

echo "=== Ratchet WebSocket Server Ready ===\n";
echo "Redis Master: {$master['host']}:{$master['port']}\n";
echo "Listening on: 0.0.0.0:8000\n";

$server->run();
