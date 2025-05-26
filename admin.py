class Admin:
    def __init__(self, telegram_username=None, telegram_id=None):
        self.telegram_username = telegram_username
        self.telegram_id = telegram_id

    def display(self):
        return f"Admin: {self.telegram_username}"

    def __str__(self):
        return f"telegram_id={self.telegram_username})"