import asyncio
import csv
import logging
from datetime import datetime, timedelta
from typing import List

from checkers.config import SiteConfig
from checkers.sites import SiteChecker
from notifications.interface import NotificationHandler
from notifications.telegram import TelegramNotifier


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)


class SiteMonitor:
    def __init__(self, site: SiteConfig, notifier: NotificationHandler):
        self.site = site
        self.notifier = notifier

    async def check_status(self) -> bool:
        status: bool = False

        if self.site.method == 'HTTP':
            status = await SiteChecker.check_http(self.site, self.notifier)
        elif self.site.method == 'PING':
            status = await SiteChecker.check_ping(self.site)
        else:
            logging.error(f"Unknown check method: {self.site.method}")
            status = False

        return status

    async def check_and_notify(self):
        current_status = await self.check_status()
        await self._handle_ssl_warnings()
        await self._handle_status_change(current_status)
        self.site.last_status = current_status

    async def _handle_ssl_warnings(self):
        if self.site.method == 'HTTP' and self.site.target.startswith('https://'):
            days_left = await SiteChecker.check_ssl(self.site)
            if days_left is None:
                return

            thresholds = [5, 10, 15, 20, 25, 30]
            active = [t for t in thresholds if days_left < t]
            
            if not active:
                return

            threshold = min(active)
            if threshold not in self.site.cert_warnings:
                message = (
                    f"⚠️ SSL Certificate Warning: {self.site.name}\n"
                    f"Days left: {days_left}\n"
                    f"Expiry date: {datetime.now() + timedelta(days=days_left):%Y-%m-%d}\n"
                    f"URL: {self.site.target}"
                )
                await self.notifier.send(message)
                self.site.cert_warnings.add(threshold)

    async def _handle_status_change(self, current_status: bool):
        if self.site.last_status is None:  
            if current_status:
                await self._send_startup_notification()
            return

        if self.site.last_status != current_status:
            await self._send_status_change_notification(current_status)

    async def _send_startup_notification(self):
        message = f"✅ Service {self.site.name} initialized\nURL: {self.site.target}"
        await self.notifier.send(message)

    async def _send_status_change_notification(self, new_status: bool):
        status = "🟢 available" if new_status else "🛑 unavailable"
        message = (
            f"🔄 Status changed: {self.site.name}\n"
            f"New status: {status}\n"
            f"Type: {self.site.method}\n"
            f"Target: {self.site.target}"
        )
        await self.notifier.send(message)

class MonitoringService:
    def __init__(self, config_file: str, notifier: NotificationHandler):
        self.config_file = config_file
        self.notifier = notifier
        self.monitors: List[SiteMonitor] = []

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                reader = csv.reader(f, skipinitialspace=True)
                for row in reader:
                    if len(row) < 7:
                        continue
                    if row[0][:2] == "# ":
                        logging.warning(f"This line comments: {', '.join(row)}")
                        continue
                    
                    site = SiteConfig(
                        name=row[0].strip(),
                        method=row[1].strip().upper(),
                        target=row[2].strip(),
                        http_method=row[3].strip().upper() if row[1].strip().upper() == 'HTTP' else None,
                        timeout=float(row[4].strip()),
                        allow_redirects=row[5].strip().lower() == 'true',
                        max_redirects=int(row[6].strip()),
                        check_body=row[7].strip().lower() == 'true')
                    
                    self.monitors.append(SiteMonitor(site, self.notifier))
        except Exception as e:
            logging.error(f"Config load error: {str(e)}")

    async def run(self, interval: int = 60):
        while True:
            for monitor in self.monitors:
                await monitor.check_and_notify()
            await asyncio.sleep(interval)


async def main():
    notifier = TelegramNotifier()
    service = MonitoringService("sites.conf", notifier)
    service.load_config()
    
    try:
        await service.run(interval=60)
    except KeyboardInterrupt:
        await notifier.close()
        logging.info("Monitoring stopped")

if __name__ == "__main__":
    asyncio.run(main())
