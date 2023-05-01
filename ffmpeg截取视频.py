import os


try:
    input_path = str(input("请输入输入文件的路径："))
    out_path  = str(input("请输入输出文件的路径：")) or "E:\BaiduNetdiskDownload"
    input_filename = str(input("请输入输入文件的文件名："))
    start_time = input("请输入起始时间（格式：00:00:00）：")
    end_time = input("请输入结束时间（格式：00:00:00）：")

    input_file_path = '"' + os.path.join(input_path, input_filename) + '"'

    # 将时间转换为秒数
    start_seconds = sum(x * int(t) for x, t in zip([3600, 60, 1], start_time.split(":")))
    end_seconds = sum(x * int(t) for x, t in zip([3600, 60, 1], end_time.split(":")))

    output_filename = f"{input_filename}_{start_time}-{end_time}.mp4".replace(':', '_')
    out_file_path = '"' + os.path.join(out_path, output_filename) + '"'

    # 构造ffmpeg命令并执行
    command = f"ffmpeg -i {input_file_path} -ss {start_seconds} -to {end_seconds} -c:v h264 -crf 11 {out_file_path}"
    os.system(command)

    print("操作完成！")

except Exception as e:
    print(f"发生错误：{e}")
