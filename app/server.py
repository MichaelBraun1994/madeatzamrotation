"""
Main of Made@ZAM Rotation
"""

import logging
import sys
import time
import os
import threading
from flask import Flask, render_template, jsonify, url_for
from dotenv import load_dotenv

from bot import Bot
from cache import Cache
from settings import Settings


def create_app():
    setup_server()

    app = Flask(__name__)

    @app.route("/api/images")
    def get_image_urls():
        image_posts = cache.get_posts()

        images = []

        for image_post in image_posts:
            image_post["image_files"] = [
                url_for("static", filename=image_path)
                for image_path in image_post["image_files"]
            ]

            first_image_of_post = True
            for image_path in image_post["image_files"]:
                image = {}
                image["file"] = image_path
                image["username"] = image_post["username"]

                if first_image_of_post:
                    image["message"] = image_post["message"]
                else:
                    image["message"] = ""

                images.append(image)
                first_image_of_post = False

        return jsonify(images)

    @app.route("/")
    def index():
        return render_template(
            "index.html",
            image_fetching_interval=settings.frontend_images_fetching_interval,
            polaroid_batch_presentation_duration=settings.frontend_polaroid_batch_presentation_duration,
        )

    return app


def setup_logger():
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


def fetch_posts():
    cache.update(bot.fetch_posts_with_images())


def start_periodic_posts_fetching(interval_seconds):
    def fetch_posts_task():
        while True:
            time.sleep(interval_seconds)
            fetch_posts()

    thread = threading.Thread(target=fetch_posts_task, daemon=True)
    thread.start()


def setup_server():
    load_dotenv()

    logger = setup_logger()

    global settings
    settings_file_path = os.getenv("MADEATZAM_CONFIG_FILE_PATH")
    logger.info(f"Loading settings file: {settings_file_path}")
    settings = Settings(settings_file_path)

    global bot
    bot = Bot(settings, logger)
    bot.connect()

    global cache
    cache = Cache(bot, logger)

    start_periodic_posts_fetching(settings.backend_posts_fetching_interval)
    fetch_posts()

    logger.info("Starting server")
