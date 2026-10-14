from transformers import AutoTokenizer


model_name = "/root/autodl-tmp/qwen35-4b/"
tokenizer = AutoTokenizer.from_pretrained(model_name)
print(tokenizer.chat_template)
