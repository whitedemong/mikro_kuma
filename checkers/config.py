from typing import Optional, Set


class SiteConfig:
    def __init__(self, 
                 name: str, 
                 method: str, 
                 target: str,
                 http_method: Optional[str] = None, 
                 timeout: float = 10.0,
                 allow_redirects: bool = True,
                 max_redirects: int = 5,
                 check_body: bool = True,
                 verify_ssl: bool = True):
        self.name = name
        self.method = method.upper()
        self.target = target
        self.http_method = http_method.upper() if http_method else None
        self.timeout = timeout
        self.allow_redirects = allow_redirects
        self.max_redirects = max_redirects
        self.check_body = check_body
        self.cert_warnings: Set[int] = set()
        self.last_status: Optional[bool] = None
        self.verify_ssl = verify_ssl
