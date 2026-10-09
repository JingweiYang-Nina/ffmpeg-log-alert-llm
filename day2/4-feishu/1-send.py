import requests

# 飞书机器人 Webhook URL（请替换为您自己的地址）
webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/4a857461-572f-48c7-853b-cb758cc7d7e8"

def send_alert(message):
    """发送纯文本告警消息到飞书"""
    data = {
        "msg_type": "text",
        "content": {"text": message}
    }
    try:
        resp = requests.post(webhook_url, json=data, timeout=5)
        print(f"状态码: {resp.status_code}")
        print(f"响应: {resp.text}")
    except Exception as e:
        print(f"发送失败: {e}")

if __name__ == "__main__":
    send_alert("hello")
