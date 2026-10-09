import subprocess

def capture_ffmpeg_output(command_string):
    """
    通过 shell 执行字符串形式的 ffmpeg 命令，捕获 stdout 和 stderr。
    """
    result = subprocess.run(
        command_string,
        shell=True,
        capture_output=True,
        text=True,
        check=False
    )
    return result.stdout, result.stderr

if __name__ == "__main__":
    # 两个命令（字符串形式）
    cmd_success = "ffmpeg -i stylegan.mp4 -c:v libx264 -preset medium -crf 23 -c:a aac -movflags +faststart -y stylegan_output.mp4"
    cmd_failure = "ffmpeg -i stylegan.mp4 -c:v fake_video_encoder -c:a aac stylegan_error.mp4"

    print("=" * 60)
    print("执行【成功】命令（正常转码）")
    print("=" * 60)
    stdout1, stderr1 = capture_ffmpeg_output(cmd_success)
    print("--- stdout ---")
    print(stdout1 if stdout1 else "(无内容)")
    print("--- stderr ---")
    print(stderr1 if stderr1 else "(无内容)")

    print("\n" + "=" * 60)
    print("执行【失败】命令（使用不存在的编码器）")
    print("=" * 60)
    stdout2, stderr2 = capture_ffmpeg_output(cmd_failure)
    print("--- stdout ---")
    print(stdout2 if stdout2 else "(无内容)")
    print("--- stderr ---")
    print(stderr2 if stderr2 else "(无内容)")

