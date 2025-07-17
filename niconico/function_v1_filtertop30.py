# -*- coding: utf-8 -*-
# 新增“热门翻译过滤”功能
# 在界面上添加了一个新的 "翻译过滤" 设置区域。
# 您可以启用/禁用此功能，并自定义热门排名N的值（默认为30）。
# 新增核心分析模块 _get_top_n_comments
# 这是一个新的后台辅助函数，它会预处理 jp.ass 文件。
# 通过模拟弹幕随时间播放的过程，它能找出在整个视频中，任何时刻曾经进入过出现次数排行榜前N名的所有弹幕。
# 该函数返回一个包含这些“热门弹幕”文本的集合，为后续的过滤步骤提供依据。
# 智能化改造翻译流程 (功能 4, 5, 6)
# 功能4 (扫描已有翻译)：现在会优先使用 _get_top_n_comments 的分析结果。只有当一条弹幕既存在于您的翻译数据库（CSV文件）中，又属于“热门弹幕”时，程序才会将其翻译写入 jp_ch_f.ass 文件。
# 功能5 (提取待翻译内容)：在提取需要送去翻译的文本时，会进行双重检查。一条弹幕必须同时满足“之前未被翻译过”和“属于热门弹幕”两个条件，才会被提取出来。这能确保您只专注于翻译最重要的内容。
# 功能6 (回填翻译内容)：对该功能进行了最关键的重构。它现在能精确识别出那些根据过滤规则本应被提取和翻译的行，从而确保 honyaku_temp.text 中的新翻译能够准确无误地回填到 jp_ch_f.ass 中对应的位置，避免了错位问题。
# 总而言之，这次更新将一个数据可视化的概念创造性地应用到了字幕处理流程中，使您的翻译工作能够自动聚焦于高价值、高频率的弹幕内容，有效过滤掉大量“杂音”，从而显著提升翻译的效率和性价比。
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
import csv
from pathlib import Path
from collections import Counter
import random

class AssTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ASS 弹幕翻译助手 (v3.1 过滤预处理版)")
        self.root.geometry("800x870") 

        # --- 文件路径部分 ---
        path_frame = ttk.LabelFrame(self.root, text="文件路径 (File Paths)")
        path_frame.pack(padx=10, pady=10, fill="x")

        self.jp_ass_path = tk.StringVar()
        self.jp_ch_ass_path = tk.StringVar()
        self.csv_path = tk.StringVar()
        self.filter_txt_path = tk.StringVar()
        self.already_txt_path = tk.StringVar()
        self.need_honyaku_path = tk.StringVar()
        self.honyaku_temp_path = tk.StringVar()

        self._create_path_entry(path_frame, "日文ASS (jp.ass):", self.jp_ass_path)
        self._create_path_entry(path_frame, "中文ASS (jp_ch_f.ass):", self.jp_ch_ass_path)
        self._create_path_entry(path_frame, "翻译数据 (hoyanku_data_f.csv):", self.csv_path)
        self._create_path_entry(path_frame, "热门过滤文件 (filter.txt):", self.filter_txt_path)
        self._create_path_entry(path_frame, "已翻译索引 (already_index_temp_f.txt):", self.already_txt_path)
        self._create_path_entry(path_frame, "待翻译原文 (need_honyaku_temp_f.txt):", self.need_honyaku_path)
        self._create_path_entry(path_frame, "翻译后文本 (honyaku_temp_f.txt):", self.honyaku_temp_path)

        # --- 翻译过滤设置 ---
        filter_frame = ttk.LabelFrame(self.root, text="翻译过滤 (Translation Filter)")
        filter_frame.pack(padx=10, pady=5, fill="x")

        self.filter_enabled = tk.BooleanVar(value=True)
        self.top_n_value = tk.IntVar(value=30)

        ttk.Checkbutton(filter_frame, text="启用热门过滤", variable=self.filter_enabled).pack(side="left", padx=(5,2))
        ttk.Label(filter_frame, text="(后续功能将依赖 filter.txt, 请先执行功能0)").pack(side="left", padx=(10,0))
        ttk.Entry(filter_frame, textvariable=self.top_n_value, width=4).pack(side="right", padx=5)
        ttk.Label(filter_frame, text="热门排名 N =").pack(side="right")

        # --- 功能按钮部分 ---
        func_frame = ttk.LabelFrame(self.root, text="功能 (Functions)")
        func_frame.pack(padx=10, pady=5, fill="x")
        
        btn_texts = [
            ("0. 生成过滤文件", self.run_generate_filter_file),
            ("1. 检查ASS格式", self.run_check_ass_format),
            ("2. 检查对应格式", self.run_check_format_consistency),
            ("3. 新建空白 jp_ch_f.ass", self.run_create_empty_chinese_ass),
            ("4. 扫描已有翻译", self.run_scan_existing_translations),
            ("5. 提取待翻译内容", self.run_extract_needed_translations),
            ("6. 回填翻译内容", self.run_fill_in_translations),
            ("7. 分析待翻译内容重复项", self.run_analyze_needed_translations)
        ]
        
        for i, (text, command) in enumerate(btn_texts):
            button = ttk.Button(func_frame, text=text, command=command)
            button.grid(row=(i // 2), column=(i % 2), padx=5, pady=5, sticky="ew")
        
        func_frame.grid_columnconfigure(0, weight=1)
        func_frame.grid_columnconfigure(1, weight=1)

        # --- 高级功能部分 ---
        adv_func_frame = ttk.LabelFrame(self.root, text="高级功能 (Advanced Functions)")
        adv_func_frame.pack(padx=10, pady=10, fill="x")

        merge_frame = ttk.Frame(adv_func_frame)
        merge_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(merge_frame, text="8. 合并为双语字幕 (Merge to Bilingual)", command=self.run_merge_to_bilingual).pack(fill="x")

        compress_frame = ttk.Frame(adv_func_frame)
        compress_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(compress_frame, text="时间缩放值 (Value):").pack(side="left", padx=5)
        self.time_scale_value = tk.StringVar(value="1.0")
        ttk.Entry(compress_frame, textvariable=self.time_scale_value, width=10).pack(side="left", padx=5)
        ttk.Button(compress_frame, text="9. 压缩/拉伸时间轴 (Compress/Stretch Timeline)", command=self.run_compress_timeline).pack(side="left", fill="x", expand=True, padx=5)

        reconstruct_frame = ttk.LabelFrame(adv_func_frame, text="10. 重构高级弹幕 (Reconstruct Advanced Danmaku)")
        reconstruct_frame.pack(fill="x", padx=5, pady=5)
        
        params_grid = ttk.Frame(reconstruct_frame)
        params_grid.pack(fill="x", pady=5)

        self.reconstruct_params = {
            "threshold": tk.IntVar(value=5),
            "move_duration": tk.DoubleVar(value=0.5),
            "base_font_size": tk.IntVar(value=25)
        }

        ttk.Label(params_grid, text="热门阈值 (Threshold):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(params_grid, textvariable=self.reconstruct_params["threshold"], width=8).grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(params_grid, text="移动时长(秒) (Move Duration):").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        ttk.Entry(params_grid, textvariable=self.reconstruct_params["move_duration"], width=8).grid(row=0, column=3, padx=5, pady=2)
        ttk.Label(params_grid, text="固定弹幕字号 (Base Font Size):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Entry(params_grid, textvariable=self.reconstruct_params["base_font_size"], width=8).grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(reconstruct_frame, text="执行重构 (Run Reconstruction)", command=self.run_reconstruct_danmaku).pack(fill="x", padx=5, pady=5)

        # --- 日志输出部分 ---
        log_frame = ttk.LabelFrame(self.root, text="输出日志 (Output Log)")
        log_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.log_text = tk.Text(log_frame, wrap="word", height=15)
        self.log_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
    def _create_path_entry(self, parent, label_text, string_var):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=5, pady=2)
        label = ttk.Label(frame, text=label_text, width=32)
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
                self.jp_ch_ass_path.set(p.with_name("jp_ch_f.ass"))
                self.csv_path.set(p.with_name("hoyanku_data_f.csv"))
                self.filter_txt_path.set(p.with_name("filter.txt"))
                self.already_txt_path.set(p.with_name("already_index_temp_f.txt"))
                self.need_honyaku_path.set(p.with_name("need_honyaku_temp_f.txt"))
                self.honyaku_temp_path.set(p.with_name("honyaku_temp_f.txt"))

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def _get_path(self, var, name, check_exists=True):
        path = var.get()
        if not path:
            messagebox.showerror("错误 (Error)", f"路径未设置: {name}")
            return None
        if check_exists and not os.path.exists(path):
            messagebox.showerror("错误 (Error)", f"文件不存在: {name}\n路径: {path}")
            return None
        return Path(path)
        
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
    
    def _hms_to_seconds(self, time_str):
        try:
            h, m, s = time_str.split(':')
            return int(h) * 3600 + int(m) * 60 + float(s)
        except Exception:
            self.log(f"警告: 无法解析时间戳 '{time_str}'，返回0。")
            return 0.0

    def _seconds_to_hms(self, seconds):
        if seconds < 0: seconds = 0
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    def _clean_text_for_matching(self, text):
        if not isinstance(text, str):
            return ""
        pattern = r'[\s\u3000]'
        return re.sub(pattern, '', text)

    def _get_top_n_comments_texts(self, ass_file_path, n):
        self.log(f"--- (后台) 开始分析 Top {n} 热门评论文本 ---")
        try:
            with open(ass_file_path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            dialogue_events = []
            for line in lines:
                if line.strip().startswith("Dialogue:"):
                    prefix, _, text = self._get_dialogue_parts(line)
                    text = text.strip()
                    if text and prefix:
                        try:
                            start_time_str = prefix.split(',')[1]
                            start_time = self._hms_to_seconds(start_time_str)
                            dialogue_events.append({'time': start_time, 'text': text})
                        except (IndexError, ValueError):
                            continue
            dialogue_events.sort(key=lambda x: x['time'])
            if not dialogue_events:
                self.log("未找到有效的Dialogue事件进行分析。")
                return set()
            top_n_texts_cleaned = set()
            counts = Counter()
            for event in dialogue_events:
                cleaned_text = self._clean_text_for_matching(event['text'])
                if not cleaned_text: continue
                counts[cleaned_text] += 1
                current_top_n = {item[0] for item in counts.most_common(n)}
                top_n_texts_cleaned.update(current_top_n)
            self.log(f"分析完成。共找到 {len(top_n_texts_cleaned)} 个曾经进入 Top {n} 的不重复评论(已清理)。")
            return top_n_texts_cleaned
        except Exception as e:
            self.log(f"分析Top {n}评论时发生严重错误: {e}")
            messagebox.showerror("错误", f"分析Top {n}评论时发生错误: {e}")
            return set()
    
    def run_generate_filter_file(self):
        self.clear_log()
        self.log("--- 开始执行功能0: 生成热门弹幕过滤文件 ---")
        jp_ass_file = self._get_path(self.jp_ass_path, "jp.ass")
        if not jp_ass_file: return
        
        filter_file = self._get_path(self.filter_txt_path, "filter.txt", check_exists=False)
        if not filter_file: return

        try:
            n_value = self.top_n_value.get()
            if n_value <= 0:
                messagebox.showerror("错误", "热门评论排名N必须是正整数。")
                return
        except tk.TclError:
            messagebox.showerror("错误", "请输入有效的排名数字N。")
            return
            
        top_texts_set = self._get_top_n_comments_texts(jp_ass_file, n_value)
        if not top_texts_set:
            self.log("未能分析出热门评论，无法生成过滤文件。")
            return
            
        self.log("正在扫描文件以匹配热门评论的行号...")
        filtered_line_numbers = []
        with open(jp_ass_file, 'r', encoding='utf-8-sig') as f:
            for i, line in enumerate(f):
                if line.strip().startswith("Dialogue:"):
                    _, _, text = self._get_dialogue_parts(line)
                    if text is not None:
                        cleaned_text = self._clean_text_for_matching(text)
                        if cleaned_text in top_texts_set:
                            filtered_line_numbers.append(str(i + 1))
        
        try:
            with open(filter_file, 'w', encoding='utf-8') as f:
                f.write(','.join(filtered_line_numbers))
            self.log(f"成功生成过滤文件，共包含 {len(filtered_line_numbers)} 个热门弹幕行号。")
            self.log(f"文件已保存至: {filter_file}")
            messagebox.showinfo("成功", f"过滤文件已成功生成！\n包含 {len(filtered_line_numbers)} 行。")
        except Exception as e:
            self.log(f"保存过滤文件时出错: {e}")
            messagebox.showerror("保存失败", f"无法写入过滤文件:\n{e}")
        
        self.log("--- 功能0: 执行完毕 ---\n")

    def _read_filter_file(self):
        filter_file = self._get_path(self.filter_txt_path, "filter.txt")
        if not filter_file:
            return None
        try:
            with open(filter_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            if not content:
                self.log("警告: filter.txt 为空, 将处理所有行。")
                return set()
            return set(content.split(','))
        except Exception as e:
            self.log(f"读取filter.txt时出错: {e}")
            messagebox.showerror("读取错误", f"无法读取过滤文件: {e}")
            return None

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
                if line.strip() == "[Events]":
                    format_line_index = i
                    break
            if format_line_index == -1:
                self.log("错误: 文件中未找到 '[Events]' 开头的行。检查无法继续。")
                messagebox.showerror("错误", "未在文件中找到 '[Events]' 行。")
                return
            
            dialogue_start_index = -1
            for i in range(format_line_index + 1, len(lines)):
                if lines[i].strip().lower().startswith("format:"):
                     dialogue_start_index = i + 1
                     break
            if dialogue_start_index == -1:
                 self.log("警告: 未找到 'Format:' 行, 将从 '[Events]' 下一行开始检查。")
                 dialogue_start_index = format_line_index + 1

            for i in range(dialogue_start_index, len(lines)):
                line_num = i + 1
                line = lines[i].strip()
                if not line or line.startswith(';'): continue
                if not line.startswith("Dialogue:"):
                    self.log(f"第 {line_num} 行内容异常: 该行应以 'Dialogue:' 开头 (如果不是注释或样式行)。内容: '{line}'")
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

    def check_format_consistency_logic(self, silent=False):
        jp_ass_file = self._get_path(self.jp_ass_path, "jp.ass")
        jp_ch_ass_file = self._get_path(self.jp_ch_ass_path, "jp_ch_f.ass")
        if not jp_ass_file or not jp_ch_ass_file: return False
        try:
            with open(jp_ass_file, 'r', encoding='utf-8-sig') as f1: lines1 = f1.readlines()
            with open(jp_ch_ass_file, 'r', encoding='utf-8') as f2: lines2 = f2.readlines()
            
            if len(lines1) != len(lines2):
                if not silent:
                    self.log(f"文件行数不匹配: jp.ass ({len(lines1)}行) vs jp_ch_f.ass ({len(lines2)}行)")
                    messagebox.showerror("行数不匹配", "两个文件的总行数不一致，无法比较。")
                return False

            for i, (line1, line2) in enumerate(zip(lines1, lines2)):
                line_num = i + 1
                if line1.strip().startswith("Dialogue:"):
                    if not line2.strip().startswith("Dialogue:"):
                        if not silent:
                            self.log(f"第 {line_num} 行类型不匹配: jp.ass是Dialogue行，但jp_ch_f.ass不是。")
                            messagebox.showwarning("不匹配", f"在第 {line_num} 行发现类型不匹配。")
                        return False

                    prefix1, _, _ = self._get_dialogue_parts(line1)
                    prefix2, _, _ = self._get_dialogue_parts(line2)
                    
                    if prefix1 is None or prefix2 is None:
                        if not silent: self.log(f"第 {line_num} 行存在格式问题，无法比较。")
                        continue
                    
                    if prefix1 != prefix2:
                        if not silent:
                            self.log(f"格式不匹配于第 {line_num} 行。")
                            self.log(f"jp.ass : {prefix1}")
                            self.log(f"jp_ch_f.ass: {prefix2}")
                            messagebox.showwarning("不匹配", f"在第 {line_num} 行发现格式不匹配。")
                        return False
                elif line1.strip() != line2.strip():
                     if not silent:
                            self.log(f"第 {line_num} 行不匹配 (非Dialogue行).")
                            self.log(f"jp.ass : {line1.strip()}")
                            self.log(f"jp_ch_f.ass: {line2.strip()}")
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
        
    def run_create_empty_chinese_ass(self):
        self.clear_log()
        self.log("--- 开始执行功能3: 新建空白 jp_ch_f.ass ---")
        jp_ass_file = self._get_path(self.jp_ass_path, "jp.ass")
        if not jp_ass_file: return
        jp_ch_ass_file = self._get_path(self.jp_ch_ass_path, "jp_ch_f.ass", check_exists=False)
        if not jp_ch_ass_file: return
        try:
            with open(jp_ass_file, 'r', encoding='utf-8-sig') as f_in, \
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

    def run_scan_existing_translations(self):
        self.clear_log()
        self.log("--- 开始执行功能4: 扫描已有翻译 ---")
        if not self.check_format_consistency_logic(silent=True):
            self.log("错误: 'jp.ass' 与 'jp_ch_f.ass' 格式或行数不匹配，无法继续。")
            messagebox.showerror("错误", "格式不匹配，操作中止。")
            return
        
        jp_ass_file = self._get_path(self.jp_ass_path, "jp.ass")
        jp_ch_ass_file = self._get_path(self.jp_ch_ass_path, "jp_ch_f.ass")
        csv_file = self._get_path(self.csv_path, "hoyanku_data_f.csv")
        already_txt_file = self._get_path(self.already_txt_path, "already_index_temp_f.txt", check_exists=False)
        if not all([jp_ass_file, jp_ch_ass_file, csv_file, already_txt_file]): return

        allowed_line_numbers = None
        if self.filter_enabled.get():
            self.log("热门过滤已启用，正在读取 filter.txt...")
            allowed_line_numbers = self._read_filter_file()
            if allowed_line_numbers is None: return

        try:
            trans_dict = {}
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        cleaned_key = self._clean_text_for_matching(row[0])
                        if cleaned_key and cleaned_key not in trans_dict:
                            trans_dict[cleaned_key] = row[1]
            self.log(f"成功加载 {len(trans_dict)} 条有效翻译记录。")

            with open(jp_ass_file, 'r', encoding='utf-8-sig') as f: jp_lines = f.readlines()
            with open(jp_ch_ass_file, 'r', encoding='utf-8') as f: ch_lines = f.readlines()

            found_indices = []
            updated_count = 0
            
            self.log("扫描并替换翻译...")
            for i, jp_line in enumerate(jp_lines):
                line_num_str = str(i + 1)
                
                is_translatable = not self.filter_enabled.get() or allowed_line_numbers is None or line_num_str in allowed_line_numbers

                if is_translatable:
                    prefix, style, text = self._get_dialogue_parts(jp_line)
                    if prefix:
                        cleaned_text = self._clean_text_for_matching(text)
                        if cleaned_text in trans_dict:
                            translation = trans_dict[cleaned_text]
                            ch_lines[i] = f"{prefix},{style}{translation}\n"
                            found_indices.append(line_num_str)
                            updated_count += 1
            
            self.log(f"扫描完成，共找到并更新 {updated_count} 行。")
            with open(jp_ch_ass_file, 'w', encoding='utf-8') as f: f.writelines(ch_lines)
            with open(already_txt_file, 'w', encoding='utf-8') as f: f.write(','.join(found_indices))
            messagebox.showinfo("成功", f"操作完成！\n- {updated_count} 行被更新到 {jp_ch_ass_file.name}\n- {len(found_indices)} 个行号被保存到 {already_txt_file.name}")

        except Exception as e:
            self.log(f"发生错误: {e}")
            messagebox.showerror("异常", f"处理文件时发生异常: {e}")
        self.log("--- 功能4: 执行完毕 ---\n")
        
    def run_extract_needed_translations(self):
        self.clear_log()
        self.log("--- 开始执行功能5: 提取待翻译内容 ---")
        jp_ass_file = self._get_path(self.jp_ass_path, "jp.ass")
        already_txt_file = self._get_path(self.already_txt_path, "already_index_temp_f.txt")
        need_honyaku_file = self._get_path(self.need_honyaku_path, "need_honyaku_temp_f.txt", check_exists=False)
        if not all([jp_ass_file, already_txt_file, need_honyaku_file]): return

        allowed_line_numbers = None
        if self.filter_enabled.get():
            self.log("热门过滤已启用，正在读取 filter.txt...")
            allowed_line_numbers = self._read_filter_file()
            if allowed_line_numbers is None: return

        try:
            if os.path.exists(already_txt_file):
                with open(already_txt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    already_indices = set(content.split(',')) if content else set()
            else:
                already_indices = set()
            self.log(f"读取到 {len(already_indices)} 个已翻译行号。")

            needed_strings = []
            with open(jp_ass_file, 'r', encoding='utf-8-sig') as f:
                for i, line in enumerate(f):
                    line_num_str = str(i + 1)
                    
                    if line_num_str not in already_indices:
                        is_translatable = not self.filter_enabled.get() or allowed_line_numbers is None or line_num_str in allowed_line_numbers
                        if is_translatable:
                            _, _, text = self._get_dialogue_parts(line)
                            if text is not None:
                                needed_strings.append(text)
            
            self.log(f"提取到 {len(needed_strings)} 条需要翻译的纯文本。")
            with open(need_honyaku_file, 'w', encoding='utf-8') as f:
                for s in needed_strings: f.write(s + '\n')
            self.log(f"成功将待翻译内容保存到: {need_honyaku_file}")
            messagebox.showinfo("成功", f"成功提取 {len(needed_strings)} 条待翻译内容到\n{need_honyaku_file.name}")

        except Exception as e:
            self.log(f"发生错误: {e}")
            messagebox.showerror("异常", f"处理文件时发生异常: {e}")
        self.log("--- 功能5: 执行完毕 ---\n")
        
    def run_fill_in_translations(self):
        self.clear_log()
        self.log("--- 开始执行功能6: 回填翻译内容 ---")
        jp_ch_ass_file = self._get_path(self.jp_ch_ass_path, "jp_ch_f.ass")
        honyaku_temp_file = self._get_path(self.honyaku_temp_path, "honyaku_temp_f.txt")
        already_txt_file = self._get_path(self.already_txt_path, "already_index_temp_f.txt")
        if not all([jp_ch_ass_file, honyaku_temp_file, already_txt_file]): return

        allowed_line_numbers = None
        if self.filter_enabled.get():
            self.log("热门过滤已启用，正在读取 filter.txt...")
            allowed_line_numbers = self._read_filter_file()
            if allowed_line_numbers is None: return

        try:
            if os.path.exists(already_txt_file):
                with open(already_txt_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    already_indices = set(content.split(',')) if content else set()
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
                line_num_str = str(i + 1)
                
                if line.strip().startswith("Dialogue:") and line_num_str not in already_indices:
                    is_translatable = not self.filter_enabled.get() or allowed_line_numbers is None or line_num_str in allowed_line_numbers
                    if is_translatable:
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
            
            with open(jp_ch_ass_file, 'w', encoding='utf-8') as f: f.writelines(ch_lines)
            self.log("最终检查通过。")
            self.log(f"成功将 {len(translated_lines)} 行翻译回填到 '{jp_ch_ass_file.name}'。")
            messagebox.showinfo("成功", f"成功完成！\n{len(translated_lines)} 行翻译已回填。")
        except Exception as e:
            self.log(f"发生错误: {e}")
            messagebox.showerror("异常", f"处理文件时发生异常: {e}")
        self.log("--- 功能6: 执行完毕 ---\n")

    def run_analyze_needed_translations(self):
        self.clear_log()
        self.log("--- 开始执行功能7: 分析待翻译内容重复项 ---")
        need_honyaku_file = self._get_path(self.need_honyaku_path, "need_honyaku_temp_f.txt")
        if not need_honyaku_file: return
        try:
            with open(need_honyaku_file, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines()]
            self.log(f"从 '{need_honyaku_file.name}' 读取 {len(lines)} 行待翻译内容。")
            self.log("开始清理并统计内容...")
            cleaned_lines = [self._clean_text_for_matching(line) for line in lines]
            counter = Counter(cleaned_lines)
            most_common_items = counter.most_common(100)
            self.log("\n--- 分析结果：出现频率最高的前100项 (已忽略空格) ---")
            if not most_common_items:
                self.log("没有找到任何内容或所有内容清理后均为空。")
            else:
                self.log("名次 | 出现次数 | 清理后的内容")
                self.log("---- | -------- | -----------")
                for i, (item, count) in enumerate(most_common_items):
                    display_item = item if item else "[空]"
                    self.log(f"{i+1:<4} | {count:<8} | {display_item}")
            messagebox.showinfo("分析完成", f"分析完成！共统计 {len(counter)} 种不同内容。\n详情请查看日志。")
        except Exception as e:
            self.log(f"发生错误: {e}")
            messagebox.showerror("异常", f"处理文件时发生异常: {e}")
        self.log("--- 功能7: 执行完毕 ---\n")

    def run_merge_to_bilingual(self):
        self.clear_log()
        self.log("--- 开始执行功能8: 合并为双语字幕 ---")
        jp_ass_file = self._get_path(self.jp_ass_path, "jp.ass")
        jp_ch_ass_file = self._get_path(self.jp_ch_ass_path, "jp_ch_f.ass")
        if not jp_ass_file or not jp_ch_ass_file: return
        output_path = jp_ass_file.with_name("doublesub.ass")
        try:
            with open(jp_ass_file, 'r', encoding='utf-8') as f_jp, \
                 open(jp_ch_ass_file, 'r', encoding='utf-8') as f_ch:
                jp_lines = f_jp.readlines()
                ch_lines = f_ch.readlines()
            if len(jp_lines) != len(ch_lines):
                self.log("错误: jp.ass 和 jp_ch_f.ass 文件行数不一致，无法合并。")
                messagebox.showerror("错误", "文件行数不一致!")
                return
            new_lines = []
            for i, jp_line in enumerate(jp_lines):
                if jp_line.strip().startswith("Dialogue:"):
                    prefix, style, jp_text = self._get_dialogue_parts(jp_line)
                    _, _, ch_text = self._get_dialogue_parts(ch_lines[i])
                    if prefix is None or ch_text is None:
                        new_lines.append(jp_line)
                        continue
                    merged_text = f"{ch_text.strip()} | {jp_text.strip()}"
                    new_line = f"{prefix},{style}{merged_text}\n"
                    new_lines.append(new_line)
                else:
                    new_lines.append(jp_line)
            with open(output_path, 'w', encoding='utf-8') as f_out:
                f_out.writelines(new_lines)
            self.log(f"双语字幕文件已成功生成: {output_path}")
            messagebox.showinfo("成功", f"文件已保存至:\n{output_path}")
        except Exception as e:
            self.log(f"发生错误: {e}")
            messagebox.showerror("异常", f"处理文件时发生异常: {e}")
        self.log("--- 功能8: 执行完毕 ---\n")

    def run_compress_timeline(self):
        self.clear_log()
        self.log("--- 开始执行功能9: 压缩/拉伸时间轴 ---")
        jp_ch_ass_file = self._get_path(self.jp_ch_ass_path, "jp_ch_f.ass")
        if not jp_ch_ass_file: return
        try:
            scale_value = float(self.time_scale_value.get())
            if scale_value <= 0:
                messagebox.showerror("错误", "时间缩放值必须是正数。")
                return
        except (ValueError, TypeError):
            messagebox.showerror("错误", "无效的时间缩放值，请输入一个数字。")
            return
        output_path = jp_ch_ass_file.with_name(f"jp_ch_{scale_value}.ass")
        try:
            with open(jp_ch_ass_file, 'r', encoding='utf-8') as f_in:
                lines = f_in.readlines()
            new_lines = []
            dialogue_regex = re.compile(r"^(Dialogue: \d+,)([^,]+),([^,]+),(.+)")
            for line in lines:
                match = dialogue_regex.match(line)
                if match:
                    parts = list(match.groups())
                    start_time_str, end_time_str = parts[1], parts[2]
                    start_sec = self._hms_to_seconds(start_time_str)
                    end_sec = self._hms_to_seconds(end_time_str)
                    new_start_sec = start_sec * scale_value
                    new_end_sec = end_sec * scale_value
                    parts[1] = self._seconds_to_hms(new_start_sec)
                    parts[2] = self._seconds_to_hms(new_end_sec)
                    new_line = f"{parts[0]}{parts[1]},{parts[2]},{parts[3]}\n"
                    new_lines.append(new_line)
                else:
                    new_lines.append(line)
            with open(output_path, 'w', encoding='utf-8') as f_out:
                f_out.writelines(new_lines)
            self.log(f"时间轴已成功缩放 {scale_value} 倍。")
            self.log(f"文件已保存至: {output_path}")
            messagebox.showinfo("成功", f"文件已保存至:\n{output_path}")
        except Exception as e:
            self.log(f"发生错误: {e}")
            messagebox.showerror("异常", f"处理文件时发生异常: {e}")
        self.log("--- 功能9: 执行完毕 ---\n")
    
    def _parse_ass_header(self, lines):
        res_x, res_y = 1920, 1080
        for line in lines:
            line = line.strip()
            if line.lower().startswith("playresx:"):
                try: res_x = int(line.split(':')[1].strip())
                except ValueError: self.log(f"警告: 无法解析 PlayResX: '{line}'")
            elif line.lower().startswith("playresy:"):
                try: res_y = int(line.split(':')[1].strip())
                except ValueError: self.log(f"警告: 无法解析 PlayResY: '{line}'")
            elif line.strip() == "[Events]":
                break
        self.log(f"解析到屏幕分辨率: {res_x}x{res_y}")
        return res_x, res_y
    
    def _estimate_bbox(self, text, font_size):
        width = int(font_size * len(text) * 0.6)
        height = int(font_size * 1.2)
        return width, height

    def _calculate_layout(self, comments_to_place, screen_w, screen_h):
        positions = {}
        comments_to_place.sort(key=lambda item: item[2], reverse=True)
        margin = 10
        spacing = 5
        cursor_x = margin
        cursor_y = screen_h - margin
        row_height = 0
        for text, w, h, _ in comments_to_place:
            if cursor_x + w > screen_w - margin:
                cursor_x = margin
                cursor_y -= (row_height + spacing)
                row_height = 0
            positions[text] = (cursor_x, cursor_y)
            cursor_x += w + spacing
            row_height = max(row_height, h)
        return positions

    def run_reconstruct_danmaku(self):
        self.clear_log()
        self.log("--- 开始执行功能10: 重构高级弹幕 ---")
        input_file = self._get_path(self.jp_ch_ass_path, "jp_ch_value.ass (或其他输入源)")
        if not input_file: return
        try:
            threshold = self.reconstruct_params["threshold"].get()
            move_duration = self.reconstruct_params["move_duration"].get()
            base_font_size = self.reconstruct_params["base_font_size"].get()
        except tk.TclError:
            messagebox.showerror("错误", "参数无效，请输入正确的整数或小数。")
            return
        output_path = input_file.with_name("ultra_comments.ass")
        self.log(f"参数: 阈值={threshold}, 移动时长={move_duration}s, 基础字号={base_font_size}")
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            self.log("步骤 1/5: 分析弹幕内容和时间...")
            screen_w, screen_h = self._parse_ass_header(lines)
            header_lines = []
            dialogue_lines = []
            in_events_section = False
            for l in lines:
                if l.strip() == '[Events]':
                    in_events_section = True
                if l.strip().startswith("Dialogue:") and in_events_section:
                    dialogue_lines.append(l)
                else:
                    header_lines.append(l)
            comment_data = {} 
            for line in dialogue_lines:
                prefix, style, text = self._get_dialogue_parts(line)
                text = text.strip()
                if not text or prefix is None or '\\move' in style: continue
                line_parts = prefix.split(',')
                if len(line_parts) < 3:
                    self.log(f"警告: 跳过格式不完整的行: {line.strip()}")
                    continue
                start_sec = self._hms_to_seconds(line_parts[1])
                if text not in comment_data:
                    comment_data[text] = {"count": 0, "events": []}
                comment_data[text]["count"] += 1
                comment_data[text]["events"].append(start_sec)
            for text in comment_data:
                comment_data[text]["events"].sort()
            self.log(f"分析完成，找到 {len(comment_data)} 种不同弹幕。")
            self.log("步骤 2/5: 生成飞入弹幕效果...")
            new_dialogues = []
            for text, data in comment_data.items():
                for start_time in data["events"]:
                    end_time = start_time + move_duration
                    start_y = random.randint(0, int(screen_h * 0.6))
                    end_y = random.randint(int(screen_h * 0.2), int(screen_h * 0.8))
                    move_tag = f"\\move({screen_w}, {start_y}, 0, {end_y}, 0, {int(move_duration * 1000)})"
                    style_tag = f"{{{move_tag}\\1a&H80&}}"
                    line = f"Dialogue: 0,{self._seconds_to_hms(start_time)},{self._seconds_to_hms(end_time)},Default,,0,0,0,,{style_tag}{text}\n"
                    new_dialogues.append(line)
            self.log(f"已生成 {len(new_dialogues)} 条飞入弹幕。")
            self.log("步骤 3/5: 处理固定弹幕布局...")
            hot_comments = {t: d for t, d in comment_data.items() if d["count"] >= threshold}
            if not hot_comments:
                self.log("没有达到阈值的热门弹幕，跳过固定弹幕生成。")
            else:
                self.log(f"找到 {len(hot_comments)} 种热门弹幕。")
                event_times = sorted(list(set(time for text in hot_comments for time in hot_comments[text]["events"])))
                if not event_times:
                     self.log("热门弹幕没有有效的时间事件，跳过。")
                else:
                    event_times.append(event_times[-1] + 30) 
                    current_counts = Counter()
                    for i in range(len(event_times) - 1):
                        interval_start = event_times[i]
                        interval_end = event_times[i+1]
                        for text, data in hot_comments.items():
                            if interval_start in data["events"]:
                                current_counts[text] += data["events"].count(interval_start)
                        comments_to_place = []
                        for text, count in current_counts.items():
                            scale_factor = 1 + (9 * (count**0.5 / 100**0.5)) if count > 1 else 1
                            current_font_size = base_font_size * scale_factor
                            w, h = self._estimate_bbox(text, current_font_size)
                            comments_to_place.append((text, w, h, {"count": count, "scale": scale_factor}))
                        if not comments_to_place: continue
                        layout = self._calculate_layout(comments_to_place, screen_w, screen_h)
                        for text, (x,y) in layout.items():
                            count_data = next(item[3] for item in comments_to_place if item[0] == text)
                            scale_percent = int(count_data["scale"] * 100)
                            style_tag = f"\\an7\\pos({x},{y})\\fscx{scale_percent}\\fscy{scale_percent}\\fs{base_font_size}\\1a&H00&"
                            line = f"Dialogue: 1,{self._seconds_to_hms(interval_start)},{self._seconds_to_hms(interval_end)},Default,,0,0,0,,{{{style_tag}}}{text}\n"
                            new_dialogues.append(line)
            self.log("步骤 5/5: 写入最终ass文件...")
            final_content = "".join(header_lines) + "".join(new_dialogues)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            self.log(f"高级弹幕文件已成功生成: {output_path}")
            messagebox.showinfo("成功", f"文件已保存至:\n{output_path}")
        except Exception as e:
            self.log(f"发生严重错误: {e}")
            import traceback
            self.log(traceback.format_exc())
            messagebox.showerror("异常", f"处理文件时发生异常: {e}")
        self.log("--- 功能10: 执行完毕 ---\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = AssTranslatorApp(root)
    root.mainloop()