import os

from tg_type import Type


PROJECT_PATH = os.getenv("PROJECT_PATH")
FILE_PATH = f"{PROJECT_PATH}/generated/rust"
FILE_NAME = "types.rs"

TYPES = {
    "Integer": "i64", "String": "String", "InputFile": "InputFile", "True": "bool", "Boolean": "bool", "Float": "f64"
}


def get_type(tg_type: str) -> str:
    """
    Converts the telegram botapi data type to the Rust data type

    :param tg_type: Telegram bot api data type
    :return: The Rust data type
    """

    global TYPES

    tg_type_copy = tg_type.lower()

    if tg_type_copy.startswith("array of "):
        return f"Vec<{get_type(tg_type[len("array of "):])}>"

    if tg_type in TYPES.keys():
        return TYPES[tg_type]

    return tg_type


def or_enum_name(tg_type: str) -> str:
    """
    Creates an enumeration name

    :param tg_type: Telegram bot api data type
    :return: The name of the enumeration
    """

    tg_type_list = [*tg_type]
    name = ""
    for i, e in enumerate(tg_type_list):
        if e == " ":
            tg_type_list[i + 1] = tg_type_list[i + 1].upper()
            e = ""
        name += e
    return name


def or_enum(tg_type: str) -> str:
    """
    Generates an enumeration from data types

    :param tg_type: Telegram bot api data type
    :return: Generated enumeration
    """

    tg_type_copy = tg_type.lower().strip()

    if ("arrayof" in tg_type_copy) and ("or" in tg_type_copy):
        raise Exception("'Array of' and 'or' in one type")

    result = "#[derive(Serialize, Deserialize, Debug, Clone)]\n"
    result += "pub enum %s {\n" % or_enum_name(tg_type)

    for t in tg_type.split(" or "):
        result += f"\t{t}({get_type(t)}),\n"

    return result + "}\n\n"


def generate_structs(item: tuple[str, list[Type]] | tuple[str, list[str]]) -> list[str]:
    """
    Generates a structure for the telegram bot api data type

    :param item: Telegram bot api data type
    :return: A list with structures
    """

    name = item[0]
    fields = item[1]

    if len(fields) == 0:
        res = "#[derive(Serialize, Deserialize, Debug, Clone)]\n"
        res += f"pub struct {name};\n\n"
        return [res]

    if type(fields[0]) is str:
        res = "#[derive(Serialize, Deserialize, Debug, Clone)]\n"
        res += "pub enum %s {\n" % name
        for field in fields:
            res += f"\t{field}({field}),\n"
        return [res + "}\n\n"]

    result = []
    res = "#[derive(Serialize, Deserialize, Debug, Clone)]\n"
    res += "pub struct %s {\n" % name

    for field in fields:
        if " or " in field.tg_type.lower():
            result.append(or_enum(field.tg_type))
            field.tg_type = or_enum_name(field.tg_type)
        rust_type = ("Option<%s>" if field.optional else "%s") % get_type(field.tg_type)
        rust_name = "#[serde(rename = \"type\")]\n\ttype_" if field.name == "type" else field.name
        res += f"\t{rust_name}: {rust_type},\n"
    result.append(res + "}\n\n")

    return result


def save_structs(structs: set[str]) -> None:
    """
    Saves structures to a file

    :param structs: Structures that need to be preserved
    :return: None
    """

    global FILE_PATH, FILE_NAME

    if not os.path.exists(FILE_PATH):
        os.makedirs(FILE_PATH)

    code = "use serde::{Deserialize, Serialize};\n\n"
    for struct in structs:
        code += struct
    # print(code)

    with open(f"{FILE_PATH}/{FILE_NAME}", "w", encoding="utf-8") as file:
        file.write(code)


def create_structs(types: dict[str, list[Type]] | dict[str, list[str]]) -> None:
    """
    Generates and stores telegram bot api type in rust structures

    :param types: Parsed telegram bot api data types
    :return: None
    """

    structs = set()
    for item in types.items():
        for struct in generate_structs(item):
            structs.add(struct)
    save_structs(structs)

