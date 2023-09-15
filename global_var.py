import json

with open("config.json", "r", encoding="utf-8") as global_json_file:
    global_data = json.load(global_json_file)
    global CharacterName
    global PtuningModel
    global QQid
    global QQ_at_token
    CharacterName = global_data["CharacterName"]
    PtuningModel = global_data["PtuningModel"]
    QQid = global_data["QQid"]
    QQ_at_token = "[CQ:at,qq=" + QQid + "]"