import json


def pretty_json(data) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)
