# UnsplashRandDownloader

Python Unsplash Random Image Downloader.

This component periodically download and store random images based of specified topics from Unsplash platform and allows the user to request one of the downloaded images. It keeps control of the Unsplash API requests limits, and using some kind of "image files rotate" of the storage (removing and replacing older images with newer ones), it also control and limit the maximum number of images downloaded in the filesytem.

## Installation

From Pypi:

```bash
python3 -m pip install unsplash_rand_downloader
```

From Sources:

```bash
git clone https://www.github.com/J-Rios/unsplash_rand_downloader
cd unsplash_rand_downloader
python3 -m pip install .
```

## Usage

```py

# Import the module
from unsplash_rand_downloader import UnsplashRandDownloader

# Set your Unsplash API access account identification parameters
# (Application Name, Client ID and Client Secret Key)
APP_NAME = "XXXXXXXXXXXXXXX"
CLIENT_ID = "XXXXXXXXXXX_XXXXX-XX-XXXXXXXXXXXXXXXXXXXXXX"
CLIENT_SECRET = "XXXXXX-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# Unsplash API mode to use (API_DEMO or API_PRODUCTION)
API_MODE = UnsplashRandDownloader.API_DEMO

# Limit the number of images to be downloaded (None, to use the maximum
# calculated number from Unsplash API request limits DEMO/PRODUCTION)
LIMIT_MAX_NUM_IMG = None

# Path of directory to store the downloaded images
IMAGES_DOWNLOAD_DIR = "./images"

# Size of images to download
IMG_WIDTH = 320
IMG_HEIGHT = 240

# Topics of images to download
TOPICS = ["bird", "halloween", "fire", "computer"]

# Setup the Downloader
unsplash = UnsplashRandDownloader(APP_NAME, CLIENT_ID, CLIENT_SECRET, API_MODE)
unsplash.setup(IMAGES_DOWNLOAD_DIR, TOPICS, IMG_WIDTH, IMG_HEIGHT,
               LIMIT_MAX_NUM_IMG)

# Launch the Downloader
unsplash.start()

# Wait some time to allow UnsplashRandDownloader download some images
# ...

# Request a random image from downloaded images
img = unsplash.get_random_image()
if img is not None:
    print("Image Topic: {}".format(img["topic"]))
    print("Image ID: {}".format(img["id"]))
    print("Image Attribution: {}".format(img["attribution"]))
    #print("Image Raw: {}".format(img["image"]))

# To exit your application, remember to stop the downloader before
unsplash.stop()
```
