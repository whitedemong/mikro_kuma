import ssl
import logging
import aiohttp
import asyncio
import platform
from typing import Optional
from datetime import datetime

from checkers.config import SiteConfig
from notifications.interface import NotificationHandler


class SiteChecker:
    @staticmethod
    async def check_http(site: SiteConfig, notifier: NotificationHandler) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                method = site.http_method.lower()  # noqa
                timeout = aiohttp.ClientTimeout(total=site.timeout)
                
                async with session.request(
                    method=method,
                    url=site.target,
                    allow_redirects=True,
                    max_redirects=5,
                    timeout=timeout,
                    ssl=False
                ) as response:
                    if not (200 <= response.status < 400):
                        return False
                    body = await response.text()
                    
                    history = response.history
                    for resp in history:
                        logging.debug(f"Redirect: {resp.status} {resp.url}")

                    final_url = str(response.url)
                    if final_url != site.target:
                        logging.info(f"Redirect detected: {site.target} -> {final_url}")
                    if final_url.startswith('https://'):
                        ssl_warning = await SiteChecker._handle_ssl_warnings(site, final_url)
                        if ssl_warning:
                            await notifier.send(ssl_warning)

                    if site.check_body:
                        body = await response.text()
                        return len(body.strip()) > 0

                    return True
                    
        except aiohttp.ClientError as e:
            logging.error(f"HTTP connection error for {site.name}: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"HTTP check failed for {site.name}: {str(e)}")
            return False

    @staticmethod
    async def check_ping(site: SiteConfig) -> bool:
        target = site.target
        timeout = site.timeout

        if platform.system().lower() == 'windows':
            command = ['ping', '-n', '1', '-w', str(int(timeout * 1000)), target]
        else:
            command = ['ping', '-c', '1', '-W', str(timeout), target]

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout + 1
            )
            
            return process.returncode == 0
        except asyncio.TimeoutError:
            return False
        except Exception as e:
            logging.error(f"PING check failed for {site.name}: {str(e)}")
            return False

    @staticmethod
    async def check_ssl(site: SiteConfig) -> Optional[int]:
        if not site.target.startswith('https://'):
            return None

        hostname = site.target.split('//')[1].split('/')[0].split(':')[0]
        context = ssl.create_default_context()  # noqa
        writer = None
        
        try:
            port: int = 443
            try:
                port = int(site.target.replace('/', '').split(':')[-1])
            except Exception as err:  # noqa
                pass
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(hostname, port, ssl=context),
                timeout=5.0
            )
            
            ssl_object = writer.get_extra_info('ssl_object')
            if not ssl_object:
                logging.error(f"No SSL context for {site.target}")
                return None

            cert = ssl_object.getpeercert()
            if not cert:
                logging.error(f"No certificate found for {site.target}")
                return None

            expire_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
            days_left = (expire_date - datetime.now()).days
            return days_left
            
        except Exception as e:
            logging.error(f"SSL check failed for {site.name}: {str(e)}")
            return None
        finally:
            if writer:
                writer.close()
                await writer.wait_closed()

    @staticmethod
    async def _handle_ssl_warnings(site: SiteConfig, url: str) -> Optional[str]:
        """
        """
        try:
            if not url.startswith('https://'):
                return None

            host_port = url.split('//')[1].split('/')[0]
            hostname = host_port.split(':')[0]
            port = 443
            if ':' in host_port:
                port = int(host_port.split(':')[1])

            context = ssl.create_default_context()
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(hostname, port, ssl=context),
                timeout=5.0
            )

            ssl_obj = writer.get_extra_info('ssl_object')
            if not ssl_obj:
                return None

            cert = ssl_obj.getpeercert()
            writer.close()
            await writer.wait_closed()

            expire_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
            days_left = (expire_date - datetime.now()).days

            thresholds = [5, 10, 15, 20, 25, 30]
            active = [t for t in thresholds if days_left < t]
            
            if not active:
                return None

            threshold = min(active)
            if threshold not in site.cert_warnings:
                site.cert_warnings.update({t for t in thresholds if t >= threshold})
                return (
                    f"⚠️ SSL Certificate Warning: {site.name}\n"
                    f"URL: {url}\n"
                    f"Days left: {days_left}\n"
                    f"Expiry date: {expire_date.strftime('%Y-%m-%d')}"
                )

        except Exception as e:
            logging.error(f"SSL warning check failed for {url}: {str(e)}")
        
        return None