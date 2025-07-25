import os
import pysrt
import re
import shutil # 用于复制文件

def sanitize_filename(text, max_length=50):
    """清理文本，使其可以安全地用作文件名的一部分。"""
    sanitized = re.sub(r'[\\/*?:"<>|]', '', text)
    sanitized = sanitized.replace(' ', '')
    return sanitized[:max_length]

def process_text_for_comparison(text):
    """
    处理字幕或WAV文件名中的文本，以便进行比较。
    """
    processed_text = text.replace("j:", "")
    processed_text = processed_text.split('|', 1)[0]
    processed_text = re.sub(r'\s+', '', processed_text)
    processed_text = sanitize_filename(processed_text)
    return processed_text

def parse_wav_filename(filename):
    """
    辅助函数：解析WAV文件名，返回序号、语言代码、文本部分和扩展名。
    如果格式不符，返回 None。
    """
    try:
        name_without_ext, ext = filename.rsplit('.', 1)
        if ext.lower() != 'wav':
            return None
        prefix, lang_code, text_part = name_without_ext.split('_', 2)
        return prefix, lang_code, text_part, ext
    except ValueError:
        return None

def rename_wav_files_by_srt_text(srt_file_path, wav_folder_path, delete_unmatched_wavs=False):
    """
    【最终版安全逻辑】根据SRT文件，通过“锁定-复制-清理”三阶段，确保WAV文件唯一对应。
    """
    print("---- 开始处理 (最终安全逻辑) ----")
    print(f"SRT文件: {srt_file_path}")
    print(f"WAV文件夹: {wav_folder_path}")
    if delete_unmatched_wavs:
        print("警告：删除不匹配和冗余WAV文件的功能已启用！")
    else:
        print("提示：删除不匹配和冗余WAV文件的功能已禁用。")

    # --- 预处理：加载SRT并建立索引 ---
    try:
        subs = pysrt.open(srt_file_path, encoding='utf-8')
    except Exception as e:
        print(f"错误：无法打开SRT文件 '{srt_file_path}': {e}")
        return

    # srt_map: {srt_index: processed_text}
    srt_map = {f"{sub.index:04d}": process_text_for_comparison(sub.text) for sub in subs}
    # text_map: {processed_text: [srt_indexes]}
    text_map = {}
    for index, text in srt_map.items():
        if text not in text_map:
            text_map[text] = []
        text_map[text].append(index)
    
    print(f"SRT文件预处理完成，共 {len(subs)} 条字幕。")

    # 初始化计数器
    locked_count, copied_count, deleted_count, no_source_count = 0, 0, 0, 0
    
    # --- 第一阶段：识别与锁定“完美匹配”的文件 ---
    print("\n---- 开始第一阶段：锁定完美匹配的文件 ----")
    locked_wav_files = set()
    unmatched_srt_indexes = set(srt_map.keys())
    
    initial_wav_files = os.listdir(wav_folder_path)
    wav_file_info = {} # 存储所有WAV文件的解析信息

    for filename in initial_wav_files:
        parsed = parse_wav_filename(filename)
        if parsed:
            prefix, lang, text, ext = parsed
            processed_text = process_text_for_comparison(text)
            wav_file_info[filename] = {
                "prefix": prefix, "lang_code": lang, "text_part": text, "ext": ext, "processed_text": processed_text
            }
            # 检查是否为完美匹配
            if prefix in srt_map and srt_map[prefix] == processed_text:
                print(f"  -> 锁定: '{filename}' 是SRT序号 {prefix} 的完美匹配。")
                locked_wav_files.add(filename)
                unmatched_srt_indexes.remove(prefix)
                locked_count += 1

    print(f"第一阶段完成。{locked_count} 个文件被确认为完美匹配并已锁定。")
    print(f"剩余 {len(unmatched_srt_indexes)} 个SRT条目需要处理。")

    # --- 第二阶段：为剩余SRT条目复制创建WAV文件 ---
    print("\n---- 开始第二阶段：为剩余的SRT条目创建文件 ----")
    if not unmatched_srt_indexes:
        print("所有SRT条目均已完美匹配，无需进入第二阶段。")
    else:
        # 建立一个内容到源文件的映射，优先使用已锁定的文件
        source_candidates = {}
        # 优先从已锁定的文件中寻找源
        for filename in locked_wav_files:
            info = wav_file_info[filename]
            if info["processed_text"] not in source_candidates:
                source_candidates[info["processed_text"]] = filename
        # 再从其他文件中寻找，以防某个文本的所有WAV都未被锁定
        for filename, info in wav_file_info.items():
            if info["processed_text"] not in source_candidates:
                 source_candidates[info["processed_text"]] = filename
        
        for srt_index in sorted(list(unmatched_srt_indexes)): #排序保证处理顺序一致
            processed_text = srt_map[srt_index]
            print(f"处理SRT序号: {srt_index} (文本: '{processed_text}')")

            # 寻找可供复制的源文件
            source_file = source_candidates.get(processed_text)

            if not source_file:
                print(f"  -> 结果: 未能找到任何内容为 '{processed_text}' 的WAV文件作为复制源。")
                no_source_count += 1
                continue

            # 构建目标文件名并执行复制
            source_info = wav_file_info[source_file]
            target_filename = f"{srt_index}_{source_info['lang_code']}_{source_info['text_part']}.{source_info['ext']}"
            target_path = os.path.join(wav_folder_path, target_filename)
            
            if os.path.exists(target_path):
                 print(f"  -> 跳过: 目标文件 '{target_filename}' 已存在。")
                 # 即使已存在，也必须将其锁定
                 locked_wav_files.add(target_filename)
            else:
                try:
                    source_path = os.path.join(wav_folder_path, source_file)
                    shutil.copy2(source_path, target_path)
                    print(f"  -> 操作: 从 '{source_file}' 复制创建了 '{target_filename}'")
                    locked_wav_files.add(target_filename)
                    copied_count += 1
                except Exception as e:
                    print(f"  -> 错误: 复制文件时出错: {e}")
    
    print(f"第二阶段完成。")

    # --- 第三阶段：最终清理 ---
    print("\n---- 开始第三阶段：清理所有未被锁定的文件 ----")
    if not delete_unmatched_wavs:
        print("删除功能已禁用，跳过清理阶段。")
    else:
        final_wav_files = os.listdir(wav_folder_path)
        for filename in final_wav_files:
            # 只处理wav文件，并且这个文件不在我们的安全锁定列表中
            if filename.lower().endswith('.wav') and filename not in locked_wav_files:
                try:
                    os.remove(os.path.join(wav_folder_path, filename))
                    print(f"  -> 清理: 删除冗余/不匹配文件 '{filename}'")
                    deleted_count += 1
                except OSError as e:
                    print(f"  -> 错误: 无法删除文件 '{filename}': {e}")
        print(f"第三阶段完成。{deleted_count} 个文件被清理。")

    # --- 操作摘要 ---
    print("\n--- 操作摘要 ---")
    print(f"第一阶段锁定的完美匹配文件数量： {locked_count}")
    print(f"第二阶段复制创建的文件数量： {copied_count}")
    print(f"SRT条目因无任何内容匹配的源WAV而跳过的数量： {no_source_count}")
    if delete_unmatched_wavs:
        print(f"第三阶段清理删除的文件数量： {deleted_count}")
    print(f"---- 处理完成 ----")


# --- 主执行块 ---
if __name__ == "__main__":
    # !!! 重要：设置此项来控制是否删除不匹配和冗余的WAV文件 !!!
    DELETE_UNMATCHED_FILES = True

    # 示例路径 (请根据你的操作系统和文件位置进行修改):
    srt_file_path = "E:/抽吧唧/薬屋のひとりごと展/2.srt"
    wav_folder_path = "E:/抽吧唧/薬屋のひとりごと展/sub"

    # --- ----------------------------------------------- ---

    if not os.path.exists(srt_file_path):
        print(f"错误：SRT文件 '{srt_file_path}' 不存在。请检查路径是否正确。")
    elif not os.path.isfile(srt_file_path):
        print(f"错误：'{srt_file_path}' 不是一个文件。请检查路径。")
    elif not os.path.exists(wav_folder_path):
        print(f"错误：WAV文件夹 '{wav_folder_path}' 不存在。请检查路径是否正确。")
    elif not os.path.isdir(wav_folder_path):
        print(f"错误：'{wav_folder_path}' 不是一个文件夹。请检查路径。")
    else:
        rename_wav_files_by_srt_text(srt_file_path, wav_folder_path, delete_unmatched_wavs=DELETE_UNMATCHED_FILES)