"""
Caching of image posts from the made@ZAM mattermost channel
"""

import os
import json
import shutil
import logging
from typing import List
from dotenv import load_dotenv
from mattermostdriver import Driver


def create_post_cache(logger: logging.Logger):
    driver = connect_to_mattermost(get_bot_secrets_from_env(), logger)
    posts = fetch_posts_metadata_from_channel(10, driver, logger)
    cache_posts(posts, driver, logger)

    driver.logout()
    logger.info("Logged out")


class BotSecrets:
    def __init__(self, username, token):
        self.username = username
        self.token = token


def connect_to_mattermost(secrets: BotSecrets, logger: logging.Logger) -> Driver:
    driver = Driver(
        {
            "url": "chat.zam.haus",
            "token": secrets.token,
            "port": 443,
            "scheme": "https",
            "verify": True,
            "basepath": "/api/v4",
            "timeout": 30,
        }
    )

    driver.login()
    logger.info("Logged in")

    return driver


def get_bot_secrets_from_env() -> BotSecrets:
    load_dotenv()

    username_env_variable = "MATTERMOST_BOT_USERNAME"
    token_env_variable = "MATTERMOST_BOT_TOKEN"

    username = os.getenv(username_env_variable)
    if username is None:
        raise RuntimeError(f"{username_env_variable} is not set.")

    token = os.getenv(token_env_variable)
    if token is None:
        raise RuntimeError(f"{token_env_variable} is not set.")

    return BotSecrets(username, token)


class PostMetaData:
    def __init__(
        self, post_id, create_at, update_at, user_id, username, message, file_ids
    ):
        self.post_id = post_id
        self.create_at = create_at
        self.update_at = update_at
        self.user_id = user_id
        self.username = username
        self.message = message
        self.file_ids = file_ids


def is_image(file_id, driver: Driver) -> bool:
    file_info = driver.files.get_file_metadata(file_id)
    file_type = file_info.get("mime_type")
    return file_type.startswith("image/")


def fetch_posts_metadata_from_channel(
    posts_limit, driver: Driver, logger: logging.Logger
) -> List[PostMetaData]:
    team_name = "ZAM"
    channel_name = "made-at-zam"
    team = driver.teams.get_team_by_name(team_name)
    channel = driver.channels.get_channel_by_name(team["id"], channel_name)

    posts = driver.posts.get_posts_for_channel(
        channel["id"], params={"page": 0, "per_page": posts_limit}
    )
    logger.info("Fetched posts metadata")

    post_ids_with_files = filter(
        lambda post_id: posts["posts"][post_id].get("file_ids"),
        reversed(posts["order"]),
    )

    image_posts = []

    for post_id in post_ids_with_files:
        post = posts["posts"][post_id]
        post_message = post["message"]
        post_create_at = post["create_at"]
        post_update_at = post["update_at"]
        post_user_id = post["user_id"]
        post_image_ids = list(
            filter(lambda file_id: is_image(file_id, driver), post["file_ids"])
        )

        user = driver.users.get_user(post_user_id)
        post_username = user["username"]

        if len(post_image_ids) != 0:
            image_posts.append(
                PostMetaData(
                    post_id,
                    post_create_at,
                    post_update_at,
                    post_user_id,
                    post_username,
                    post_message,
                    post_image_ids,
                )
            )

    return image_posts


def export_metadata(post: PostMetaData, export_dir):
    data = {
        "create_at": post.create_at,
        "update_at": post.update_at,
        "user_id": post.user_id,
        "username": post.username,
        "message": post.message,
    }
    filepath = os.path.join(export_dir, "meta.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def fetch_images_of_post(
    post: PostMetaData, output_path, driver: Driver, logger: logging.Logger
):
    for file_id in post.file_ids:
        file_info = driver.files.get_file_metadata(file_id)
        file_extension = file_info.get("extension")
        file_name = file_id + "." + file_extension

        with open(os.path.join(output_path, file_name), "wb") as f:
            file_bytes = driver.files.get_file(file_id).content
            f.write(file_bytes)
            logger.info(f"\tFetched {file_name}")


def get_cache_entry_path(post: PostMetaData):
    return os.path.join("cache", post.post_id)


def create_post_cache_entry(post: PostMetaData, driver: Driver, logger: logging.Logger):
    cache_entry_path = get_cache_entry_path(post)

    os.makedirs(cache_entry_path, exist_ok=True)
    export_metadata(post, cache_entry_path)

    logger.info(f"Create cache entry {post.post_id}")
    fetch_images_of_post(post, cache_entry_path, driver, logger)


def get_cache_entry_last_update(post: PostMetaData):
    metadata_filepath = os.path.join(get_cache_entry_path(post), "meta.json")
    with open(metadata_filepath, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data.get("update_at")


def is_cache_entry_valid(post: PostMetaData) -> bool:
    cache_entry_path = get_cache_entry_path(post)
    if not os.path.exists(cache_entry_path):
        return False

    if post.update_at != get_cache_entry_last_update(post):
        return False

    return True


def clean_cache_from_old_posts(posts: List[PostMetaData], logger: logging.Logger):
    """Deletes old cache entries of posts that are no longer relevant or got removed"""
    cache_entries = [
        post_id
        for post_id in os.listdir("cache")
        if os.path.isdir(os.path.join("cache", post_id))
    ]

    new_post_ids = [post.post_id for post in posts]
    posts_to_remove = [
        cache_entry for cache_entry in cache_entries if cache_entry not in new_post_ids
    ]

    for post_to_remove in posts_to_remove:
        shutil.rmtree(os.path.join("cache", post_to_remove))
        logger.info(f"Removed cache entry {post_to_remove}")


def cache_posts(posts: List[PostMetaData], driver: Driver, logger: logging.Logger):
    """
    Caches posts based on their post_id and update_at meta information.
    """
    os.makedirs("cache", exist_ok=True)

    clean_cache_from_old_posts(posts, logger)

    for post in posts:
        if not is_cache_entry_valid(post):
            create_post_cache_entry(post, driver, logger)
        else:
            logger.info(f"Cache hit {post.post_id}")

    logger.info("Finished caching posts")
