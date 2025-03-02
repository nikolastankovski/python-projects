import json

def isNullOrEmpty(s:str) -> bool:
    return not s or not s.strip()

def toJson(obj):
    return json.dumps(
            obj,
            default=lambda o: o.__dict__, 
            sort_keys=True,
            indent=4)