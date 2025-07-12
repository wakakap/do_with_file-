def merge_files(file1_path, file2_path, output_path):
    try:
        with open(file1_path, 'r', encoding='utf-8') as f1, \
             open(file2_path, 'r', encoding='utf-8') as f2, \
             open(output_path, 'w', encoding='utf-8') as outfile:

            # 使用 zip 函数逐行配对读取
            # 当其中一个文件读取完毕时，zip 会自动停止
            for line1, line2 in zip(f1, f2):
                # 去除每行末尾的换行符，然后用逗号拼接
                merged_line = f"{line1.strip()},{line2.strip()}\n"
                outfile.write(merged_line)
        print(f"文件合并成功！已保存至：{output_path}")

    except FileNotFoundError:
        print("错误：一个或两个输入文件未找到。请检查文件路径是否正确。")
    except Exception as e:
        print(f"发生未知错误：{e}")

# 1. 定义你的文件路径
# 请将下面的路径替换成你自己的实际文件路径
path_to_file1 = 'niconico/takop/need_honyaku_temp.txt'  # 第一个输入文件
path_to_file2 = 'niconico/takop/honyaku_temp.txt'  # 第二个输入文件
path_to_output = 'niconico/takop/merged_file.txt' # 合并后的输出文件


merge_files(path_to_file1, path_to_file2, path_to_output)

# 3. (可选) 打印输出文件的内容进行验证
print("\n合并后文件的内容：")
with open(path_to_output, 'r', encoding='utf-8') as f:
    print(f.read())