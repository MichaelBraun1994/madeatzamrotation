"""
Main of Made@ZAM Rotation
"""

import logging
import sys
from flask import Flask, render_template, jsonify, url_for

from bot import Bot
from cache import Cache

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
    return render_template("index.html")


def setup_logger():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    return logging.getLogger(__name__)


def start_server():
    logger = setup_logger()

    global bot
    bot = Bot(logger)
    bot.connect()

    global cache
    cache = Cache(bot, logger)
    cache.update(bot.fetch_posts_with_images())

    app.run()
