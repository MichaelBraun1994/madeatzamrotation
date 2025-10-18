class ImagePost:
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
