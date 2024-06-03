import os
import re

from tg import Type, MethodField


PROJECT_PATH = os.getenv("PROJECT_PATH")
FILE_PATH = f"{PROJECT_PATH}/generated/rust"
TYPES_FILE_NAME = "types.rs"
METHODS_FILE_NAME = "api.rs"

TYPES = {
    "Integer": "i64", "String": "String", "InputFile": "InputFile", "True": "bool", "Boolean": "bool", "Float": "f64"
}

CAMEL_CASE_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")


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

    tg_type = tg_type.replace(" , ", " ")
    tg_type = tg_type.replace(" and ", " ")

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

    if ("array of" in tg_type_copy) and (" or " in tg_type_copy):
        raise Exception("'Array of' and 'or' in one type")

    if "array of" in tg_type_copy:
        result = "#[derive(Serialize, Deserialize, Debug, Clone)]\n"
        result += "pub enum %s {\n" % or_enum_name(tg_type)
        tg_type = tg_type[len("array of "):]
        tg_type = tg_type.replace(" , ", " ")
        tg_type = tg_type.replace(" and ", " ")
        for t in tg_type.split(" "):
            result += f"\tArrayOf{t}(Vec<{t}>),\n"
        return result + "}\n\n"

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


def get_type_names(structs: set[str]) -> list[tuple[str, str]]:
    result = [("None", "")]

    for struct in structs:
        struct = struct[len("#[derive(Serialize, Deserialize, Debug, Clone)]\n"):]
        begin = 0
        end = 0

        if struct.startswith("pub enum "):
            begin = len("pub enum ")
        elif struct.startswith("pub struct "):
            begin = len("pub struct ")
        else:
            raise Exception("UNKNOWN START OF STRUCT")

        if ";" in struct:
            end = struct.find(";")
        else:
            end = struct.find(" ", begin)

        result.append((struct[begin:end], f"({struct[begin:end]})"))
        result.append((f"ArrayOf{struct[begin:end]}", f"(Vec<{struct[begin:end]}>)"))
        result.append((f"ArrayOfArrayOf{struct[begin:end]}", f"(Vec<Vec<{struct[begin:end]}>>)"))

    return result


def generate_all_types_enum(structs: set[str]) -> str:
    on_of_type_enum = "#[derive(Serialize, Deserialize, Debug, Clone)]\n"
    on_of_type_enum += "pub enum OneOfType {\n"
    for t in get_type_names(structs):
        type_name = t[0]
        type_type = t[1]
        on_of_type_enum += f"\t{type_name}{type_type},\n"
    return on_of_type_enum + "}\n\n"


def save_structs(structs: set[str]) -> None:
    """
    Saves structures to a file

    :param structs: Structures that need to be preserved
    :return: None
    """

    global FILE_PATH, TYPES_FILE_NAME

    if not os.path.exists(FILE_PATH):
        os.makedirs(FILE_PATH)

    code = "use serde::{Deserialize, Serialize};\n\n"
    for struct in structs:
        code += struct
    # print(code)

    with open(f"{FILE_PATH}/{TYPES_FILE_NAME}", "w", encoding="utf-8") as file:
        file.write(code)


def create_structs(types: dict[str, list[Type] | list[str]]) -> None:
    """
    Generates and stores telegram bot api type in rust structures

    :param types: Parsed telegram bot api data types
    :return: None
    """

    structs = set()
    for item in types.items():
        for struct in generate_structs(item):
            structs.add(struct)
    structs.add(generate_all_types_enum(structs))

    save_structs(structs)


def generate_method_docs(method_desc: str) -> str:
    result = f"\t/// {method_desc}\n"
    return result


def save_new_enum(tg_type: str) -> None:
    global FILE_PATH, TYPES_FILE_NAME

    with open(f"{FILE_PATH}/{TYPES_FILE_NAME}", "r", encoding="utf-8") as file:
        if or_enum_name(tg_type) in file.read():
            return

    new_enum = or_enum(tg_type)
    with open(f"{FILE_PATH}/{TYPES_FILE_NAME}", "a", encoding="utf-8") as file:
        file.write(new_enum)


def generate_method(item: tuple[str, tuple[str, list[MethodField]]]) -> str:
    method_name = item[0]
    method_desc = item[1][0]
    method_fields = item[1][1]

    result = generate_method_docs(method_desc)
    result += f"\tpub fn {CAMEL_CASE_PATTERN.sub('_', method_name).lower()}(&self, "
    for field in method_fields:
        if (" or " in field.tg_type.lower()) or (" , " in field.tg_type.lower()):
            save_new_enum(field.tg_type)
            field.tg_type = or_enum_name(field.tg_type)

        rust_type = ("%s" if field.required else "Option<%s>") % get_type(field.tg_type)
        if field.name == "type":
            field.name += "_"
        result += f"{field.name}: {rust_type}, "

    if result.endswith(", "):
        result = result[:-2]

    result += ") -> Result<OneOfType> {\n"
    body = "\t\tlet url: String = format!(\"{}{}{}\", \"https://api.telegram.org/bot\", self.token, \"/%s\");\n" % method_name
    body += "\t\tlet tm: Duration = Duration::from_secs(20);\n"

    body += f"\t\tlet query: [(&str, String); {len(method_fields)}] = ["
    for field in method_fields:
        body += f"(\"{field.name}\", serde_json::to_string(&{field.name})?), "
    if body.endswith(", "):
        body = body[:-2]
    body += "];\n"

    body += "\t\tlet response: Response = self.client.get(url).timeout(tm).query(&query).send()?;\n"
    body += "\t\tlet status: Status = serde_json::from_str::<Status>(response.text()?.as_str())?;\n"
    body += "\t\tif status.ok {\n"
    body += "\t\t\tOk(status.result)\n"
    body += "\t\t}\n"
    body += "\t\telse {\n"
    body += "\t\t\tbail!(\"{:#?}\", status);\n"
    body += "\t\t}\n"

    return result + body + "\t}\n\n"


def save_methods(methods: list[str]) -> None:
    global FILE_PATH, METHODS_FILE_NAME

    if not os.path.exists(FILE_PATH):
        os.makedirs(FILE_PATH)

    code = "use std::time::Duration;\n\n"
    code += "use anyhow::{bail, Result};\n"
    code += "use reqwest::blocking::*;\n"
    code += "use serde::{Deserialize, Serialize};\n"
    code += "use serde_json;\n\n"
    code += "use crate::types::*;\n\n\n"
    code += "#[derive(Serialize, Deserialize, Debug, Clone)]\n"
    code += "pub struct Status {\n"
    code += "\tok: bool,\n"
    code += "\tresult: OneOfType,\n"
    code += "}\n\n\n"
    code += "#[derive(Debug, Clone)]\n"
    code += "pub struct Api {\n"
    code += "\tpub token: String,\n"
    code += "\tpub client: Client,\n"
    code += "}\n\n\n"
    code += "impl Api {\n"

    for method in methods:
        code += method

    with open(f"{FILE_PATH}/{METHODS_FILE_NAME}", "w", encoding="utf-8") as file:
        file.write(code + "}\n")


def create_methods(methods: dict[str, tuple[str, list[MethodField]]]) -> None:
    result = [generate_method(item) for item in methods.items()]
    save_methods(result)
