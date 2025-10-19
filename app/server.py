"""
Main of Made@ZAM Rotation
"""

import logging
import sys
import time
import threading
from flask import Flask, render_template, jsonify, url_for

from bot import Bot
from cache import Cache
from settings import Settings

app = Flask(__name__)


@app.route("/api/images")
def get_image_urls():
    image_posts = cache.get_posts()

    for image_post in image_posts:
        image_post["image_files"] = [
            url_for("static", filename=image_path)
            for image_path in image_post["image_files"]
        ]

    return jsonify(image_posts)


@app.route("/")
def index():
    return render_template(
        "index.html",
        image_fetching_interval=settings.frontend_images_fetching_interval,
        image_rotation_interval=settings.frontend_image_rotation_interval,
    )


def setup_logger():
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


def start_periodic_posts_fetching(interval_seconds):
    def fetch_posts_task():
        while True:
            cache.update(bot.fetch_posts_with_images())
            time.sleep(interval_seconds)

    thread = threading.Thread(target=fetch_posts_task, daemon=True)
    thread.start()


def start_server(settings_path):
    logger = setup_logger()

    global settings
    settings = Settings(settings_path)

    global bot
    bot = Bot(settings, logger)
    bot.connect()

    global cache
    cache = Cache(bot, logger)

    start_periodic_posts_fetching(settings.backend_posts_fetching_interval)
    app.run()
