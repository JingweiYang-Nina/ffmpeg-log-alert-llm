import subprocess
import requests
import json

def capture_ffmpeg_stderr(command_string):
    """
    通过 shell 执行字符串形式的 ffmpeg 命令，只返回 stderr。
    """
    result = subprocess.run(
        command_string,
        shell=True,
        capture_output=True,
        text=True,
        check=False
    )
    return result.stderr

def send_to_vllm(text):
    """
    将原始文本直接作为用户消息发送给 vLLM (OpenAI 兼容 API)，
    不添加任何额外提示词。
    """
    api_url = "http://localhost:8000/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "ffmodel", 
        "messages": [
            {"role": "user", "content": text}
        ],
        "max_tokens": 512,
        "temperature": 0.0   # 确定性输出
    }
    try:
        resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        reply = resp.json()["choices"][0]["message"]["content"]
        return reply
    except Exception as e:
        return f"请求失败: {e}"

if __name__ == "__main__":
    # 两个 ffmpeg 命令（字符串形式）
    cmd_success = "ffmpeg -i stylegan.mp4 -c:v libx264 -preset medium -crf 23 -c:a aac -movflags +faststart -y stylegan_output.mp4"
    cmd_failure = "ffmpeg -i stylegan.mp4 -c:v fake_video_encoder -c:a aac stylegan_error.mp4"

    print("=" * 60)
    print("执行【成功】命令，捕获 stderr 并发送给 vLLM")
    print("=" * 60)
    stderr1 = capture_ffmpeg_stderr(cmd_success)
    print(f"--- 捕获到的 stderr 长度: {len(stderr1)} 字符 ---")
    print("--- 捕获到的 stderr (前500字符) ---")
    print(stderr1[:500] if stderr1 else "(无内容)")
    
    print("\n--- 发送到 vLLM (端口8000)，等待推理结果 ---")
    reply1 = send_to_vllm(stderr1)
    print("模型回复:\n", reply1)

    print("\n" + "=" * 60)
    print("执行【失败】命令，捕获 stderr 并发送给 vLLM")
    print("=" * 60)
    stderr2 = capture_ffmpeg_stderr(cmd_failure)
    print(f"--- 捕获到的 stderr 长度: {len(stderr2)} 字符 ---")
    print("--- 捕获到的 stderr (前500字符) ---")
    print(stderr2[:500] if stderr2 else "(无内容)")
    
    print("\n--- 发送到 vLLM (端口8000)，等待推理结果 ---")
    reply2 = send_to_vllm(stderr2)
    print("模型回复:\n", reply2)
