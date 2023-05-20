#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Script:
    _downloader.py
Description:
    This component periodically download and store random images based
    of specified topics. It uses Unsplash API to get the images and it
    keeps control of the API requests limits, and also keep a maximum
    number of images downloaded by some kind of "image files rotate" of
    the the storage (removing and replacing older images with newer
    ones).
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

# Operating System Library
from os import path, listdir, makedirs
from os import remove as file_remove

# Persistent RAM Library
from pickle import dump as pickle_dump
from pickle import load as pickle_load

# Random Library
from random import choice, randint

# High Level Files Utils Library
from shutil import copyfileobj

# Threads Library
from threading import Thread, Lock

# Time Library
from time import sleep, time

# Error Traceback Library
from traceback import format_exc

# Data Types Library
from typing import Any, Dict, List, Union


###############################################################################
# Third-Party Libraries
###############################################################################

# HTTP Request Library
from requests import get as http_get

# Usplash API Framework
from unsplash.api import Api
from unsplash.auth import Auth


###############################################################################
# Logger Setup
###############################################################################

logger = logging.getLogger(__name__)


###############################################################################
# Class UnsplashRandDownloader
###############################################################################

class UnsplashRandDownloader():
    '''Unsplash Random Image Downloader Manager.'''

    API_REDIRECT_URI: str = "urn:ietf:wg:oauth:2.0:oob"
    USPLASH_REFERRAL: str = "utm_source={}&utm_medium=referral"
    UNSPLASH_URL: str = "https://unsplash.com"
    FILE_IMAGES_DATA_SESSION: str = "session_img_data.pkl"
    T_RETRY_CONNECT_S: int = 30
    MAX_DEMO_REQUESTS_PER_HOUR: int = 50
    MAX_PROD_REQUESTS_PER_HOUR: int = 5000
    API_DEMO: int = MAX_DEMO_REQUESTS_PER_HOUR
    API_PRODUCTION: int = MAX_PROD_REQUESTS_PER_HOUR
    REQUESTS_PER_IMAGE_DOWNLOAD: int = 2
    DEFAULT_IMG_WIDTH: int = 320
    DEFAULT_IMG_HEIGHT: int = 240
    SECONDS_IN_HOUR: int = 3600

    def __init__(
            self,
            application_name: str,
            api_client_id: str,
            api_client_secret: str,
            max_api_requests_per_hour: int = MAX_DEMO_REQUESTS_PER_HOUR
            ):
        '''UnsplashRandDownloader Constructor.'''
        self.thread: Union[Thread, None] = None
        self.th_stop: bool = False
        self.file_locks: Dict[str, Lock] = {}
        self.setup_done: bool = False
        self.app_name: str = application_name
        self.referral: str = self.USPLASH_REFERRAL.format(self.app_name)
        self.unsplash_attribution: str = \
            f"{self.UNSPLASH_URL}/?{self.referral}"
        self.client_id: str = api_client_id
        self.client_secret: str = api_client_secret
        self.redirect_uri: str = self.API_REDIRECT_URI
        self.max_api_requests_per_hour = max_api_requests_per_hour
        self.max_images_per_hour: float = \
            (max_api_requests_per_hour / self.REQUESTS_PER_IMAGE_DOWNLOAD)
        # self.time_to_download_img: float = (3600 / self.max_images_per_hour)
        self.time_to_download_img: float = 10.0
        self.first_image_in_this_hour = True
        self.t_first_down_image: float = time()
        self.api_requests_counter: int = 0
        self.img_width: int = self.DEFAULT_IMG_WIDTH
        self.img_height: int = self.DEFAULT_IMG_HEIGHT
        self.images_dir: str = ""
        self.file_session_path: str = ""
        self.topics: List[str] = []
        self.auth: Union[Auth, None] = None
        self.api: Union[Api, None] = None
        self.connected: bool = False
        self.num_images: int = 0
        self.num_images_topic: Dict[str, int] = {}
        self.images: Dict[str, List] = {}
        for topic in self.topics:
            if topic not in self.images:
                self.images[topic] = []
                self.num_images_topic[topic] = 0

    def save_images_data_session(self) -> bool:
        '''Backup image data of current execution to session file.'''
        images_data = {
            "images": self.images
        }
        if not self.pickle_save(self.file_session_path, images_data):
            logger.error("Fail on backup image data session")
            return False
        logger.debug("Current image data session saved")
        return True

    def restore_images_data_session(self) -> bool:
        '''
        Load backup image data from previous execution session file.
        '''
        if not path.exists(self.file_session_path):
            return False
        images_data = self.pickle_restore(self.file_session_path)
        if images_data is None:
            return False
        self.images = images_data["images"]
        self.num_images = 0
        self.num_images_topic = {}
        self.topics = []
        for topic_images in self.images:
            if topic_images not in self.topics:
                self.topics.append(topic_images)
            self.num_images_topic[topic_images] = 0
            for image in self.images[topic_images]:
                self.file_locks[image["file_path"]] = Lock()
                self.num_images = self.num_images + 1
                self.num_images_topic[topic_images] = \
                    self.num_images_topic[topic_images] + 1
        logger.info("Restored previous image data session")
        return True

    def setup(
            self,
            images_download_dir: str,
            topics: list,
            image_width: int = DEFAULT_IMG_WIDTH,
            image_height: int = DEFAULT_IMG_HEIGHT,
            max_num_images: int = 0
            ):
        '''
        Configure the downloader manager with the topics, maximum number
        of images to download and the seconds between each image
        download.
        '''
        self.images_dir = images_download_dir
        self.topics = topics
        self.img_width = image_width
        self.img_height = image_height
        if max_num_images != 0:
            if max_num_images < self.max_images_per_hour:
                self.max_images_per_hour = max_num_images
        self.images.clear()
        for topic in self.topics:
            if topic not in self.images:
                self.images[topic] = []
                self.num_images_topic[topic] = 0
        self.file_session_path = \
            f"{self.images_dir}/{self.FILE_IMAGES_DATA_SESSION}"
        self.restore_images_data_session()
        self.setup_done = True
        logger.info(
                "Download an image each ~%d seconds",
                self.time_to_download_img)
        logger.info(
                "Maximum number of images to download: %d",
                self.max_images_per_hour)
        logger.info("Setup done")

    def get_random_image(self) -> Union[dict, None]:
        '''Get an image from the already downloaded images.'''
        if not self.setup_done:
            return None
        if self.num_images == 0:
            return None
        topics_with_any_image = []
        for topic in self.topics:
            if len(self.images[topic]) > 0:
                topics_with_any_image.append(topic)
        if len(topics_with_any_image) == 0:
            return None
        random_topic = choice(topics_with_any_image)
        random_image = choice(self.images[random_topic])
        image = self.file_read(random_image["file_path"])
        if image is None:
            self.images[random_topic].remove(random_image)
            self.num_images = self.num_images - 1
            self.num_images_topic[random_topic] = \
                self.num_images_topic[random_topic] - 1
            return None
        image_data = {
            "attribution": random_image["attribution"],
            "id": random_image["id"],
            "image": image,
            "topic": random_topic
        }
        logger.debug("Image from topic %s taken", random_topic)
        return image_data

    def start(self) -> bool:
        '''Launch UnsplashRandDownloader manager thread.'''
        if not self.setup_done:
            return False
        if self.thread is not None:
            return False
        try:
            self.thread = Thread(target=self.manage, name=f"th_{__name__}")
            if self.thread is None:
                return False
            self.th_stop = False
            self.thread.start()
        except Exception:
            logger.error(format_exc())
            return False
        return True

    def stop(self) -> bool:
        '''
        Request to stop UnsplashRandDownloader manager thread and wait
        for it.
        '''
        if self.thread is None:
            return False
        self.th_stop = True
        if self.thread.is_alive():
            self.thread.join()
        return True

    def manage(self):
        '''
        Unsplash Random Image Downloader Manager main functionality.
        It periodically downloads random images from configured topics
        and control the number of downloaded image files by removing
        older ones and downloading new ones (image files rotate).
        '''
        first_iteration = True
        logger.info("Start Running")
        while not self.th_stop:
            # Do nothing if API limit has been reached
            if self.api_requests_counter == self.max_api_requests_per_hour:
                logger.info("Unsplash API Limit Reached, waiting next hour")
                # Check if a new hour has come and reset limit
                if time() - self.t_first_down_image > self.SECONDS_IN_HOUR:
                    logger.info("Unsplash API Limit Reset (new hour)")
                    self.api_requests_counter = 0
                    self.first_image_in_this_hour = True
                sleep(60)
                continue
            # Manage connection to Unsplash API
            if not self.connected:
                self.connect()
                # Wait T_RETRY_CONNECT_S seconds for next retry if
                # connection fail
                if not self.connected:
                    sleep(self.T_RETRY_CONNECT_S)
                    logger.debug("Fail to auth and connect to Unsplash API.")
                    logger.debug("Retrying...")
                    continue
            # Wait time to try download a new image
            if not first_iteration:
                rand_time = randint(0, 10)
                sleep(self.time_to_download_img + rand_time)
            first_iteration = False
            # Remove an image when max number of images are downloaded
            if self.num_images >= self.max_images_per_hour:
                topic = self.get_topic_more_num_images()
                image = choice(self.images[topic])
                if not self.remove_image_file(image["file_path"]):
                    continue
                self.images[topic].remove(image)
                self.num_images = self.num_images - 1
                self.num_images_topic[topic] = self.num_images_topic[topic] - 1
                logger.info("Image from topic %s removed", topic)
            else:
                topic = self.get_topic_less_num_images()
            if topic == "":
                continue
            # Download a new image and save it to a file
            logger.debug("Downloading Image of topic %s", topic)
            image = self.download_image(topic, self.img_width, self.img_height)
            if image is None:
                continue
            if self.first_image_in_this_hour:
                self.first_image_in_this_hour = False
                self.t_first_down_image = time()
            img_file_name = f"{topic}_{self.num_images_topic[topic]}.jpg"
            image["file_path"] = f"{self.images_dir}/{img_file_name}"
            if not self.save_data_to_file(image["file_path"], image["raw"]):
                continue
            # Store the image in the images dictionary and count it
            self.images[topic].append(image)
            self.file_locks[image["file_path"]] = Lock()
            self.num_images = self.num_images + 1
            self.num_images_topic[topic] = self.num_images_topic[topic] + 1
            logger.info("Image %s downloaded", img_file_name)
            # Save current image data to persistent session file
            self.save_images_data_session()
        logger.info("Stopped")

    def connect(self) -> bool:
        '''Authenticate to Unsplash API Service.'''
        logger.info("Connecting to Unsplash API...")
        try:
            self.auth = Auth(
                    self.client_id,
                    self.client_secret,
                    self.redirect_uri,
                    code=""
            )
            self.api = Api(self.auth)
            self.connected = True
            logger.info("Connected to Unsplash API")
        except Exception:
            logger.error(format_exc())
            self.connected = False
        return self.connected

    def download_image(
            self,
            topic: str,
            width: int,
            height: int
            ) -> Union[dict, None]:
        '''
        Send a Request to Unspash API for getting a random image data,
        then get the URL of the image, request to download it and send
        a request to notify Unsplash the download.
        '''
        image: Dict = {}
        logger.debug("Downloading Image of topic: %s", topic)
        if self.api is None:
            logger.error("API not initialized")
            return None
        try:
            img_data = self.api.photo.random(
                    query=topic, w=width, h=height, orientation="landscape")
            if img_data is None:
                logger.error("Unsplash get random image fail")
                return None
            self.api_requests_counter = self.api_requests_counter + 1
            img_data = img_data[0]
            img_url = img_data.urls.small
            photographer = (
                f"<a href=\"{img_data.user.links.html}?{self.referral}\">"
                f"{img_data.user.name}</a>")
            attribution = (
                f"Photo by {photographer} on "
                f"<a href=\"{self.unsplash_attribution}\">Unsplash</a>")
            response = http_get(img_url, stream=True, timeout=5.0)
            if response.status_code != 200:
                logger.error("Unsplash Request Fail: %d", response.status_code)
                return None
            logger.debug("Image successfully Downloaded")
            response.raw.decode_content = True
            image["raw"] = response.raw
            image["attribution"] = attribution
            image["id"] = img_data.id
            self.api.photo.download(img_data.id)
            self.api_requests_counter = self.api_requests_counter + 1
        except Exception:
            logger.error(format_exc())
            return None
        return image

    def save_data_to_file(
            self,
            file_path: str,
            data: Any
            ) -> bool:
        '''Save file object data into a filesystem file.'''
        save_ok = False
        logger.debug("Saving file %s ...", file_path)
        if not self.create_file_dir(file_path):
            return False
        if file_path in self.file_locks:
            self.file_locks[file_path].acquire()
        try:
            with open(file_path, "wb") as file:
                copyfileobj(data, file)
            save_ok = True
            logger.debug("Save Ok")
        except Exception:
            logger.error(format_exc())
            save_ok = False
        if file_path in self.file_locks:
            self.file_locks[file_path].release()
        return save_ok

    def remove_image_file(
            self,
            file_path: str
            ) -> bool:
        '''Remove a file from the filesystem.'''
        remove_ok = False
        logger.debug("Removing file %s ...", file_path)
        if file_path in self.file_locks:
            self.file_locks[file_path].acquire()
        try:
            if path.exists(file_path):
                file_remove(file_path)
                remove_ok = True
                logger.debug("Remove Ok")
            else:
                logger.debug("Remove fail, file does not exist")
        except Exception:
            logger.error(format_exc())
        if file_path in self.file_locks:
            self.file_locks[file_path].release()
        return remove_ok

    def file_read(
            self,
            file_path: str
            ) -> Union[bytes, None]:
        '''Read a binary file (read an image).'''
        read_data = None
        logger.debug("Reading file %s ...", file_path)
        if file_path in self.file_locks:
            self.file_locks[file_path].acquire()
        try:
            with open(file_path, "rb") as file:
                read_data = file.read(-1)
        except Exception:
            logger.error(format_exc())
        if file_path in self.file_locks:
            self.file_locks[file_path].release()
        return read_data

    def create_file_dir(
            self,
            file_path: str
            ) -> bool:
        '''
        Create all the directories of a file path, it doesn't exists
        (mkdir -p file_path).
        '''
        directory_path = path.dirname(file_path)
        if path.exists(directory_path):
            return True
        try:
            makedirs(directory_path)
        except Exception:
            logger.error(format_exc())
            return False
        return True

    def list_files_in_directory(
            self,
            directory_path: str
            ) -> list:
        '''Get a list of the files that provided directory contains.'''
        list_files = []
        for dir_or_file in listdir(directory_path):
            if path.isfile(path.join(directory_path, dir_or_file)):
                list_files.append(dir_or_file)
        return list_files

    def get_topic_more_num_images(self) -> str:
        '''Return the topic that has more images downloaded.'''
        more_num_images_topics = []
        more_len = 0
        # Get topic with higher number of images
        for topic in self.topics:
            if len(self.images[topic]) > more_len:
                more_len = len(self.images[topic])
        # Check if other topics has the same number of images
        for topic in self.topics:
            if len(self.images[topic]) == more_len:
                more_num_images_topics.append(topic)
        return choice(more_num_images_topics)

    def get_topic_less_num_images(self) -> str:
        '''Return the topic that has less images downloaded.'''
        less_num_images_topic = ""
        less_len = self.max_images_per_hour
        for topic in self.topics:
            if len(self.images[topic]) <= less_len:
                less_len = len(self.images[topic])
                less_num_images_topic = topic
        return less_num_images_topic

    def pickle_save(
            self,
            pickle_file_path: str,
            data: Any
            ) -> bool:
        '''Save data to pickle file.'''
        try:
            with open(pickle_file_path, "wb") as file:
                pickle_dump(data, file)
        except Exception:
            logger.error(format_exc())
            return False
        return True

    def pickle_restore(
            self,
            pickle_file_path: str
            ):
        '''Load data from pickle file.'''
        try:
            with open(pickle_file_path, "rb") as file:
                last_session_data = pickle_load(file)
        except Exception:
            logger.error(format_exc())
            return None
        return last_session_data
