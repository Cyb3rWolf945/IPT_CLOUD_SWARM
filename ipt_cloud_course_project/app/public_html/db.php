<?php
include '_dotenv.php';

// Function to handle database connection
function connectToDatabase($db_host, $db_port, $db_name, $db_user, $db_pass)
{
    try {
        return new PDO("pgsql:host=$db_host;port=$db_port;dbname=$db_name", $db_user, $db_pass);
    } catch (PDOException $e) {
        die("Error: " . $e->getMessage());
    }
}

// Function to truncate the messages table
function truncateTable($pdo)
{
    if (isset($_POST['truncate'])) {
        try {
            // Truncate the table
            $pdo->exec('TRUNCATE TABLE messages');
            return '<div class="alert alert-success">Table truncated successfully!</div>';
        } catch (PDOException $e) {
            return '<div class="alert alert-danger">Error: ' . $e->getMessage() . '</div>';
        }
    }
}

// Function to handle message insertion
function handleMessageInsertion($pdo)
{
    if (isset($_POST['submit'])) {
        $message = $_POST['message'];
        $escapedInput = htmlspecialchars($message, ENT_QUOTES, 'UTF-8');

        // Insert the message into the database
        $stmt = $pdo->prepare("INSERT INTO messages (message) VALUES (?)");
        $stmt->execute([$escapedInput]);

        return '<div class="alert alert-success">Message added successfully!</div>';
    }
}

// Function to delete a message
function deleteMessage($pdo)
{
    if (isset($_POST['delete'])) {
        $id = $_POST['message_id'];

        // Delete the message from the database
        $stmt = $pdo->prepare("DELETE FROM messages WHERE id = ?");
        $stmt->execute([$id]);

        return '<div class="alert alert-success">Message deleted successfully!</div>';
    }
}

// Function to fetch messages from the database
function fetchMessages($pdo)
{
    $stmt = $pdo->query("SELECT * FROM messages ORDER BY id DESC");
    return $stmt->fetchAll(PDO::FETCH_ASSOC);
}

$pdo = connectToDatabase($db_host, $db_port, $db_name, $db_user, $db_pass);

$truncateMessage = truncateTable($pdo);
$insertMessage = handleMessageInsertion($pdo);
$deleteMessage = deleteMessage($pdo);
$messages = fetchMessages($pdo);
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CNV - Project A</title>
    <!-- Load Bootstrap 5.3 CSS from a local copy -->
    <link rel="stylesheet" href="css/bootstrap.min.css">
    <!-- Load custom CSS -->
    <link rel="stylesheet" href="css/site.css">
</head>
<body class="d-flex flex-column">
    <?php include 'partials/navbar.php'; ?>

    <!-- Begin page content -->
    <main class="flex-shrink-0">
        <div class="container mt-5">
            <h1 class="text-center">Message Board</h1>

            <!-- Display message insertion and truncation messages -->
            <?php echo $insertMessage; ?>
            <?php echo $truncateMessage; ?>
            <?php echo $deleteMessage; ?>

            <!-- Display messages table -->
            <?php if (!empty($messages)): ?>
                <table class="table table-dark table-striped">
                    <thead>
                        <tr>
                            <th scope="col">ID</th>
                            <th scope="col">Message</th>
                            <th scope="col">Created At</th>
                            <th scope="col">Actions</th> <!-- Added Actions column -->
                        </tr>
                    </thead>
                    <tbody class="table-group-divider">
                        <?php foreach ($messages as $message): ?>
                            <tr>
                                <th scope="row"><?php echo $message['id']; ?></th>
                                <td><?php echo $message['message']; ?></td>
                                <td><?php echo date('Y-m-d H:i:s', strtotime($message['created_at'])); ?></td>
                                <td>
                                    <form method="POST">
                                        <input type="hidden" name="message_id" value="<?php echo $message['id']; ?>">
                                        <button type="submit" class="btn btn-danger" name="delete" onclick="return confirm('Are you sure you want to delete this message?');">Delete</button>
                                    </form>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            <?php else: ?>
                <p class="text-center">No messages found.</p>
            <?php endif; ?>

            <hr>

            <!-- Display form to insert a new message -->
            <form method="POST">
                <div class="input-group mb-3">
                    <input type="text" class="form-control" id="message" name="message" placeholder="Enter your message" required>
                    <button type="submit" class="btn btn-primary" name="submit">Submit</button>
                </div>
            </form>

            <hr>

            <!-- Display form to truncate table -->
            <form method="POST">
                <button type="submit" class="btn btn-danger" name="truncate" onclick="return confirm('Are you sure you want to truncate the table? This action cannot be undone.');">Truncate Table</button>
            </form>
        </div>
    </main>

    <?php include 'partials/footer.php'; ?>

    <!-- Load Bootstrap 5.3 JS from a local copy -->
    <script src="js/bootstrap.bundle.min.js"></script>
</body>
</html>
