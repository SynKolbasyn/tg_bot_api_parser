import os

import requests
from bs4 import BeautifulSoup


TG_BOT_API_URL = "https://core.telegram.org/bots/api"
PROJECT_PATH = os.getenv("PROJECT_PATH")


def save_html() -> None:
    """
    Saves the html page of the telegram bot api

    :return: None
    """

    global TG_BOT_API_URL, PROJECT_PATH

    answer = requests.get(TG_BOT_API_URL)
    content = answer.content
    soup = BeautifulSoup(content, "html.parser")
    path = f"{PROJECT_PATH}/html"
    name = "tg_bot_api.html"

    if not os.path.exists(path):
        os.makedirs(path)

    with open(f"{path}/{name}", "w", encoding="utf-8") as file:
        html = soup.prettify()
        file.write(html)


def main() -> int:
    return 0


if __name__ == "__main__":
    exit(main())
