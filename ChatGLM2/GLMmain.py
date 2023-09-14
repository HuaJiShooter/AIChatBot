import multiprocessing
import queue
import time
import random
import TextHandel
import SendMessage
import embedding

def Group_Thread(group_id,shared_queue,Result_queue,lock,lock_file):
    #shared_queue中只有一个group的消息
    history = []
    print(group_id + "线程启动成功")
    ChatMode = False
    CanTalk = True
    while True:

        interval = random.randint(300, 360)  # 默认等待参数
        timeoutsecond = random.randint(30, 60)  # 超时时间
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
                    end_time -= 15

                    personal_result = chatdata["nickname"] + '：' + chatdata["message"]  # 聊天结果(单人)
                    personal_result = TextHandel.replace_cq_image(personal_result)  # 处理表情

                    #TODO 这里将消息存入记忆
                    with lock_file:
                        try:
                            sentence_embedding = embedding.GetEmbedding(personal_result).tolist()
                            memorydata = {"sentence": personal_result, "embedding": sentence_embedding}
                            TextHandel.append_to_memory_file(r'.\memory\truememory.json',memorydata)
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

        with lock_file:
            try:
                    # 获取最后一个personal_result进行预先比较构造相关记忆段
                related_momory = embedding.find_most_similar_sentence(embedding.GetEmbedding(personal_result), "./memory")
                if related_momory is not None:
                    Result = "记忆相关内容\n" + related_momory + "\n记忆相关内容\n" + "\n"
                else:
                    print("没有相关记忆")
            except Exception as e2:
                print("余弦比较出错",e2)


        if len(result_dict) > 10:
            result_dict = result_dict[-10:]

        for results in result_dict:
            if len(results) > 0:
                Result += results + "\n"
                # 获取群聊的消息，准备好了给ChatGPT
            else:
                print("Results为空")

        with lock:
            if len(history) > 5:
                history = history[-5:]
            if CanTalk:
                #发送消息
                history = []
                Result_queue.put(history)
                print("将history", history, "放入了队列")
                Result_queue.put(Result)
                print("将Result", Result, "放入了队列")
            else:
                #清空队列
                while not Result_queue.empty():
                    Result_queue.get()

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

    #消息处理进程，启动！
    for group_id,thread_queue in thread_mapping.items():
        thread = multiprocessing.Process(target=Group_Thread, args=(group_id, thread_queue,thread_Result_mapping[group_id],lock,lock_file))
        threads.append(thread)
        thread.start()

    #消息队列处理进程，启动！
    MessageQueue_Thread = multiprocessing.Process(target=MessageQueue_handel, args=(message_queue,thread_mapping))
    MessageQueue_Thread.start()