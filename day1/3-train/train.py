from unsloth import FastLanguageModel, FastModel
import torch
from trl import SFTTrainer, SFTConfig
from datasets import load_dataset
from unsloth import to_sharegpt
from unsloth import standardize_sharegpt
from unsloth import is_bfloat16_supported
from unsloth import apply_chat_template
from transformers import TrainingArguments
from transformers import TextStreamer
from torchao.quantization import quantize_
from torchao.quantization.qat import QATConfig

max_seq_length = 4096

model, processor = FastLanguageModel.from_pretrained(
    model_name = "/root/autodl-tmp/qwen35-4b",
    load_in_4bit = False,
    load_in_8bit = False,
    full_finetuning = False,
    use_gradient_checkpointing = True,
    local_files_only=True,
)
tokenizer = processor.tokenizer

model = FastLanguageModel.get_peft_model(
   model,
   finetune_vision_layers     = False, # False if not finetuning vision layers
   finetune_language_layers   = True, # False if not finetuning language layers
   finetune_attention_modules = True, # False if not finetuning attention layers
   finetune_mlp_modules       = True, # False if not finetuning MLP layers
   r = 32,
   target_modules = ["q_proj", "k_proj", "v_proj", "o_proj","gate_proj", "up_proj", "down_proj",],
   lora_alpha = 32,
   lora_dropout = 0,
   bias = "none",
   use_gradient_checkpointing = True,
   random_state = 3407,
   use_rslora = False,
   loftq_config = None,
)


dataset = load_dataset('json', data_files='../2-prepare-data/fine_tuning_dataset.jsonl', split='train')
print(dataset.column_names)

# dataset = to_sharegpt(
#     dataset,
#     merged_prompt="[[\nYour input is:\n{prompt}]]",
#     output_column_name="completion",
#     conversation_extension=3,  # Select more to handle longer conversations
# )

dataset = standardize_sharegpt(dataset)

chat_template = """Below are some instructions that describe some tasks. Write responses that appropriately complete each request.

### Instruction:
{INPUT}

### Response:
{OUTPUT}"""


dataset = apply_chat_template(
    dataset,
    tokenizer=tokenizer,
    chat_template=chat_template,
    # default_system_message = "You are a helpful assistant", << [OPTIONAL]
)

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 8,
    packing = False, # Can make training 5x faster for short sequences.
    args = TrainingArguments(
        per_device_train_batch_size = 1,
        gradient_accumulation_steps = 16,
        warmup_steps = 5,
        #max_steps = 6,
        num_train_epochs = 3, # For longer training runs!
        learning_rate = 5e-4,
        fp16 = not is_bfloat16_supported(),
        bf16 = is_bfloat16_supported(),
        logging_steps = 2,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "outputs",
        report_to = "none", # Use this for WandB etc
    ),
)

gpu_stats = torch.cuda.get_device_properties(0)
start_gpu_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
print(f"GPU = {gpu_stats.name}. Max memory = {max_memory} GB.")
print(f"{start_gpu_memory} GB of memory reserved.")

trainer_stats = trainer.train()

used_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
used_memory_for_lora = round(used_memory - start_gpu_memory, 3)
used_percentage = round(used_memory / max_memory * 100, 3)
lora_percentage = round(used_memory_for_lora / max_memory * 100, 3)
print(f"{trainer_stats.metrics['train_runtime']} seconds used for training.")
print(
    f"{round(trainer_stats.metrics['train_runtime']/60, 2)} minutes used for training."
)
print(f"Peak reserved memory = {used_memory} GB.")
print(f"Peak reserved memory for training = {used_memory_for_lora} GB.")
print(f"Peak reserved memory % of max memory = {used_percentage} %.")
print(f"Peak reserved memory for training % of max memory = {lora_percentage} %.")

FastLanguageModel.for_inference(model) # Enable native 2x faster inference

