import json
import os
import global_var

#用于确定字符串是否是json对象
def is_valid_json(json_str):
    try:
        json.loads(json_str)
        return True
    except ValueError:
        print("无效的json文件",json_str)
        return False

# 用于将消息存入记忆
def append_to_memory_file(file_name, final_result):

    # 读取现有的 JSON 数据（每行一个对象）
    existing_data = []
    with open(file_name, "r", encoding="utf-8") as json_file:
        for line in json_file:
            if line.strip():
                existing_data.append(json.loads(line))

    if(isinstance(final_result,dict)):
        existing_data.append(final_result)

    else:
        for new_object in final_result:
            existing_data.append(new_object)


        # 将更新后的数据写回到文件
    with open(file_name, "w", encoding="utf-8") as json_file:
        for obj in existing_data:
            json_file.write(json.dumps(obj, ensure_ascii=False) + '\n')


#将两段对话合并并保存max_line条消息
def process_strings(str1, str2, max_lines):
    combined_string = str1 + '\n' + str2
    lines = combined_string.split('\n')

    if len(lines) > max_lines:
        truncated_lines = lines[-max_lines:]
        processed_string = '\n'.join(truncated_lines)
    else:
        processed_string = combined_string

    return processed_string.rstrip()

#将记录储存至文本文件中
def append_to_txt_file(file_name, content1, content2, content3):
    new_object = {
        "prompt": content1,
        "summary": content2,
        "history": content3
    }

    # 读取现有的 JSON 数据（每行一个对象）
    existing_data = []
    with open(file_name, "r", encoding="utf-8") as json_file:
        for line in json_file:
            if line.strip():  # 忽略空行
                existing_data.append(json.loads(line))

    # 将新对象添加到现有数据中
    existing_data.append(new_object)

    # 将更新后的数据写回到文件
    with open(file_name, "w", encoding="utf-8") as json_file:
        for obj in existing_data:
            json_file.write(json.dumps(obj, ensure_ascii=False) + '\n')

#去除机器人开头可能的自带称谓
def remove_prefix(input_string):
    prefixes = [global_var.CharacterName + "："]

    for prefix in prefixes:
        if input_string.startswith(prefix):
            return input_string[len(prefix):]

    return input_string

def check_invalue(input_string,substring_list):
    for substring in substring_list:
        if substring in input_string:
            return True
    return False


def contains_any(target_string):
    substrings = ["...","……","啊——","好的"]
    for substring in substrings:
        if substring in target_string:
            return True
    return False

def replace_cq_image(text):
    start_marker = "[CQ:image,"
    end_marker = "]"
    result = []
    i = 0

    while i < len(text):
        start_index = text.find(start_marker, i)
        if start_index == -1:
            result.append(text[i:])
            break

        result.append(text[i:start_index])
        end_index = text.find(end_marker, start_index)
        if end_index == -1:
            result.append(text[start_index:])
            break

        result.append("发送了一个表情")
        i = end_index + 1

    return ''.join(result)

def replace_substring(input_string, old_substring, new_substring):
    new_string = input_string.replace(old_substring, new_substring)
    return new_string

def lines_to_list(text):
    lines = text.split('\n')  # 将字符串按行分割成列表
    cleaned_lines = [line.strip() for line in lines]  # 去除每行两侧的空白字符
    return cleaned_lines

#用来判断是否是对八六说的话
def break_judge(message):
    if any(item in message for item in [global_var.CharacterName, global_var.QQ_at_token]):
        return True
    else:
        return False
