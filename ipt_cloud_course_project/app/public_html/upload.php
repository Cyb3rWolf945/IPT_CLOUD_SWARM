<?php
include '_dotenv.php';

use Aws\S3\S3Client;
use Aws\Exception\AwsException;

// Initialize MinIO S3 Client
$s3Client = new S3Client([
    'version' => 'latest',
    'region'  => 'us-east-1',
    'endpoint' => 'http://minio:9000',
    'use_path_style_endpoint' => true,
    'credentials' => [
        'key'    => 'admin',
        'secret' => 'ipt_cloud_2026',
    ],
]);
$bucket = 'gallery';

// Function to handle file upload
function handleFileUpload($s3Client, $bucket)
{
    if (isset($_POST['submit'])) {
        $fileName = basename($_FILES['image']['name']);
        $fileType = pathinfo($fileName, PATHINFO_EXTENSION);
        $tmpName = $_FILES['image']['tmp_name'];

        // Check if the uploaded file is a JPG image
        if ($fileType === 'jpg' || $fileType === 'jpeg') {
            try {
                $s3Client->putObject([
                    'Bucket' => $bucket,
                    'Key'    => $fileName,
                    'SourceFile' => $tmpName,
                    'ContentType' => 'image/jpeg'
                ]);
                return '<div class="alert alert-success">Image uploaded successfully to MinIO!</div>';
            } catch (AwsException $e) {
                return '<div class="alert alert-danger">Error uploading file: ' . $e->getMessage() . '</div>';
            }
        } else {
            return '<div class="alert alert-danger">Please upload a JPG image.</div>';
        }
    }
}

// Function to handle clear gallery button click
function handleClearGallery($s3Client, $bucket)
{
    if (isset($_POST['clear'])) {
        try {
            $objects = $s3Client->listObjectsV2([
                'Bucket' => $bucket
            ]);
            
            if (isset($objects['Contents'])) {
                foreach ($objects['Contents'] as $object) {
                    $s3Client->deleteObject([
                        'Bucket' => $bucket,
                        'Key' => $object['Key']
                    ]);
                }
            }
            return '<div class="alert alert-success">Gallery cleared successfully from MinIO!</div>';
        } catch (AwsException $e) {
            return '<div class="alert alert-danger">Error clearing gallery: ' . $e->getMessage() . '</div>';
        }
    }
}

// Function to delete an individual image
function deleteImage($s3Client, $bucket, $key)
{
    if (isset($_POST['delete'])) {
        try {
            $s3Client->deleteObject([
                'Bucket' => $bucket,
                'Key' => $key
            ]);
            return '<div class="alert alert-success">Image deleted successfully from MinIO!</div>';
        } catch (AwsException $e) {
            return '<div class="alert alert-danger">Error deleting image: ' . $e->getMessage() . '</div>';
        }
    }
}

// Call functions to handle file upload, delete image, and clear gallery
$uploadMessage = handleFileUpload($s3Client, $bucket);
$clearMessage = handleClearGallery($s3Client, $bucket);
$deleteMessage = isset($_POST['delete']) ? deleteImage($s3Client, $bucket, $_POST['delete']) : '';
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
            <h1 class="text-center">Image Upload (Powered by MinIO)</h1>

            <!-- Display upload, clear gallery, and delete image messages -->
            <?php echo $uploadMessage; ?>
            <?php echo $clearMessage; ?>
            <?php echo $deleteMessage; ?>

            <div class="row">
                <div class="col-md-6">
                    <!-- Display file upload form -->
                    <form method="POST" enctype="multipart/form-data">
                        <div class="input-group mb-3">
                            <input type="file" class="form-control" name="image" accept=".jpg, .jpeg">
                            <button type="submit" class="btn btn-primary" name="submit">Upload</button>
                        </div>
                    </form>
                </div>
                <div class="col-md-6">
                    <!-- Display clear gallery button -->
                    <form method="POST">
                        <div class="form-group mt-md-4">
                            <button type="submit" class="btn btn-danger" name="clear">Clear Gallery</button>
                        </div>
                    </form>
                </div>
            </div>

            <hr>

            <!-- Display image gallery with delete buttons -->
            <div class="row">
                <?php
                try {
                    $objects = $s3Client->listObjectsV2([
                        'Bucket' => $bucket
                    ]);
                    
                    if (isset($objects['Contents'])) {
                        foreach ($objects['Contents'] as $object) {
                            $key = $object['Key'];
                            // Nginx proxies /gallery/ to MinIO
                            $imageUrl = '/gallery/' . $key;
                            
                            echo '<div class="col-md-4 mb-3">';
                            echo '<img src="' . htmlspecialchars($imageUrl) . '" class="img-fluid">';
                            echo '<form method="POST" class="mt-2">';
                            echo '<input type="hidden" name="delete" value="' . htmlspecialchars($key) . '">';
                            echo '<button type="submit" class="btn btn-danger btn-sm">Delete</button>';
                            echo '</form>';
                            echo '</div>';
                        }
                    }
                } catch (AwsException $e) {
                    echo '<div class="col-12"><div class="alert alert-warning">Could not load gallery from MinIO: ' . $e->getMessage() . '</div></div>';
                }
                ?>
            </div>
        </div>
    </main>
    <?php include 'partials/footer.php'; ?>
    <!-- Load Bootstrap 5.3 JS from a local copy -->
    <script src="js/bootstrap.bundle.min.js"></script>
</body>
</html>
