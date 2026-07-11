<?php
include '_dotenv.php';

session_set_cookie_params(86400); // Set the session cookie's lifetime to 24 hours (in seconds)
session_start();

// Check if the destroy session button is clicked
if (isset($_POST['destroy'])) {
    session_destroy();
    header('Location: ' . $_SERVER['PHP_SELF']);
    exit();
}

// Check if the name is submitted and save it to the session
if (isset($_POST['save'])) {
    $name = $_POST['name'];
    $escapedInput = htmlspecialchars($name, ENT_QUOTES, 'UTF-8');
    $_SESSION['name'] = $escapedInput;
    // Redirect to avoid form resubmission on page reload
    header('Location: ' . $_SERVER['PHP_SELF']);
    exit();
}

// Check if the session name is set
if (isset($_SESSION['name'])) {
    $savedName = $_SESSION['name'];
    $welcomeMessage = "Hello <b>$savedName</b>, welcome back!";
} else {
    $welcomeMessage = "Welcome! Please enter your name.";
}
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
            <div class="row">
                <div class="col-md-6 offset-md-3">
                    <h1 class="text-center">Session Example</h1>
                    <p class="lead text-center"><?php echo $welcomeMessage; ?></p>
                    <form method="POST">
                        <div class="input-group mb-3">
                            <input type="text" class="form-control" name="name" placeholder="Enter your name" required>
                            <button type="submit" class="btn btn-primary" name="save">Save</button>
                        </div>
                    </form>
                    <form method="POST">
                        <div class="text-center">
                            <button type="submit" class="btn btn-danger" name="destroy">Destroy Session</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </main>
    <?php include 'partials/footer.php'; ?>
    <!-- Load Bootstrap 5.3 JS from a local copy -->
    <script src="js/bootstrap.bundle.min.js"></script>
</body>
</html>
