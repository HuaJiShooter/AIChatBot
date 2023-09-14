import os
import platform
import signal
from transformers import AutoTokenizer, AutoModel, AutoConfig
import torch
#载入Tokenizer
tokenizer = AutoTokenizer.from_pretrained("model", trust_remote_code=True)
#加载ptuning的CheckPoint
config = AutoConfig.from_pretrained("model", trust_remote_code=True, pre_seq_len=128)
model = AutoModel.from_pretrained("model", config=config, trust_remote_code=True)
prefix_state_dict = torch.load(os.path.join("ptuning_model", "pytorch_model.bin"))
new_prefix_state_dict = {}
for k, v in prefix_state_dict.items():
    if k.startswith("transformer.prefix_encoder."):
        new_prefix_state_dict[k[len("transformer.prefix_encoder."):]] = v
model.transformer.prefix_encoder.load_state_dict(new_prefix_state_dict)
#模型进行量化
model = model.quantize(8).cuda().eval()

os_name = platform.system()
clear_command = 'cls' if os_name == 'Windows' else 'clear'
stop_stream = False


def signal_handler(signal, frame):
    global stop_stream
    stop_stream = True


def predict(query,history):
    response, history = model.chat(tokenizer, query, history)
    return response,history


if __name__ == "__main__":
    main()
