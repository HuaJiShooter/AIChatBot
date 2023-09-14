import json
import socket


def getmessage(message_queue):
    print("获取消息创建进程成功")

    #无需设置
    host = '127.0.0.1'
    getmessage_port = 8081

    #构造好socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, getmessage_port))
    server_socket.listen(1)
    print(f"Listening on {host}:{getmessage_port}")



    json_data = None

    while True:
        client_socket, client_address = server_socket.accept()
        data=b""

        while True:
            chunk = client_socket.recv(1024)
            if not chunk:
                break
            data += chunk


        request_lines = data.decode('utf-8').split('\r\n')

        for line_index, line in enumerate(request_lines):
            if line.startswith("{"):
                json_data = json.loads(request_lines[line_index])
                break

        if json_data:

            response = ""
            message_type_match = json_data.get("message_type",None)
            notice_type_match = json_data.get("notice_type", None)

            #TODO 当收到消息时
            if message_type_match is not None:
                #获取发送人消息
                message_match = json_data.get("message",None)
                sender_match = json_data.get("sender",None)
                nickname = sender_match.get("nickname",None)
                user_id = sender_match.get("user_id",None)
                if message_type_match == "group":
                    #获取群组消息后
                    group_id = json_data.get("group_id",None)
                    card = sender_match.get("card",None)
                    if card != '':
                        message_queue.put({"group_id":group_id,"nickname":card,"user_id":user_id,"message":message_match})

                    else:
                        message_queue.put({"group_id":group_id,"nickname":nickname,"user_id":user_id,"message":message_match})
                    print("已将消息放入队列中")


                if message_type_match == "private":
                    #获取私聊消息后
                    message_queue.put({"group_id":None,"nickname":nickname,"user_id":user_id,"message":message_match})



            #TODO 当收到通知时
            elif notice_type_match is not None:
                if notice_type_match == "group_recall":
                    group_id = sender_match.get("group_id",None)
                    user_id = sender_match.get("user_id", None)
                    message_queue.put({"group_id":group_id,"nickname":None,"user_id":user_id,"message":"撤回了一条消息"})

                elif notice_type_match == "friend_recall":
                    user_id = sender_match.get("user_id", None)
                    message_queue.put({"group_id": None, "nickname": None, "user_id": user_id, "message": "撤回了一条消息"})

                else:
                    print("获取了未知通知")

            json_data = None