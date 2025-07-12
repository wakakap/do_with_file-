# -*- coding: utf-8 -*-
# 我在做一个翻译弹幕文件ass的项目，用python帮我实现以下功能，并把功能集成在一个界面上。我的设计思路是: 翻译的文件是jp.ass，新建文件jp_ch.ass，储存数据的hoyanku_data.csv。文件浏览选择jp.ass，功能1“检查ass”: 读取jp.ass，找到Format开头的行，然后从下一行逐行扫描，每一行必须满足的格式是：Dialogue: 0,0:00:00.00,0:00:09.00,Default,,0,0,0,,{xxx}string 你需要检查开头是否是Dialogue: 逗号数量是否正确，时间格式是否正确，{xxx}部分是否缺失{}。返回所有不满足的行序号。功能2“检查对应格式”：选择jp_ch.ass和jp.ass两个文件路径（设计出用户可拖拽进界面就填入路径的形式），然后逐行扫描两个文件，只有序号相同的行才会比较，忽略掉每行string部分，前面的Dialogue: 0,0:00:00.00,0:00:09.00,Default,,0,0,0,,{xxx}部分如果不一致，则返回这一行的序号，每次运行返回第一个不相同的行序号即可。功能3“新建jp_ch.ass”：选择jp.ass路径，把每一行都原封不动地复制，但删除掉每行string部分，保存到相同路径下“jp_ch.ass”。功能4“扫描已有翻译”：选择jp.ass，jp_ch.ass和hoyanku_data.csv三个文件路径，先运行功能2，如果功能2所有行相同再运行：扫描jp.ass每行，把其中的string部分提取出来在hoyanku_data中搜索，如果存在对应翻译记录，则把jp_ch.ass中相同行的string内容替换成对应的翻译，并同时记录找到有对应翻译记录时的行号，最后全部扫描完后，把行号保存在同目录的already_index_temp.txt文件里,用逗号分隔。功能5：读取already_index_temp.txt路径和jp.ass路径，把jp.ass中没在already_index_temp.txt中出现且满足Dialogue:开头的行进行扫描，提取每行的string部分，然后每个string占一行保存在同目录的need_honyaku_temp.text文件中，用于记录需要让AI翻译的内容。功能6：我会把自己用其他方式把need_honyaku_temp.text中的内容翻译好，保存到同目录的honyaku_temp.text文件中。这里选择honyaku_temp.text和already_index_temp.txt的路径，然后把honyaku_temp.text中的每行内容提取出来，逐行付给没在already_index_temp.txt中出现的jp_ch.ass行的string部分，already_index_temp.txt扫描到最后行后看对应的是否恰好是jp_ch.ass中没在already_index_temp.txt中出现的行的最后一行。是的话返回成功完成。否则弹出有错误。给我实现这些功能的完整代码
##帮我把该日文内容翻译成简体中文，注意这些来自于ニコニコ的评论，注意语言风格要符合，如果内容是常见的英文对应的假名，翻译成中文时可以直接使用英文单词，保留其他特殊字符。直接给我翻译后的中文，每行对应原日文的一行，不要出现少行、多行的情况。你经常犯一个错误，倘若连续出现相同的翻译结果，你容易缺行，请特别小心。

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
import csv
from pathlib import Path
from collections import Counter ### NEW ###: 导入Counter用于计数

class AssTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ASS 弹幕翻译助手 (v2.1 增强版)")
        ### MODIFIED ###: 增加了窗口高度以容纳新按钮
        self.root.geometry("800x780") 

        # --- 文件路径部分 ---
        path_frame = ttk.LabelFrame(self.root, text="文件路径 (File Paths)")
        path_frame.pack(padx=10, pady=10, fill="x")

        self.jp_ass_path = tk.StringVar()
        self.jp_ch_ass_path = tk.StringVar()
        self.csv_path = tk.StringVar()
        self.already_txt_path = tk.StringVar()
        self.need_honyaku_path = tk.StringVar()
        self.honyaku_temp_path = tk.StringVar()

        self._create_path_entry(path_frame, "日文ASS (jp.ass):", self.jp_ass_path)
        self._create_path_entry(path_frame, "中文ASS (jp_ch.ass):", self.jp_ch_ass_path)
        self._create_path_entry(path_frame, "翻译数据 (hoyanku_data.csv):", self.csv_path)
        self._create_path_entry(path_frame, "已翻译索引 (already_index_temp.txt):", self.already_txt_path)
        self._create_path_entry(path_frame, "待翻译原文 (need_honyaku_temp.txt):", self.need_honyaku_path)
        self._create_path_entry(path_frame, "翻译后文本 (honyaku_temp.txt):", self.honyaku_temp_path)

        # --- 功能按钮部分 ---
        func_frame = ttk.LabelFrame(self.root, text="功能 (Functions)")
        func_frame.pack(padx=10, pady=5, fill="x")

        ### MODIFIED ###: 增加了功能7的按钮定义
        btn_texts = [
            ("1. 检查ASS格式", self.run_check_ass_format),
            ("2. 检查对应格式", self.run_check_format_consistency),
            ("3. 新建空白 jp_ch.ass", self.run_create_empty_chinese_ass),
            ("4. 扫描已有翻译", self.run_scan_existing_translations),
            ("5. 提取待翻译内容", self.run_extract_needed_translations),
            ("6. 回填翻译内容", self.run_fill_in_translations),
            ("7. 分析待翻译内容重复项", self.run_analyze_needed_translations) # 新增按钮
        ]
        
        # 按钮布局循环自动处理新按钮的排列
        for i, (text, command) in enumerate(btn_texts):
            button = ttk.Button(func_frame, text=text, command=command)
            button.grid(row=i // 2, column=i % 2, padx=5, pady=5, sticky="ew")
        
        func_frame.grid_columnconfigure(0, weight=1)
        func_frame.grid_columnconfigure(1, weight=1)

        # --- 日志输出部分 ---
        log_frame = ttk.LabelFrame(self.root, text="输出日志 (Output Log)")
        log_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.log_text = tk.Text(log_frame, wrap="word", height=20)
        self.log_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
    def _create_path_entry(self, parent, label_text, string_var):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=5, pady=2)
        label = ttk.Label(frame, text=label_text, width=25)
        label.pack(side="left")
        entry = ttk.Entry(frame, textvariable=string_var)
        entry.pack(side="left", fill="x", expand=True)
        button = ttk.Button(frame, text="浏览(Browse)", command=lambda: self._browse_file(string_var, label_text))
        button.pack(side="right", padx=5)

    def _browse_file(self, string_var, label_text):
        file_path = filedialog.askopenfilename()
        if file_path:
            string_var.set(file_path)
            if "jp.ass" in label_text:
                p = Path(file_path)
                self.jp_ch_ass_path.set(p.with_name("jp_ch.ass"))
                self.csv_path.set(p.with_name("hoyanku_data.csv"))
                self.already_txt_path.set(p.with_name("already_index_temp.txt"))
                self.need_honyaku_path.set(p.with_name("need_honyaku_temp.txt"))
                self.honyaku_temp_path.set(p.with_name("honyaku_temp.txt"))

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def _get_path(self, var, name):
        path = var.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("错误 (Error)", f"文件路径无效或文件不存在: {name}\nPath is invalid or file does not exist: {path}")
            return None
        return Path(path)

    def _get_output_path(self, var, name):
        path_str = var.get()
        if not path_str:
            messagebox.showerror("错误 (Error)", f"输出文件路径未设置: {name}\nOutput path is not set: {path_str}")
            return None
        return Path(path_str)
        
    def _get_dialogue_parts(self, line):
        line = line.strip()
        if not line.startswith("Dialogue:"):
            return None, None, None
        parts = line.split(',', 9)
        if len(parts) != 10:
            return None, None, None
        prefix = ','.join(parts[:-1])
        text_field = parts[9]
        last_brace_pos = text_field.rfind('}')
        if last_brace_pos != -1 and text_field.startswith('{'):
            style_block = text_field[:last_brace_pos + 1]
            text = text_field[last_brace_pos + 1:]
        else:
            style_block = ""
            text = text_field
        return prefix, style_block, text

    ### NEW ###
    def _clean_text_for_matching(self, text):
        """
        移除文本中的日文空格（全角）和英文空格（半角），用于匹配。
        Removes Japanese (full-width) and English (half-width) spaces from text for matching purposes.
        """
        if not isinstance(text, str):
            return ""
        # \s: 匹配任何空白字符，包括空格、制表符、换行符等 (英文半角空格)
        # \u3000: 匹配全角空格 (日文空格)
        pattern = r'[\s\u3000]'
        return re.sub(pattern, '', text)
        
    # --- 功能 1: 检查ASS格式---
    def run_check_ass_format(self):
        self.clear_log()
        self.log("--- 开始执行功能1: 检查ASS格式 ---")
        jp_ass_file = self._get_path(self.jp_ass_path, "jp.ass")
        if not jp_ass_file: return
        invalid_lines = []
        try:
            with open(jp_ass_file, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            format_line_index = -1
            for i, line in enumerate(lines):
                if line.strip().startswith("[Events]"):
                    format_line_index = i
                    break
            if format_line_index == -1:
                self.log("错误: 文件中未找到 '[Events]:' 开头的行。检查无法继续。")
                messagebox.showerror("错误", "未在文件中找到 '[Events]:' 行。")
                return
            self.log(f"找到 '[Events]:' 行在第 {format_line_index+1} 行。开始从下下行扫描...")
            for i in range(format_line_index + 2, len(lines)):
                line_num = i + 1
                line = lines[i].strip()
                if not line:
                    self.log(f"第 {line_num} 行错误: 该行为空，但应以 'Dialogue:' 开头。")
                    invalid_lines.append(line_num)
                    continue
                if not line.startswith("Dialogue:"):
                    self.log(f"第 {line_num} 行错误: 该行应以 'Dialogue:' 开头，但实际内容是: '{line}'")
                    invalid_lines.append(line_num)
                    continue
                line_errors = []
                parts = line.split(',', 9)
                if len(parts) != 10:
                    line_errors.append("逗号数量不正确 (应为9个)")
                time_format_regex = re.compile(r'^\d+:\d{2}:\d{2}\.\d{2}$')
                if len(parts) > 2:
                    if not time_format_regex.match(parts[1]):
                        line_errors.append(f"开始时间格式错误: {parts[1]}")
                    if not time_format_regex.match(parts[2]):
                        line_errors.append(f"结束时间格式错误: {parts[2]}")
                if len(parts) == 10:
                    text_field = parts[9]
                    if text_field.count('{') != text_field.count('}'):
                         line_errors.append("样式代码 {...} 的花括号数量不匹配")
                if line_errors:
                    self.log(f"第 {line_num} 行 ('Dialogue:' 开头) 内部格式错误: {'; '.join(line_errors)}")
                    invalid_lines.append(line_num)
            if not invalid_lines:
                self.log("检查完成。所有相关行格式均正确。")
                messagebox.showinfo("成功", "检查完成，所有相关行格式均正确。")
            else:
                final_invalid_lines = sorted(list(set(invalid_lines)))
                self.log(f"\n检查完成。发现 {len(final_invalid_lines)} 个格式错误的行。")
                self.log(f"错误行号: {', '.join(map(str, final_invalid_lines))}")
                messagebox.showwarning("完成", f"检查完成，发现 {len(final_invalid_lines)} 个错误行，详情请看日志。")
        except Exception as e:
            self.log(f"发生错误: {e}")
            messagebox.showerror("异常", f"处理文件时发生异常: {e}")
        self.log("--- 功能1: 执行完毕 ---\n")

    # --- 功能 2: 检查对应格式 ---
    def check_format_consistency_logic(self, silent=False):
        jp_ass_file = self._get_path(self.jp_ass_path, "jp.ass")
        jp_ch_ass_file = self._get_path(self.jp_ch_ass_path, "jp_ch.ass")
        if not jp_ass_file or not jp_ch_ass_file: return False
        try:
            with open(jp_ass_file, 'r', encoding='utf-8') as f1, \
                 open(jp_ch_ass_file, 'r', encoding='utf-8') as f2:
                for i, (line1, line2) in enumerate(zip(f1, f2)):
                    line_num = i + 1
                    if line1.strip().startswith("Dialogue:"):
                        prefix1, _, _ = self._get_dialogue_parts(line1)
                        prefix2, _, _ = self._get_dialogue_parts(line2)
                        if prefix1 is None or prefix2 is None:
                            if not silent:
                                self.log(f"第 {line_num} 行存在格式问题，无法比较。")
                            continue
                        if prefix1 != prefix2:
                            if not silent:
                                self.log(f"格式不匹配于第 {line_num} 行。")
                                self.log(f"jp.ass : {prefix1}")
                                self.log(f"jp_ch.ass: {prefix2}")
                                messagebox.showwarning("不匹配", f"在第 {line_num} 行发现格式不匹配。")
                            return False
                    elif line1.strip() != line2.strip():
                         if not silent:
                                self.log(f"第 {line_num} 行不匹配 (非Dialogue行).")
                                messagebox.showwarning("不匹配", f"第 {line_num} 行不匹配 (非Dialogue行).")
                         return False
            if not silent:
                self.log("所有对应行格式均一致。")
                messagebox.showinfo("成功", "所有对应行格式均一致。")
            return True
        except Exception as e:
            if not silent:
                self.log(f"发生错误: {e}")
                messagebox.showerror("异常", f"处理文件时发生异常: {e}")
            return False

    def run_check_format_consistency(self):
        self.clear_log()
        self.log("--- 开始执行功能2: 检查对应格式 ---")
        self.check_format_consistency_logic()
        self.log("--- 功能2: 执行完毕 ---\n")
        
    # --- 功能 3: 新建空白 jp_ch.ass ---
    def run_create_empty_chinese_ass(self):
        self.clear_log()
        self.log("--- 开始执行功能3: 新建空白 jp_ch.ass ---")
        jp_ass_file = self._get_path(self.jp_ass_path, "jp.ass")
        if not jp_ass_file: return
        jp_ch_ass_file = self._get_output_path(self.jp_ch_ass_path, "jp_ch.ass")
        if not jp_ch_ass_file: return
        try:
            with open(jp_ass_file, 'r', encoding='utf-8') as f_in, \
                 open(jp_ch_ass_file, 'w', encoding='utf-8') as f_out:
                for line in f_in:
                    if line.strip().startswith("Dialogue:"):
                        prefix, style, _ = self._get_dialogue_parts(line)
                        if prefix is not None:
                            f_out.write(f"{prefix},{style}\n")
                        else:
                            self.log(f"警告: Dialogue行格式不标准，已按原样复制: {line.strip()}")
                            f_out.write(line)
                    else:
                        f_out.write(line)
            self.log(f"成功创建文件: {jp_ch_ass_file}")
            messagebox.showinfo("成功", f"成功创建文件:\n{jp_ch_ass_file}")
        except Exception as e:
            self.log(f"发生错误: {e}")
            messagebox.showerror("异常", f"处理文件时发生异常: {e}")
        self.log("--- 功能3: 执行完毕 ---\n")

    ### MODIFIED ###
    # --- 功能 4: 扫描已有翻译 (已修正和优化) ---
    def run_scan_existing_translations(self):
        self.clear_log()
        self.log("--- 开始执行功能4: 扫描已有翻译 (忽略日文/英文/空格) ---")
        
        self.log("步骤1: 运行格式对应检查...")
        if not self.check_format_consistency_logic(silent=True):
            self.log("错误: 'jp.ass' 与 'jp_ch.ass' 格式不匹配，无法继续。")
            messagebox.showerror("错误", "格式不匹配，操作中止。")
            return
        self.log("格式对应检查通过。")
        
        jp_ass_file = self._get_path(self.jp_ass_path, "jp.ass")
        jp_ch_ass_file = self._get_path(self.jp_ch_ass_path, "jp_ch.ass")
        csv_file = self._get_path(self.csv_path, "hoyanku_data.csv")
        already_txt_file = self._get_output_path(self.already_txt_path, "already_index_temp.txt")
        if not all([jp_ass_file, jp_ch_ass_file, csv_file, already_txt_file]): return

        try:
            self.log("步骤2: 读取翻译数据库并创建清理后的匹配字典...")
            trans_dict = {}
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        original_jp = row[0]
                        translation = row[1]
                        # 使用清理后的日文作为key
                        cleaned_key = self._clean_text_for_matching(original_jp)
                        if cleaned_key in trans_dict:
                            self.log(f"警告: 清理后的键 '{cleaned_key}' 发生冲突。来自原文 '{original_jp}' 的翻译将覆盖旧值。")
                        trans_dict[cleaned_key] = translation
            self.log(f"成功加载 {len(trans_dict)} 条翻译记录 (基于清理后的键)。")

            with open(jp_ass_file, 'r', encoding='utf-8') as f:
                jp_lines = f.readlines()
            ch_lines = list(jp_lines) # 创建一个可修改的副本

            found_indices = []
            updated_count = 0
            
            self.log("步骤3: 扫描并替换翻译...")
            for i, jp_line in enumerate(jp_lines):
                line_num = i + 1
                prefix, style, text = self._get_dialogue_parts(jp_line)
                if prefix is not None:
                    # 对当前行的文本进行同样的清理以进行匹配
                    cleaned_text = self._clean_text_for_matching(text)
                    if cleaned_text in trans_dict:
                        translation = trans_dict[cleaned_text]
                        ch_lines[i] = f"{prefix},{style}{translation}\n"
                        found_indices.append(str(line_num))
                        updated_count += 1
            
            self.log(f"扫描完成，共找到并更新 {updated_count} 行。")

            self.log(f"步骤4: 将更新后的内容写回 '{jp_ch_ass_file.name}'...")
            with open(jp_ch_ass_file, 'w', encoding='utf-8') as f:
                f.writelines(ch_lines)
            
            self.log(f"步骤5: 将已翻译的行号保存到 '{already_txt_file.name}'...")
            with open(already_txt_file, 'w', encoding='utf-8') as f:
                f.write(','.join(found_indices))

            messagebox.showinfo("成功", f"操作完成！\n- {updated_count} 行被更新到 {jp_ch_ass_file.name}\n- {len(found_indices)} 个行号被保存到 {already_txt_file.name}")

        except Exception as e:
            self.log(f"发生错误: {e}")
            messagebox.showerror("异常", f"处理文件时发生异常: {e}")
        self.log("--- 功能4: 执行完毕 ---\n")
        
    # --- 功能 5: 提取待翻译内容 (此功能无需修改) ---
    def run_extract_needed_translations(self):
        self.clear_log()
        self.log("--- 开始执行功能5: 提取待翻译内容 ---")
        jp_ass_file = self._get_path(self.jp_ass_path, "jp.ass")
        already_txt_file = self._get_path(self.already_txt_path, "already_index_temp.txt")
        need_honyaku_file = self._get_output_path(self.need_honyaku_path, "need_honyaku_temp.txt")
        if not all([jp_ass_file, already_txt_file, need_honyaku_file]): return

        try:
            with open(already_txt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    already_indices = set(content.split(','))
                else:
                    already_indices = set()
            self.log(f"读取到 {len(already_indices)} 个已翻译行号。")

            needed_strings = []
            with open(jp_ass_file, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    line_num = str(i + 1)
                    if line_num not in already_indices:
                        _, _, text = self._get_dialogue_parts(line)
                        if text is not None:
                            needed_strings.append(text)
            
            self.log(f"提取到 {len(needed_strings)} 条需要翻译的纯文本。")
            with open(need_honyaku_file, 'w', encoding='utf-8') as f:
                for s in needed_strings:
                    f.write(s + '\n')
            
            self.log(f"成功将待翻译内容保存到: {need_honyaku_file}")
            messagebox.showinfo("成功", f"成功提取 {len(needed_strings)} 条待翻译内容到\n{need_honyaku_file.name}")

        except Exception as e:
            self.log(f"发生错误: {e}")
            messagebox.showerror("异常", f"处理文件时发生异常: {e}")
        self.log("--- 功能5: 执行完毕 ---\n")
        
    # --- 功能 6: 回填翻译内容 ---
    def run_fill_in_translations(self):
        self.clear_log()
        self.log("--- 开始执行功能6: 回填翻译内容 ---")
        jp_ch_ass_file = self._get_path(self.jp_ch_ass_path, "jp_ch.ass")
        honyaku_temp_file = self._get_path(self.honyaku_temp_path, "honyaku_temp.txt")
        already_txt_file = self._get_path(self.already_txt_path, "already_index_temp.txt")
        if not all([jp_ch_ass_file, honyaku_temp_file, already_txt_file]): return
        try:
            with open(already_txt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    already_indices = set(int(x) for x in content.split(','))
                else:
                    already_indices = set()
            self.log(f"读取到 {len(already_indices)} 个已翻译行号。")
            with open(honyaku_temp_file, 'r', encoding='utf-8') as f:
                translated_lines = [line.strip() for line in f.readlines()]
            self.log(f"从 '{honyaku_temp_file.name}' 读取到 {len(translated_lines)} 行翻译。")
            with open(jp_ch_ass_file, 'r', encoding='utf-8') as f:
                ch_lines = f.readlines()
            lines_to_update_indices = []
            for i, line in enumerate(ch_lines):
                line_num = i + 1
                if line.strip().startswith("Dialogue:") and line_num not in already_indices:
                    lines_to_update_indices.append(i)
            self.log(f"在 '{jp_ch_ass_file.name}' 中找到 {len(lines_to_update_indices)} 行需要回填。")
            if len(translated_lines) != len(lines_to_update_indices):
                msg = f"翻译文本数量 ({len(translated_lines)}) 与需要回填的行数 ({len(lines_to_update_indices)}) 不匹配!"
                self.log(f"错误: {msg}")
                messagebox.showerror("数量不匹配", msg)
                return
            for i, line_index in enumerate(lines_to_update_indices):
                translation = translated_lines[i]
                prefix, style, _ = self._get_dialogue_parts(ch_lines[line_index])
                if prefix is not None:
                    ch_lines[line_index] = f"{prefix},{style}{translation}\n"
            self.log("回填处理完成，正在写入文件...")
            with open(jp_ch_ass_file, 'w', encoding='utf-8') as f:
                f.writelines(ch_lines)
            self.log("最终检查通过。")
            self.log(f"成功将 {len(translated_lines)} 行翻译回填到 '{jp_ch_ass_file.name}'。")
            messagebox.showinfo("成功", f"成功完成！\n{len(translated_lines)} 行翻译已回填。")
        except Exception as e:
            self.log(f"发生错误: {e}")
            messagebox.showerror("异常", f"处理文件时发生异常: {e}")
        self.log("--- 功能6: 执行完毕 ---\n")
    
    ### NEW ###
    # --- 功能 7: 分析待翻译内容重复项 ---
    def run_analyze_needed_translations(self):
        self.clear_log()
        self.log("--- 开始执行功能7: 分析待翻译内容重复项 ---")
        need_honyaku_file = self._get_path(self.need_honyaku_path, "need_honyaku_temp.txt")
        if not need_honyaku_file: return

        try:
            with open(need_honyaku_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            self.log(f"从 '{need_honyaku_file.name}' 读取 {len(lines)} 行待翻译内容。")
            self.log("开始清理并统计内容...")

            cleaned_lines = [self._clean_text_for_matching(line.strip()) for line in lines]
            
            # 使用Counter进行计数
            counter = Counter(cleaned_lines)
            
            # 获取最常见的前100个
            most_common_items = counter.most_common(100)
            
            self.log("\n--- 分析结果：出现频率最高的前100项 (已忽略日/英/空格) ---")
            if not most_common_items:
                self.log("没有找到任何内容或所有内容清理后均为空。")
            else:
                self.log("名次 | 出现次数 | 清理后的内容")
                self.log("---- | -------- | -----------")
                for i, (item, count) in enumerate(most_common_items):
                    # 对于完全是日文/英文/空格的行，清理后会变为空字符串
                    display_item = item if item else "[空]"
                    self.log(f"{i+1:<4} | {count:<8} | {display_item}")

            messagebox.showinfo("分析完成", f"分析完成！共统计 {len(counter)} 种不同内容。\n详情请查看日志。")

        except Exception as e:
            self.log(f"发生错误: {e}")
            messagebox.showerror("异常", f"处理文件时发生异常: {e}")
        self.log("--- 功能7: 执行完毕 ---\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = AssTranslatorApp(root)
    root.mainloop()