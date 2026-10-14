from vllm import SamplingParams
from vllm.utils import random_uuid
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.engine.arg_utils import AsyncEngineArgs
from transformers import AutoTokenizer
import httpx
import asyncio

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import json
import re
import time
import json


async def alert(is_succ, psnr_value, error_message, resolution_steps):
    """发送飞书告警（仅在转码失败时调用）"""
    webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/4a857461-572f-48c7-853b-cb758cc7d7e8"

    content_text = (
        f"转码是否成功: {is_succ}\n"
        f"PSNR 值: {psnr_value}\n"
        f"错误信息: {error_message}\n"
        f"解决步骤: {resolution_steps}\n"
    )

    data = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": "转码告警",
                    "content": [
                        [
                            {"tag": "text", "text": content_text},
                            {"tag": "a", "text": "点击进行更多操作", "href": "http://www.baidu.com/"},
                            {"tag": "text", "text": "\n"},
                            {"tag": "at", "user_id": "all"}
                        ]
                    ]
                }
            }
        }
    }

    headers = {"Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                url=webhook_url,
                json=data,
                headers=headers
            )
            print("飞书响应状态码:", resp.status_code)
            print("飞书响应内容:", resp.text)
    except Exception as e:
        print("发送飞书告警失败:", e)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行（startup）
    global llm
    global sampling_params
    global tokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        "/root/autodl-tmp/qwen35-4b-finetuned-ffmpeglog",
        trust_remote_code=True
    )

    print("service start, LLM initing ...")
    engine_args = AsyncEngineArgs(
        model="/root/autodl-tmp/qwen35-4b-finetuned-ffmpeglog",
        max_model_len=8192,
        max_num_batched_tokens=8192,
        tensor_parallel_size=1,
        gpu_memory_utilization=0.90,
        trust_remote_code=True,
        language_model_only=True,
    )
    llm = AsyncLLMEngine.from_engine_args(engine_args)

    sampling_params = SamplingParams(
        max_tokens=512,
        temperature=0.0,
        top_p=1.0,
        top_k=-1,
    )
    
    yield

    print("sevice is shuting down, cleaning...")
    if llm:
        del llm

async def vllm_analyze(log_str: str):
    conversation = [
        {"role": "user", "content": log_str}
    ]
    
    prompt_str = tokenizer.apply_chat_template(
        conversation,
        tokenize=False,
        add_generation_prompt=True
    )
    request_id = random_uuid()
    final_output = None
    async for output in llm.generate(prompt_str, sampling_params, request_id):
        final_output = output
    return final_output.outputs[0].text



# ------------------------------------------------------------
# Parse vLLM response
# ------------------------------------------------------------
def parse_vllm_response(raw_text: str) -> dict:
    """
    解析 vLLM 模型输出的原始文本，提取 JSON 中的四个字段：
    is_succ, psnr_value, error_message, resolution_steps。
    若解析失败则返回安全的默认值。
    """
    try:
        # Assume the model outputs pure JSON
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        # Try to find a JSON object inside the text
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            # Fallback when no JSON found
            parsed = {
                "is_succ": False,
                "psnr_value": 0.0,
                "error_message": f"Model output cannot be parsed as JSON: {raw_text[:200]}",
                "resolution_steps": "Please check model output format"
            }
    # Ensure all four fields exist
    return {
        "is_succ": parsed.get("is_succ", False),
        "psnr_value": parsed.get("psnr_value", 0.0),
        "error_message": parsed.get("error_message", "Unknown error"),
        "resolution_steps": parsed.get("resolution_steps", "No solution provided"),
    }


app = FastAPI(
        title="Log Analyzer VLLM Service", 
        description="Log Analyzer VLLM Service",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
        )

@app.get("/health")
def health():
    return {"message": '"Always."-Snape'}

@app.post("/analyze")
async def analyze_log(request: Request):
    body = await request.body()
    ffmpeg_log_str = body.decode("utf-8")

    max_retries = 3
    result = None
    raw_text = None

    for attempt in range(1, max_retries + 1):
        try:
            raw_text = await vllm_analyze(ffmpeg_log_str)
            result = parse_vllm_response(raw_text)
            print(f"Parsing successful on attempt {attempt}")
            break
        except ValueError as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                # Final fallback result
                result = {
                    "is_succ": False,
                    "psnr_value": 0.0,
                    "error_message": f"Model output invalid after {max_retries} attempts. Last raw output: {raw_text[:200] if raw_text else 'None'}",
                    "resolution_steps": "Please check model output format or retry manually."
                }
                break
            # Wait a short time before retry (optional)
            await asyncio.sleep(1)

    # Print final result
    print("\n===== vLLM Response =====")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=========================\n")

    # Decide whether to send Feishu alert
    if result["is_succ"]:
        print("Transcoding succeeded (is_succ=True). Skipping Feishu alert.")
    else:
        print("Transcoding failed. Sending alert to Feishu...")
        await alert(**result)

    return result
