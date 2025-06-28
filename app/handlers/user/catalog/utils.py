from typing import Tuple, Union


async def get_category(arg: Union[str, int]) -> Tuple[str, int]:
    mapping_str = {
        "tires": ("Б/У Резина", 1),
        "discs": ("Б/У Диски", 2)
    }
    mapping_int = {
        1: ("Б/У Резина", 1),
        2: ("Б/У Диски", 2)
    }
    if isinstance(arg, str):
        return mapping_str.get(arg, ("Неизвестная категория", 0))
    elif isinstance(arg, int):
        return mapping_int.get(arg, ("Неизвестная категория", 0))
    else:
        return ("Неизвестная категория", 0)