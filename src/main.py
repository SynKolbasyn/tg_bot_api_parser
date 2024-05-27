import os

import requests
from bs4 import BeautifulSoup, Tag

from tg_type import Type


TG_BOT_API_URL = "https://core.telegram.org/bots/api"
PROJECT_PATH = os.getenv("PROJECT_PATH")
html_path = f"{PROJECT_PATH}/html"
html_name = "tg_bot_api.html"


def trim(tag: Tag) -> str:
    """
    Leaves only the text from the tag

    :param tag: The tag from which the entire text is selected
    :return: Clean text
    """

    result = ""

    for i in tag.stripped_strings:
        result += i

    return result


def get_html() -> BeautifulSoup:
    """
    Gets the html code of the telegram bot api page and creates a BeautifulSoup object from it

    :return: The BeautifulSoup object of the entire telegram bot api page
    """

    global TG_BOT_API_URL, html_path, html_name

    response = requests.get(TG_BOT_API_URL)

    if response.status_code != 200:
        raise Exception("Request code not 200")

    return BeautifulSoup(response.text, "html.parser")


def save_html() -> None:
    """
    Saves the html page of the telegram bot api

    :return: None
    """

    soup = get_html()

    if not os.path.exists(html_path):
        os.makedirs(html_path)

    with open(f"{html_path}/{html_name}", "w", encoding="utf-8") as file:
        html = soup.prettify()
        file.write(html)


def load_html(path: str = "") -> BeautifulSoup:
    """
    Loads the downloaded telegram bot api page and creates a BeautifulSoup object from it

    :param path: The path to the file containing the html code of the telegram bot api page
    :return: The BeautifulSoup object of the telegram bot api html page
    """

    global html_path, html_name

    if path == "":
        path = f"{html_path}/{html_name}"

    with open(path, "r", encoding="utf-8") as file:
        html = file.read()
        soup = BeautifulSoup(html, features="html.parser")

    return soup


def filtrate_data(data: BeautifulSoup) -> list[Tag]:
    """
    The function removes all unnecessary tags

    :param data: The tag that contains the basic information of the telegram bot api: <div id="dev_page_content">
    :return: A list containing only the "h4", "p" and "table" tags
    """

    result = []
    for i in data.find_all():
        if i.name not in ("h4", "p", "table", "ul"):
            continue
        result.append(i)
    return result


def check_type(type_name: Tag, type_desc: Tag) -> bool:
    """
    Checks whether the tag is a data type, since not all "h4" tags are such

    :param type_name: The "h4" tag
    :param type_desc: The "p" tag
    :return: True if the tag is a data type, otherwise false
    """

    if type_name.name != "h4" or type_desc.name != "p":
        return False

    if not trim(type_desc).startswith("This object"):
        return False

    return True


def create_from_table(type_table: Tag) -> list[Type]:
    """
    Creates a list of Types from the "table" tag

    :param type_table: A tag containing a table of composite types
    :return: A list of Types
    """

    result = []
    table = type_table.select_one("tbody")

    for types in table.find_all("tr"):
        name, data_type, desc = types.find_all("td")
        name, data_type, desc = trim(name), trim(data_type), trim(desc)

        t = Type(name, data_type, desc.startswith("Optional"))
        result.append(t)

    return result


def create_from_list(type_list: Tag) -> list[str]:
    """
    Creates a list of strs from a "ul" tag

    :param type_list: A tag containing a list of composite types
    :return: A list of strs
    """

    result = []

    for i in type_list.find_all("li"):
        result.append(trim(i))

    return result


def parse_types(from_file: str = "") -> dict[str, list[Type]]:
    """
    Parses all types of telegram bot api data

    :param from_file: The path to the file containing the html code of the telegram bot api page
    :return: A dictionary whose keys are the name of the data type, the value is a list of Types or strings, depending
             on the telegram data type
    """

    result = {}
    soup = load_html(from_file) if from_file != "" else get_html()
    data = soup.select_one("div[id=dev_page_content]")
    filtered_data = filtrate_data(data)

    for i, e in enumerate(filtered_data[2:], start=2):
        type_name = filtered_data[i - 2]
        type_desc = filtered_data[i - 1]
        type_table = e

        if not check_type(type_name, type_desc):
            continue

        match type_table.name:
            case "table":
                result[trim(type_name)] = create_from_table(type_table)
            case "ul":
                result[trim(type_name)] = create_from_list(type_table)

    return result


def main() -> int:
    result = parse_types(f"{html_path}/{html_name}")
    print(*result.items(), sep="\n")
    return 0


if __name__ == "__main__":
    exit(main())