def chat(content: str, model, tokenizer, max_new_tokens: int = 128):
    messages = [{"role": "user", "content": content}]

    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt = True, # Must add for generation
        tokenize = True,
        return_tensors = "pt",
        return_dict = True,
        )

    _ = model.generate(
        **inputs.to("cuda"),
        max_new_tokens = 512, # Increase for longer outputs!
        temperature = 0.7, top_p = 0.8, top_k = 20,
        use_cache = True,
        streamer = TextStreamer(tokenizer, skip_prompt = True),
    )

    print()

chat("Below are FFmpeg transcode log content that describe the result of the video transcoding. Analyze the log content and provide the transcoding status, PSNR value, any detected error message, and suggested resolution steps in json.ffmpeg -i input.mp4 -c:v libx264 -crf 23 -f null -\nffmpeg version 4.4.2-0ubuntu0.22.04.1 Copyright (c) 2000-2021 FFmpeg developers\nInput #0, mov,mp4,m4a,3gp,3g2,mj2, from 'input.mp4':\n  Duration: 00:00:10.00, start: 0.000000, bitrate: 1000 kb/s\n    Stream #0:0: Video: h264 (High), yuv420p, 1280x720, 25 fps\nOutput #0, null, to 'pipe:1':\n  Metadata:\n    encoder         : Lavf58.76.100\n    Stream #0:0: Video: h264 (libx264), yuv420p, 1280x720, q=-1--1, 25 fps\nStream mapping:\n  Stream #0:0 -> #0:0 (h264 (native) -> libx264 (libx264))\nPress [q] to stop, [?] for help.\nframe=  250 fps= 25 q=28.0 size=N/A time=00:00:10.00 bitrate=N/A speed=1.00x\nvideo:0kB audio:0kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: 0.000000%", model, tokenizer)
chat("Below are FFmpeg transcode log content that describe the result of the video transcoding. Analyze the log content and provide the transcoding status, PSNR value, any detected error message, and suggested resolution steps in json.ffmpeg -i input.mp4 -c:v copy -b:v 1G -c:a copy output_large_bitrate.mp4\nffmpeg version 4.4.2-0ubuntu0.22.04.1 Copyright (c) 2000-2021 FFmpeg developers\n[mp4 @ 0x...] Value 1000000000 for parameter 'video_bit_rate' is out of range [-2147483648 - 2147483647]\nCould not write header for output file 'output_large_bitrate.mp4': Invalid argument\nConversion failed!", model, tokenizer)
chat("Below are FFmpeg transcode log content that describe the result of the video transcoding. Analyze the log content and provide the transcoding status, PSNR value, any detected error message, and suggested resolution steps in json. ffmpeg version N-random-g897d21b1b44 shared. Build: gcc-latest.\nInput #0, mov,mp4, from 'input_video_5.mp4':\n  Duration: 00:00:13.00, start: 0.000000, bitrate: 622 kb/s\n    Stream #0:0: Video: h264 (Main), yuv420p, 1920x1080, 52 fps\n    Stream #0:1: Audio: aac, 48000 Hz, stereo\n[libx264 @ 0x81b53c73796d10f5] PSNR Y:46.39 U:48.91 V:47.38 Avg:47.56 Global:47.74\nOutput #0, mp4, to 'output_video_54.mp4':\n  Stream #0:0: Video: h264 (H.264 Main)\n  Stream #0:1: Audio: aac\nframe=  676 fps= 37 q=29.0 size=     48003kB time=00:00:13.00 bitrate=2870kbits/s speed=2.1x\nvideo:43202kB audio:4800kB subtitle:0kB other streams:0kB global headers:0kB muxing overhead: 0.000%", model, tokenizer)


print("saving...")
model.save_pretrained_merged("/root/autodl-tmp/qwen35-4b-finetuned-ffmpeglog", tokenizer)
#tokenizer.save_pretrained("/root/autodl-tmp/qwen35-08b-finetuned-ffmpeglog")
print("saved")
