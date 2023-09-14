import requests

#发送信息的函数
def sendmessage(ChatResult,groupid):
    # 设置请求头
    headers = {
        'Content-Type': 'application/json'
    }

    # 构造发送的消息
    data = {
        "message_type": "group",
        "group_id": groupid,  # 替换成你要发送消息的 QQ 账号
        "message": ChatResult  # 替换成要发送的文本内容
    }

    # 发送 HTTP 请求
    response = requests.post('http://localhost:5700/send_msg', headers=headers, json=data)

    # 解析返回的数据
    if response.json().get("status") == "ok":
        print("消息发送成功")
    else:
        print("消息发送失败")