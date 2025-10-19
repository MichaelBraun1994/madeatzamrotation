from typing import List
from image_posts import ImagePost
from logging import Logger
from mattermostdriver import Driver
from dotenv import load_dotenv
import os


class BotSecrets:
    def __init__(self, username, token):
        self.username = username
        self.token = token


class Bot:
    """
    Bot interacting with mattermost channel.
    """

    def __init__(self, logger: Logger):
        self.logger = logger
        self.load_secrets_from_env()

    def connect(self):
        self.driver = Driver(
            {
                "url": "chat.zam.haus",
                "token": self.secrets.token,
                "port": 443,
                "scheme": "https",
                "verify": True,
                "basepath": "/api/v4",
                "timeout": 30,
            }
        )

        self.driver.login()
        self.logger.info("Logged in")

    def load_secrets_from_env(self) -> BotSecrets:
        load_dotenv()

        username_env_variable = "MATTERMOST_BOT_USERNAME"
        token_env_variable = "MATTERMOST_BOT_TOKEN"

        username = os.getenv(username_env_variable)
        if username is None:
            raise RuntimeError(f"{username_env_variable} is not set.")

        token = os.getenv(token_env_variable)
        if token is None:
            raise RuntimeError(f"{token_env_variable} is not set.")

        self.secrets = BotSecrets(username, token)

    def is_file_image(self, file_id) -> bool:
        file_info = self.driver.files.get_file_metadata(file_id)
        file_type = file_info.get("mime_type")
        return file_type.startswith("image/")

    def fetch_posts_with_images(self) -> List[ImagePost]:
        team_name = "ZAM"
        channel_name = "made-at-zam"
        posts_fetch_limit = 100
        team = self.driver.teams.get_team_by_name(team_name)
        channel = self.driver.channels.get_channel_by_name(team["id"], channel_name)

        posts = self.driver.posts.get_posts_for_channel(
            channel["id"], params={"page": 0, "per_page": posts_fetch_limit}
        )
        self.logger.info("Fetched posts metadata")

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
                filter(lambda file_id: self.is_file_image(file_id), post["file_ids"])
            )

            user = self.driver.users.get_user(post_user_id)
            post_username = user["username"]

            if len(post_image_ids) != 0:
                image_posts.append(
                    ImagePost(
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

    def fetch_images_of_post(self, image_post: ImagePost, output_path):
        for file_id in image_post.file_ids:
            file_info = self.driver.files.get_file_metadata(file_id)
            file_extension = file_info.get("extension")
            file_name = file_id + "." + file_extension

            with open(os.path.join(output_path, file_name), "wb") as f:
                file_bytes = self.driver.files.get_file(file_id).content
                f.write(file_bytes)
                self.logger.info(f"\tFetched {file_name}")
