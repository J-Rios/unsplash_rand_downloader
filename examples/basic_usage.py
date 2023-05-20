#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Script:
    basic_usage.py
Description:
    Test unsplash_rand_downloader library to get random images from some
    specified topics.
Author:
    Jose Miguel Rios Rubio
Creation date:
    22/01/2023
Last modified date:
    22/01/2023
Version:
    1.0.0
'''

###############################################################################
# Standard Libraries
###############################################################################

# Logging Library
import logging

from unsplash_rand_downloader import UnsplashRandDownloader
from time import sleep
from traceback import format_exc


###############################################################################
# Logger Setup
###############################################################################

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


###############################################################################
# Constants & Configurations
###############################################################################

APP_NAME = "XXXXXXXXXXXXX"
CLIENT_ID = "XXXXXXXXXXX_XXXXX-XX-XXXXXXXXXXXXXXXXXXXXXX"
CLIENT_SECRET = "XXXXXX-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

API_MODE = UnsplashRandDownloader.API_DEMO
LIMIT_MAX_NUM_IMG = 3
IMAGES_DOWNLOAD_DIR = "images"
IMG_WIDTH = 320
IMG_HEIGHT = 240
TOPICS = ["water", "fire", "lightning"]


###############################################################################
# Main Function
###############################################################################

def main():
    '''Main Function'''
    # Check for User Setup
    if (APP_NAME == "XXXXXXXXXXXXX") \
    or (CLIENT_ID == "XXXXXXXXXXX_XXXXX-XX-XXXXXXXXXXXXXXXXXXXXXX") \
    or (CLIENT_SECRET == "XXXXXX-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"):
        logging.error("You need to set your Unsplash App, ID and Secret keys.")
        logging.error("Please modify the next lines of code:")
        logging.error("APP_NAME = \"XXXXXXXXXXXXX\"")
        logging.error(
            "CLIENT_ID = \"XXXXXXXXXXX_XXXXX-XX-XXXXXXXXXXXXXXXXXXXXXX\"")
        logging.error(
            "CLIENT_SECRET = \"XXXXXX-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\"")
        exit(1)
    # Launch Demo
    logging.info("Test Start")
    unsplash = UnsplashRandDownloader(APP_NAME, CLIENT_ID, CLIENT_SECRET,
            API_MODE)
    unsplash.setup(IMAGES_DOWNLOAD_DIR, TOPICS, IMG_WIDTH, IMG_HEIGHT,
            LIMIT_MAX_NUM_IMG)
    unsplash.start()
    try:
        while True:
            img = unsplash.get_random_image()
            if img is not None:
                logging.info("----------")
                logging.info("Image Topic: {}".format(img["topic"]))
                logging.info("Image ID: {}".format(img["id"]))
                logging.info("Attribution: {}".format(img["attribution"]))
                #logging.info("Image Raw: {}".format(img["image"]))
                logging.info("----------")
            else:
                logging.info("No img")
            sleep(5)
    except Exception:
        logging.error("{}".format(format_exc()))
    unsplash.stop()
    logging.info("Test Done")
    exit(0)


###############################################################################
# Runnable Main Script Detection
###############################################################################

if __name__ == "__main__":
    main()
