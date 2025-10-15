"""
Main of Made@ZAM Rotation
"""

import logging
import sys
import os
from flask import Flask, render_template
from posts_cache import create_post_cache, get_cache_path


app = Flask(__name__)


def get_image_paths(subfolder):
    jpg_files = []
    for root, dirs, files in os.walk(subfolder):
        for file in files:
            if file.lower().endswith(".jpg"):
                relative_path = os.path.relpath(
                    os.path.join(root, file), start=subfolder
                )
                jpg_files.append(relative_path)
    return jpg_files


@app.route("/")
def index():
    imagepaths = get_image_paths(get_cache_path())
    return render_template("index.html", imagepaths=imagepaths)


def setup_logger():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    return logging.getLogger(__name__)


def start_server():
    logger = setup_logger()
    create_post_cache(logger)
    app.run()
    # app.run(debug=True)
