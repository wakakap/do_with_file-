import subprocess
import math
import os

input_file = "input.mp4"
output_file = "output.mp4"
segment_length = 3
black_duration = 3
resolution = "1920x1080"

# 1. 获取视频时长
def get_duration(file):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration", "-of",
         "default=noprint_wrappers=1:nokey=1", file],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return float(result.stdout)

duration = get_duration(input_file)
print(f"Video duration: {duration} seconds")

# 2. 生成分段和黑色视频
os.makedirs("chunks", exist_ok=True)
parts = []
index = 0
t = 0

while t < duration:
    seg_out = f"chunks/part_{index}.mp4"
    cmd = [
        "ffmpeg", "-y", "-i", input_file,
        "-ss", str(t), "-t", str(segment_length),
        "-c", "copy", seg_out
    ]
    subprocess.run(cmd)
    parts.append(seg_out)
    index += 1

    # 插入黑屏
    black_out = f"chunks/black_{index}.mp4"
    cmd_black = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=color=black:s={resolution}:d={black_duration}",
        "-c:v", "libx264", "-t", str(black_duration),
        black_out
    ]
    subprocess.run(cmd_black)
    parts.append(black_out)
    index += 1

    t += segment_length

# 3. 生成 concat 文件
with open("chunks/concat_list.txt", "w") as f:
    for p in parts:
        f.write(f"file '{os.path.abspath(p)}'\n")

# 4. 合并所有段
subprocess.run([
    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
    "-i", "chunks/concat_list.txt",
    "-c", "copy", output_file
])

print(f"Done! Output saved as {output_file}")
