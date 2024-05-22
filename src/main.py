import os

import requests
from bs4 import BeautifulSoup

import type


TG_BOT_API_URL = "https://core.telegram.org/bots/api"
PROJECT_PATH = os.getenv("PROJECT_PATH")
html_path = f"{PROJECT_PATH}/html"
html_name = "tg_bot_api.html"


def save_html() -> None:
    """
    Saves the html page of the telegram bot api

    :return: None
    """

    global TG_BOT_API_URL, html_path, html_name

    response = requests.get(TG_BOT_API_URL)

    if response.status_code != 200:
        raise Exception("Request code not 200")

    content = response.content
    soup = BeautifulSoup(content, "html.parser")

    if not os.path.exists(html_path):
        os.makedirs(html_path)

    with open(f"{html_path}/{html_name}", "w", encoding="utf-8") as file:
        html = soup.prettify()
        file.write(html)


def load_html() -> BeautifulSoup:
    """
    Loads the downloaded telegram bot api page and creates a BeautifulSoup object from it

    :return: The BeautifulSoup object of the telegram bot api html page
    """

    global html_path, html_name

    with open(f"{html_path}/{html_name}", "r", encoding="utf-8") as file:
        html = file.read()
        soup = BeautifulSoup(html)

    return soup


def parse_types() -> dict[str, list[type.Type]]:
    """

    :return:
    """

    soup = load_html()

    return {}


def main() -> int:
    return 0


if __name__ == "__main__":
    exit(main())
