import json


class Settings:
    def __init__(self, filepath):
        self.load(filepath)

    def load(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.team_name = data.get("team_name")
        self.channel_name = data.get("channel_name")
        self.instance_url = data.get("instance_url")

        backend = data.get("backend", {})
        self.backend_posts_fetching_interval = backend.get("posts_fetching_interval")
        self.backend_max_post_count = backend.get("max_post_count")

        frontend = data.get("frontend", {})
        self.frontend_images_fetching_interval = (
            frontend.get("images_fetching_interval") * 1000
        )
        self.frontend_polaroid_batch_presentation_duration = (
            frontend.get("polaroid_batch_presentation_duration") * 1000
        )
