
Programm mikro_kuma
===============

*mikro_kuma: Programm mikro_kuma*

Documentation |  https://github.com/whitedemong/mikro_kuma
------------- | -------------------------------------------------
Code | https://github.com/whitedemong/mikro_kuma
Python version | Python >=3.12 <3.13
Python version during development | Python 3.12.9
------------- | -------------------------------------------------

# Description
I used the Kuma project on my server to monitor the status of my sites. Everything was configured correctly, all passwords and protections were made. Docker is constantly updated.

But there was a problem.
At some point, the hoster provider began to block the server. Strike:

2025-03-05 21:26. categories: ddos ​​attack
participating, web spam.
comment: incoming layer 7 flood detected
2025-02-11 21:24. categories: ddos ​​attack
participating, web spam.
comment: incoming layer 7 flood detected
2025-02-07 10:30. categories: bad web bot.
comment: ......

And I realized that through some vulnerability they infect this system and use it as a Bot. I really like Kuma. But I need to monitor the availability of my Sites in Real Time and to prevent the Server from being blocked for this reason.

That's why I wrote my own micro Service that does the same thing.

Yes - it's simple.

Yes - there's a Config file here.

Yes - there's no WebInterface here.

But this is a quick code made on the fly and it works!!

Package manager
----------------------
uv - https://github.com/astral-sh/uv

Packages
----------------------
aiohttp
checkers - all sorts of checks here
notifications - here Interface and Classes for sending data to recipients

Environment variables
----------------------
TELEGRAM_BOT_TOKEN="<\<TOKEN>>"

TELEGRAM_CHAT_ID="<\<ID>>"

Installation
----------------------
Local:
- git clone --recursive --branch master git@github.com:whitedemong/mikro_kuma.git
- cd mikro_kuma
- uv sync
- source .env

Run
----------
Local:
- uv run main.py

# How it works

1. You need to write your variables to .env or Docker variables
2. Write your sites to the sites.conf file.
