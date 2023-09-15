import GetMessage
import multiprocessing
from transformers import AutoTokenizer, AutoModel, AutoConfig
import torch
import TextHandel
import SendMessage
import os
import embedding
from ChatGLM2 import GLMmain
import global_var



def main():

    print("正在载入模型")
    # 载入Tokenizer
    tokenizer = AutoTokenizer.from_pretrained(r".\model\ChatGLM2-6b", trust_remote_code=True)
    # 加载ptuning的CheckPoint
    config = AutoConfig.from_pretrained(r".\model\ChatGLM2-6b", trust_remote_code=True, pre_seq_len=128)
    model = AutoModel.from_pretrained(r".\model\ChatGLM2-6b", config=config, trust_remote_code=True)
    prefix_state_dict = torch.load(os.path.join("./model/" + global_var.PtuningModel, "pytorch_model.bin"))
    new_prefix_state_dict = {}
    for k, v in prefix_state_dict.items():
        if k.startswith("transformer.prefix_encoder."):
            new_prefix_state_dict[k[len("transformer.prefix_encoder."):]] = v
    model.transformer.prefix_encoder.load_state_dict(new_prefix_state_dict)
    # 模型进行量化
    model = model.quantize(8).cuda().eval()
    print("模型载入成功")

    # 信息共享队列
    thread_mapping = {
        "群号1": multiprocessing.Queue(),
        "群号2": multiprocessing.Queue()
    }
    # 结果共享队列，mapping应该和信息共享队列一致
    thread_Result_mapping = {
        "群号1": multiprocessing.Queue(),
        "群号2": multiprocessing.Queue()
    }
    lock = multiprocessing.Lock()
    lock_file = multiprocessing.Lock()

    #创建获取go-cqhttp信息的进程
    Message_Queue = multiprocessing.Queue()
    GetMessage_process = multiprocessing.Process(target=GetMessage.getmessage,args=(Message_Queue,))
    GetMessage_process.start()
    Create_Process = multiprocessing.Process(target=GLMmain.Create_Process,args=(Message_Queue,thread_mapping,thread_Result_mapping,lock,lock_file))
    Create_Process.start()


    #负责让ChatGLM处理消息
    while True:
        for group_id,result_queue in thread_Result_mapping.items():
            if not result_queue.empty():
                with lock:
                    History = result_queue.get()
                    print("History is", History)
                    Result = result_queue.get()
                    print("Result is",Result)

                    GLMResult, history = predict(model,Result, History,tokenizer)
                    result_queue.put(history)

                #储存历史记录
                GLMResult = TextHandel.remove_prefix(GLMResult)
                TextHandel.append_to_txt_file("CollectedData.txt",Result,GLMResult,history)
                print("GLMResult is:" + GLMResult)

                if '\n' in GLMResult:
                    ResultList = TextHandel.lines_to_list(GLMResult)
                    for MessageResult in ResultList:
                        SendMessage.sendmessage(TextHandel.remove_prefix(MessageResult),group_id)

                        MemorySentence = global_var.CharacterName+ "：" + TextHandel.remove_prefix(MessageResult)
                        MemoryResult = {"sentence": MemorySentence,
                                        "embedding": embedding.GetEmbedding(MemorySentence).tolist()}
                        with lock_file:
                            TextHandel.append_to_memory_file(r'.\memory\truememory.json',MemoryResult)
                else:
                    SendMessage.sendmessage(TextHandel.remove_prefix(GLMResult),group_id)

                    MemorySentence = global_var.CharacterName + "：" + TextHandel.remove_prefix(GLMResult)
                    MemoryResult = {"sentence": MemorySentence,
                                    "embedding": embedding.GetEmbedding(MemorySentence).tolist()}

                    with lock_file:
                        TextHandel.append_to_memory_file(r'.\memory\truememory.json', MemoryResult)


def predict(model,query,history,tokenizer):
    response, history = model.chat(tokenizer, query, history)
    return response,history



if __name__ == "__main__":
    main()