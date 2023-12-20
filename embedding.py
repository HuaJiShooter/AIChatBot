from transformers import BertTokenizer, BertModel
import torch
import json
import numpy as np
import time
import os
import faiss
from sklearn.metrics.pairwise import cosine_similarity



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


def SerchEmbedding(SentenceEmbedding,query_vector,num_to_search):
    starttime = time.time()
    vecs = np.array(SentenceEmbedding)
    d = vecs.shape[1]
    index = faiss.IndexFlatIP(d)
    index.add(vecs)
    distances, indices = index.search(query_vector, num_to_search)
    print("此次余弦比较时间为",time.time() - starttime)
    return distances,indices