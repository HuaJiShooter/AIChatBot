import multiprocessing
import queue
import time
import random
import TextHandel
import SendMessage
import embedding
import database
import datetime
import json

history_forward = {"prompt":r'你将扮演一个游戏中的角色“八六”，并且以你的身份参与到一个群聊中去，在你回复前，你接受到的消息中"XX的相关记忆："后的消息是供你参考的回忆，从下一次对话开始，每一次对话都站在你的角度，结合供你参考的回忆，并且对"刚刚接受到的消息："后的内容进行回复，注意，你只需要站在你自己“八六”的角度回复',"summary":"好的,我会以八六的角色参与群聊,并根据你提供的记忆进行回复。让我们开始吧!"}

def Group_Thread(group_id,shared_queue,Result_queue,lock,lock_file):
    #shared_queue中只有一个group的消息
    history = []
    print(group_id + "线程启动成功")
    ChatMode = False
    CanTalk = True
    while True:

        interval = random.randint(300, 360)  # 默认等待参数
        timeoutsecond = random.randint(150, 180)  # 超时时间
        end_time = time.time() + interval
        start_time = time.time()
        result_dict = []
        chatdata = None





        if Result_queue.empty():
            while time.time() < end_time:

                with lock:
                    if not Result_queue.empty():
                        history = Result_queue.get()


                if not shared_queue.empty():
                    chatdata = shared_queue.get()
                    print("线程:" + group_id + " 接受到消息")
                    print(chatdata)

                # 计算过去的时间
                passing_time = time.time() - start_time

                # 如果聊天信息等待超过预定时间，则重置等待时间和结束时间
                if passing_time > timeoutsecond:
                    start_time = time.time()
                    end_time = time.time() + interval

                # 消息非空则增加数据
                if chatdata is not None:

                    end_time -= 30

                    personal_result = chatdata["nickname"] + '：' + chatdata["message"]  # 聊天结果(单人)

                    #TODO 这里将消息存入记忆
                    try:
                        print("进入数据库操作阶段")

                        # 存入群友说的话
                        SendTime = datetime.datetime.now()
                        MessageContent = chatdata["message"]
                        Nickname = chatdata["nickname"]
                        MessageVector = embedding.GetEmbedding(chatdata["message"]).tolist()
                        my_list_json = json.dumps(MessageVector)

                        VectorData = my_list_json
                        Data = {
                            "MessageContent": MessageContent,
                            "Nickname": Nickname,
                            "group_id": group_id,
                            "SendTime": SendTime,
                        }
                        print("正在存入消息", SendTime, Nickname, MessageContent, my_list_json)
                        database.insert_Chatdata(VectorData, Data)
                        print("存入完毕")


                    except Exception as e1:
                        print("存入记忆出错",e1)

                    result_dict.append(personal_result)


                    # 如果说话的话带有八六，那么直接回复
                    if TextHandel.break_judge(chatdata["message"]):
                        if "开启聊天模式" in chatdata["message"]:
                            ChatMode = True
                        elif "关闭聊天模式" in chatdata["message"]:
                            ChatMode = False
                        elif "闭嘴" in chatdata["message"]:
                            CanTalk = False
                            SendMessage.sendmessage("好我闭嘴",group_id)
                        elif "可以说话了" in chatdata["message"]:
                            CanTalk = True
                            SendMessage.sendmessage("哎呀，那我就继续说话了", group_id)

                        break

                    chatdata = None

                    #根据聊天模式是否继续减少等待时间
                    if ChatMode:
                        end_time -= random.randint(35,55)

        else:

            continue

        print("进入外循环")
        Result = ""

        #TODO 在这里构造prompt
        try:

            #TODO
            related_memory = construct_memory(embedding.GetEmbedding(personal_result))

            if related_memory is not None:
                Result = related_memory + "\n刚刚接受到的消息：\n"
            else:
                Result = "\n刚刚接受到的消息：\n"
                print("没有相关记忆")
            #TODO

        except Exception as e2:
            print("构造prompt记忆出错",e2)


        if len(result_dict) > 10:
            result_dict = result_dict[-10:]

        for results in result_dict:
            if len(results) > 0:
                Result += results + "\n"
                # 获取群聊的消息，准备好了给ChatGPT
            else:
                print("Results为空")

        with lock:
            if len(history) > 0:
                if len(history) > 6:
                    history = history[-6:]
                if len(history) > 0:
                    if history[0] != history_forward:
                        history.insert(0, history_forward)
            if CanTalk:
                #发送消息
                Result_queue.put(history)
                print("将history", history, "放入了队列")
                Result_queue.put(Result)
                print("将Result", Result, "放入了队列")
            '''
            else:
                #清空队列
                while not Result_queue.empty():
                    with lock:
                        Result_queue.get()
            '''

#消息处理线程
def MessageQueue_handel(message_queue,thread_mapping):
    print("消息处理队列线程，启动！")
    # 处理消息队列
    while True:

        #负责给每个群处理的进程更新队列
        if not message_queue.empty():
            #获取
            item = message_queue.get()

            item_group_id = item.get('group_id',None)

            #如果从总队列中获得的群号是待回复群列表（thread_mapping）中的群号
            if item_group_id is not None:
                print("这是群组消息")
                for test_group_id in thread_mapping:
                    if str(item_group_id) == test_group_id:
                        print("找到了对应的item_group_id在threadmapping中")
                        #通过字典放入对应线程的线程共享队列(shared_queue)中
                        print("item 为",item)
                        thread_mapping[str(item_group_id)].put(item)

            else:
                #TODO 处理私人消息
                print("这是私人消息")


#用来创建进程的函数
def Create_Process(message_queue,thread_mapping,thread_Result_mapping,lock,lock_file):

    #根据群号列表创建进程，共享队列
    threads = []


    #消息队列处理进程，启动！
    MessageQueue_Thread = multiprocessing.Process(target=MessageQueue_handel, args=(message_queue,thread_mapping))
    MessageQueue_Thread.start()

    #群队列进程，启动！
    for group_id,thread_queue in thread_mapping.items():
        thread = multiprocessing.Process(target=Group_Thread, args=(group_id, thread_queue,thread_Result_mapping[group_id],lock,lock_file))
        threads.append(thread)
        thread.start()



#用来构造记忆
def construct_memory(query_vector):
    memory_section = ''
    query_result = database.Select_Embedding()
    query_time = datetime.datetime.now()
    #检索出最相似的5个message_ID
    distances, indices = embedding.SerchEmbedding(query_result,query_vector,5)
    ID_List = indices.tolist()
    for id in ID_List[0]:
        memory_sentences = []
        # 对每个ID进行查询构建相关记忆段
        related_memory = database.select_related_message(id+1)
        count_memory = 0
        for item in related_memory:
            if count_memory == 0:
                memory_time = item[0]
                time_token = compare_datetime(query_time,memory_time)
                memory_sentences.append(time_token)
            memory_sentences.append(item[1] + "：" + item[2])

            count_memory += 1

        for line in memory_sentences:
            memory_section = memory_section + "\n" + line

    return memory_section


#用来比较时间
def compare_datetime(datetime0,datetime1):
    if datetime0.year == datetime1.year:
        if datetime0.month == datetime1.month:
            if datetime0.day == datetime1.day:
                return "今天的相关记忆："
            return "近期的相关记忆："
        return "今年的相关记忆："
    else:
        return str(datetime1.year) + "年的相关记忆"