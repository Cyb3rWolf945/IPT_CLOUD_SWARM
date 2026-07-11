<?php include '_dotenv.php'; ?>
<?php
// Start session for user identification
session_set_cookie_params(86400);
session_start();
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CNV - Project A</title>
    <link rel="stylesheet" href="css/bootstrap.min.css">
    <link rel="stylesheet" href="css/site.css">
</head>
<body class="d-flex flex-column">
    <?php include 'partials/navbar.php'; ?>

    <main class="flex-shrink-0">
        <div class="container">
            <h1 class="mt-5">WebSockets <span class="badge bg-success" id="onlineCount">0</span> online</h1>

            <div class="container py-4">
                <div class="alert alert-warning alert-dismissible fade show" role="alert" id="statusDiv">
                    Connecting to the WebSockets server...
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
                
                <div class="notifications" id="notificationDiv"></div>

                <form id="messageForm">
                    <div class="mb-3 d-flex">
                        <input type="text" id="messageInput" class="form-control me-2" placeholder="Enter a message">
                        <button type="submit" class="btn btn-primary">Send</button>
                    </div>
                </form>
            </div>
        </div>
    </main>

    <?php include 'partials/footer.php'; ?>

    <script src="js/bootstrap.bundle.min.js"></script>
    <script>
        const ws_host = window.location.host;
        const ws_uri = "ws://" + ws_host + "/ws/";
        const user_id = "<?php echo session_id(); ?>";
    </script>
    <script src="js/websockets.js?v=2" defer></script>
</body>
</html>
