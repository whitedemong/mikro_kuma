from notifications.interface import NotificationHandler


class EmailNotifier(NotificationHandler):
    def __init__(self, smtp_server: str, login: str, password: str):
        self.smtp_server = smtp_server
        self.login = login
        self.password = password

    async def send(self, message: str) -> None:
        pass

