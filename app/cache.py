import shutil
from typing import List
from image_posts import ImagePost
from bot import Bot
from logging import Logger

import os
import json


class Cache:
    def __init__(self, bot: Bot, logger: Logger):
        self.bot = bot
        self.logger = logger
        self.cache_path = os.path.join(os.path.dirname(__file__), "static/cache")
        pass

    def update(self, fetched_posts: ImagePost):
        os.makedirs(self.cache_path, exist_ok=True)

        self.clean_cache_from_old_posts(fetched_posts)

        for post in fetched_posts:
            if not self.is_cache_entry_valid(post):
                self.cache_post(post)
            else:
                self.logger.info(f"Cache hit {post.post_id}")

        self.logger.info("Finished caching posts")

    def get_posts(self):
        jpg_files = []
        for root, dirs, files in os.walk(self.cache_path):
            for file in files:
                if file.lower().endswith(".jpg"):
                    relative_path = os.path.relpath(
                        os.path.join(root, file), start=self.cache_path
                    )
                    jpg_files.append(relative_path)
        return jpg_files

    def cache_post(self, post: ImagePost):
        cache_entry_path = self.get_cache_entry_path(post)
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
        filepath = os.path.join(self.get_cache_entry_path(post), "meta.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def get_cache_entry_path(self, post: ImagePost):
        return os.path.join(self.cache_path, post.post_id)

    def is_cache_entry_valid(self, post: ImagePost) -> bool:
        cache_entry_path = self.get_cache_entry_path(post)
        if not os.path.exists(cache_entry_path):
            return False

        if post.update_at != self.get_cache_entry_last_update(post):
            return False

        return True

    def get_cache_entry_last_update(self, post: ImagePost):
        metadata_filepath = os.path.join(self.get_cache_entry_path(post), "meta.json")
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
            shutil.rmtree(os.path.join(self.cache_path, post_to_remove))
            self.logger.info(f"Removed cache entry {post_to_remove}")
