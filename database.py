import mysql.connector
import json
import time

# 连接到 MySQL 数据库
conn = mysql.connector.connect(
    host="localhost",     # 数据库主机地址
    user="root", # 数据库用户名
    password="123456", # 数据库密码
    database="ChatHachiRoku" # 数据库名称
)


def insert_Chatdata(VectorData,Data):
    cursor = conn.cursor()
    first_query = "INSERT INTO sentence_vectors (sentence_vector) VALUES (%s)"
    data = (VectorData,)
    cursor.execute(first_query,data)
    # 提交更改
    conn.commit()

    insert_query = "INSERT INTO Messages (sender_nickname, message_content, message_datetime, group_id, vector_id) VALUES (%s, %s, %s, %s, LAST_INSERT_ID())"
    data_to_insert = (Data["Nickname"], Data["MessageContent"], Data["SendTime"],Data["group_id"])
    cursor.execute(insert_query, data_to_insert)

    # 提交更改
    conn.commit()

    # 关闭游标
    cursor.close()

def Select_Embedding():
    start_time = time.time()
    # 创建一个游标对象
    cursor = conn.cursor()

    # 构建 SQL 查询语句
    select_query = f"SELECT sentence_vector FROM sentence_vectors"

    # 执行查询
    cursor.execute(select_query)

    # 检索结果
    result = cursor.fetchall()

    parsed_data = []

    # 解析 JSON 数据
    for json_data in result:
        float_vector = json.loads(json_data[0])[0]
        parsed_data.append(float_vector)

    # 关闭游标和连接
    cursor.close()

    print("查询数据库花费", time.time() - start_time,"时间")

    return parsed_data


#查找相关对话的附近对话
def select_related_message(id):
    # 创建一个游标对象
    cursor = conn.cursor()

    # 构建 SQL 查询语句
    select_query = f"SELECT message_datetime,sender_nickname,message_content FROM messages WHERE vector_id > %s AND vector_id < %s"

    # 执行查询
    cursor.execute(select_query,(id-3,id+3))

    # 检索结果
    result = cursor.fetchall()

    # 关闭游标
    cursor.close()

    return result



# 关闭连接
def close_database():
    conn.close()