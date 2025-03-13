import aiohttp
import os
import logging

from notifications.interface import NotificationHandler


class TelegramNotifier(NotificationHandler):
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.session = aiohttp.ClientSession()
        
    async def send(self, message: str) -> None:
        if not self.token or not self.chat_id:
            logging.error("Telegram credentials not configured!")
            return

        url = f'https://api.telegram.org/bot{self.token}/sendMessage'
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }

        try:
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    error = await response.text()
                    logging.error(f"Telegram API error: {error}")
        except Exception as e:
            logging.error(f"Failed to send Telegram message: {str(e)}")
    
    async def close(self):
        await self.session.close()
