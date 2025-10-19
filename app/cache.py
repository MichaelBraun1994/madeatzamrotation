import shutil
from typing import List
from image_posts import ImagePost
from bot import Bot
from logging import Logger

import os
import json
import threading


class Cache:
    """
    Local cache of posts with images.
    """

    def __init__(self, bot: Bot, logger: Logger):
        self.bot = bot
        self.logger = logger
        self.update_lock = threading.Lock()
        self.cache_path = os.path.join(os.path.dirname(__file__), "static/cache")
        pass

    def update(self, fetched_posts: ImagePost):
        with self.update_lock:
            self.logger.info("Updating cache")
            os.makedirs(self.cache_path, exist_ok=True)

            self.clean_cache_from_old_posts(fetched_posts)

            for post in fetched_posts:
                if not self.is_cache_entry_valid(post):
                    self.cache_post(post)
                else:
                    self.logger.info(f"\tCache hit {post.post_id}")

    def get_cached_post_ids(self):
        return [
            name
            for name in os.listdir(self.cache_path)
            if os.path.isdir(os.path.join(self.cache_path, name))
        ]

    def get_posts(self):
        with self.update_lock:
            posts = []

            for post_id in self.get_cached_post_ids():
                posts.append(self.read_cache_entry(post_id))

            return posts

    def cache_post(self, post: ImagePost):
        cache_entry_path = self.get_cache_entry_path(post.post_id)
        os.makedirs(cache_entry_path, exist_ok=True)

        self.cache_post_metadata(post)
        self.bot.fetch_images_of_post(post, cache_entry_path)

    def cache_post_metadata(self, post: ImagePost):
        data = {
            "create_at": post.create_at,
            "update_at": post.update_at,
            "user_id": post.user_id,
            "username": post.username,
            "message": post.message,
        }
        filepath = os.path.join(self.get_cache_entry_path(post.post_id), "meta.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def read_cache_entry(self, post_id):
        image_cache_path = self.get_cache_entry_path(post_id)

        filepath = os.path.join(image_cache_path, "meta.json")
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        username = data.get("username")
        message = data.get("message")

        image_files = [
            os.path.join("cache", post_id, file_name)
            for file_name in os.listdir(image_cache_path)
            if file_name != "meta.json"
        ]

        return {"username": username, "message": message, "image_files": image_files}

    def get_cache_entry_path(self, post_id):
        return os.path.join(self.cache_path, post_id)

    def is_cache_entry_valid(self, post: ImagePost) -> bool:
        cache_entry_path = self.get_cache_entry_path(post.post_id)
        if not os.path.exists(cache_entry_path):
            return False

        if post.update_at != self.get_cache_entry_last_update(post):
            return False

        return True

    def get_cache_entry_last_update(self, post: ImagePost):
        metadata_filepath = os.path.join(
            self.get_cache_entry_path(post.post_id), "meta.json"
        )
        with open(metadata_filepath, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data.get("update_at")

    def clean_cache_from_old_posts(self, fetched_posts: List[ImagePost]):
        """Deletes old cache entries of posts that are no longer relevant or got removed"""
        cache_entries = [
            post_id
            for post_id in os.listdir(self.cache_path)
            if os.path.isdir(os.path.join(self.cache_path, post_id))
        ]

        new_post_ids = [post.post_id for post in fetched_posts]
        posts_to_remove = [
            cache_entry
            for cache_entry in cache_entries
            if cache_entry not in new_post_ids
        ]

        for post_to_remove in posts_to_remove:
            self.logger.info(f"\tRemove cache entry {post_to_remove}")
            shutil.rmtree(os.path.join(self.cache_path, post_to_remove))
