from transformers import BertTokenizer, BertModel
import torch
import json
import numpy as np
import time
import os
from sklearn.metrics.pairwise import cosine_similarity



def find_most_similar_sentence(input_embedding, memory_foldername):
        # Load data from memory.json with utf-8 encoding
    starttime = time.time()

    data = []
    most_similar_sentence = ''

        #获取memory文件夹中的每一个文件名并依次处理
    # 使用 os.listdir() 获取文件夹中的所有文件和子文件夹
    memory_folder_data = os.listdir(memory_foldername)
    # 打印文件名列表
    for memory_filename in memory_folder_data:
        with open(memory_foldername + '/' + memory_filename, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))

    print("检查点1")

    if not data:
        print("相关记忆数据为空")
        return None  # Return None if no data in memory.json

    # Extract embeddings from data and convert to Numpy arrays
    embeddings = [np.array(item["embedding"][0]) for item in data]

    # Calculate cosine similarity between input embedding and all embeddings
    similarity_scores = cosine_similarity(input_embedding, embeddings)[0]

    print("检查点2")

    # Sort indices based on similarity scores
    sorted_indices = np.argsort(similarity_scores)[::-1]

    # Retrieve the most similar sentence
    for i in sorted_indices[:6]:
        most_similar_sentence += ("\n" + data[i]["sentence"])

    costtime = time.time() - starttime
    print("此次余弦比较花费时间为:",costtime)

    return most_similar_sentence

# Load pre-trained model and tokenizer
model_name = r'.\model\bert-base-chinese'
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertModel.from_pretrained(model_name)


def GetEmbedding(sentence):

    # Tokenize input and convert to tensor
    input_ids = torch.tensor(tokenizer.encode(sentence, add_special_tokens=True)).unsqueeze(0)

    # Get model output (embedding)
    with torch.no_grad():
        output = model(input_ids)
        sentence_embedding = output.last_hidden_state.mean(dim=1)  # You can use mean pooling for sentence embedding

    return sentence_embedding