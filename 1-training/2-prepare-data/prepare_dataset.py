#!/usr/bin/env python3
"""
将 ffmpeg_logs 目录下的 .log 与配对的 .result 整理成微调数据集格式
格式：包含 conversations 数组，每个消息有 role 和 content 字段
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def read_text_file(path: str) -> str:
    """读取文本文件内容（log / result）"""
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            content = f.read().strip()
            if content.startswith("\ufeff"):
                content = content[1:]
            return content
    except FileNotFoundError:
        print(f"Warning: File not found: {path}")
        return ""
    except Exception as e:
        print(f"Error reading file {path}: {e}")
        return ""


def read_log_file(log_path: str) -> str:
    """读取 log 文件内容"""
    return read_text_file(log_path)


def load_result_json(result_path: str) -> Optional[Dict[str, Any]]:
    """加载单个 .result JSON 对象"""
    raw = read_text_file(result_path)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in {result_path}: {e}")
        return None


def create_fine_tuning_message(log_content: str, output_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    创建微调数据集格式的消息

    Args:
        log_content: log 文件内容
        output_json: 含 is_succ 或 successful、psnr_value/psnr、error_message、resolution_steps

    Returns:
        包含 conversations 数组的字典
    """
    psnr_value = output_json.get("psnr_value") or output_json.get("psnr")
    if psnr_value is None:
        psnr_value = 0.0

    if "is_succ" in output_json:
        is_succ = bool(output_json["is_succ"])
    elif "successful" in output_json:
        is_succ = bool(output_json["successful"])
    else:
        is_succ = False

    output_data = {
        "is_succ": is_succ,
        "psnr_value": psnr_value,
        "error_message": output_json.get("error_message", "") or "",
        "resolution_steps": output_json.get("resolution_steps", "") or "",
    }
    output_json_str = json.dumps(output_data, ensure_ascii=False, indent=None)

    return {
        "conversations": [
            {"role": "user", "content": log_content},
            {"role": "assistant", "content": output_json_str},
        ]
    }


def prepare_dataset(log_dir: str, output_file: str) -> None:
    """
    准备微调数据集：遍历 log_dir 下所有 ffmpeg_log_*.log，读取同名 .result。

    Args:
        log_dir: 同时存放 .log 与 .result 的目录
        output_file: 输出数据集文件路径
    """
    log_dir_path = Path(log_dir)
    log_files = sorted(log_dir_path.glob("ffmpeg_log_*.log"))
    print(f"Scanning {log_dir_path} ...")
    print(f"Found {len(log_files)} .log files")

    dataset: List[Dict[str, Any]] = []
    missing_result = 0
    bad_result = 0
    empty_log = 0
    processed = 0

    for log_path in log_files:
        stem = log_path.stem
        result_path = log_dir_path / f"{stem}.result"

        if not result_path.exists():
            print(f"Warning: Missing result for {log_path.name}: {result_path.name}")
            missing_result += 1
            continue

        result = load_result_json(str(result_path))
        if result is None:
            bad_result += 1
            continue

        log_content = read_log_file(str(log_path))
        if not log_content:
            empty_log += 1
            continue

        message_data = create_fine_tuning_message(log_content, result)
        dataset.append(message_data)
        processed += 1

        if processed % 1000 == 0:
            print(f"Processed: {processed}")

    print(f"\nSaving dataset to {output_file}...")
    print(f"Total entries: {len(dataset)}")
    print(f"Missing .result: {missing_result}, Bad .result JSON: {bad_result}, Empty .log: {empty_log}")

    with open(output_file, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Dataset saved successfully! Total samples: {len(dataset)}")


def main() -> None:
    base_dir = Path(__file__).parent.resolve()
    log_dir = base_dir.parent / "1-raw-data" / "ffmpeg_logs"
    output_file = base_dir / "fine_tuning_dataset.jsonl"

    if not log_dir.exists():
        print(f"Error: Log directory not found: {log_dir}")
        return

    prepare_dataset(str(log_dir), str(output_file))


if __name__ == "__main__":
    main()
