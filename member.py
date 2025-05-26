class Member:
    def __init__(self, telegram_username: str, telegram_id: int = None):
        self.telegram_username = telegram_username
        self.telegram_id = telegram_id
        self.charge_count = 0

    def increace_charge(self):
        self.charge_count += 1

    def __str__(self):
        return f"Member(telegram_id={self.telegram_username}, charge_count={self.charge_count})"

    def __repr__(self):
        return f"Member(telegram_id={self.telegram_username}, charge_count={self.charge_count})"