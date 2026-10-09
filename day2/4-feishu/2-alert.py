import requests
import json

def alert(is_succ, psnr_value, error_message, resolution_steps):
    """
    发送飞书告警，参数与 vLLM 返回的 JSON 字段保持一致
    """
    webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/4a857461-572f-48c7-853b-cb758cc7d7e8"

    # 构造消息文本
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
        response = requests.post(
            url=webhook_url,
            data=json.dumps(data),
            headers=headers,
            timeout=5
        )
        print("Status Code:", response.status_code)
        print("Response Body:", response.text)
    except requests.exceptions.RequestException as e:
        print("请求失败:", e)

def main():
    # 模拟从 vLLM 返回的 JSON 数据（实际应使用 requests 或其他方式获得）
    vllm_response_json = {
        "is_succ": False,
        "psnr_value": 0.0,
        "error_message": "Unknown encoder 'fake_video_encoder'.",
        "resolution_steps": "Install the required codec library (e.g., `libx264`, `libvpx`) or use a supported encoder available on your system (e.g., `libx264`, `libmp3lame`)."
    }

    alert(
        is_succ=vllm_response_json["is_succ"],
        psnr_value=vllm_response_json["psnr_value"],
        error_message=vllm_response_json["error_message"],
        resolution_steps=vllm_response_json["resolution_steps"]
    )

if __name__ == "__main__":
    main()
