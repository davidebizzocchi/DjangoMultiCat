from typing import Dict, List


def string_reshape(v: str, separator=",", shape=2) -> List[List]:
    splitted = v.split(separator)

    result = []
    last_elems = []
    for i in range(len(splitted)):
        elem = splitted[i].strip()

        last_elems.append(elem)

        if (i+1) % shape == 0:
            result.append(last_elems)
            last_elems = []

    if len(last_elems) > 0:
        result.append(last_elems)

    return result

def string_to_dict(v: str, separator=",", value_len=1) -> Dict[str, List | str]:
    splitted = v.split(separator)

    result = {}
    value_list = []
    key = None

    for i in range(len(splitted)):
        elem = splitted[i].strip()

        if key is None:
            key = elem
            continue

        value_list.append(elem)

        if (len(value_list)) % value_len == 0:
            result[key] = value_list[0] if value_len == 1 else value_list
            value_list = []
            key = None

    if len(value_list) > 0:
        result[key] = value_list[0] if value_len == 1 else value_list

    return result