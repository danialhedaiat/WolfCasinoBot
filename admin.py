class Admin:
    def __init__(self, telegram_id=None):
        self.telegram_id = telegram_id

    def display(self):
        return f"Admin: {self.telegram_id}"

    def __str__(self):
        return f"telegram_id={self.telegram_id})"