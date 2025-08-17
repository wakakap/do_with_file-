# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
import csv
from pathlib import Path
from collections import Counter, defaultdict
import random
import math
import xml.etree.ElementTree as ET
from datetime import timedelta

class AssTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ASS 弹幕翻译 & 处理工具 (v2.0)")
        self.root.geometry("850x850") # 增加窗口高度以容纳新功能

        # --- 文件路径部分 ---
        path_frame = ttk.LabelFrame(self.root, text="文件路径 (File Paths)")
        path_frame.pack(padx=10, pady=10, fill="x")

        self.xml_path = tk.StringVar()
        self.jp_ass_path = tk.StringVar()
        self.jp_ch_ass_path = tk.StringVar()
        self.csv_path = tk.StringVar()
        self.already_txt_path = tk.StringVar()
        self.need_honyaku_path = tk.StringVar()
        self.honyaku_temp_path = tk.StringVar()

        # XML是新的起点
        self._create_path_entry(path_frame, "源XML文件 (Source XML):", self.xml_path, self._browse_xml_file)
        self._create_path_entry(path_frame, "日文ASS (jp.ass):", self.jp_ass_path, self._browse_file)
        self._create_path_entry(path_frame, "中文ASS (jp_ch.ass):", self.jp_ch_ass_path, self._browse_file)
        self._create_path_entry(path_frame, "翻译数据 (hoyanku_data.csv):", self.csv_path, self._browse_file)
        self._create_path_entry(path_frame, "已翻译索引 (already_index_temp.txt):", self.already_txt_path, self._browse_file)
        self._create_path_entry(path_frame, "待翻译原文 (need_honyaku_temp.txt):", self.need_honyaku_path, self._browse_file)
        self._create_path_entry(path_frame, "翻译后文本 (honyaku_temp.txt):", self.honyaku_temp_path, self._browse_file)


        # --- 功能区 ---
        main_frame = ttk.Frame(self.root)
        main_frame.pack(padx=10, pady=5, fill="x")

        # --- 步骤1: XML转ASS ---
        xml_conv_frame = ttk.LabelFrame(main_frame, text="步骤 1: 从XML生成ASS文件 (Generate ASS from XML)")
        xml_conv_frame.pack(fill="x", pady=5)
        
        xml_params_grid = ttk.Frame(xml_conv_frame)
        xml_params_grid.pack(fill="x", pady=5, padx=5)

        self.xml_params = {
            "VIDEO_WIDTH": tk.IntVar(value=1920), "VIDEO_HEIGHT": tk.IntVar(value=1080),
            "BASE_FONT_SIZE": tk.IntVar(value=45), "SCROLL_DURATION": tk.IntVar(value=16),
            "FIXED_DURATION": tk.IntVar(value=4), "AVOID_BLOCK_TIME": tk.IntVar(value=4),
            "NUM_TOP_TRACKS": tk.IntVar(value=8), "NUM_BOTTOM_TRACKS": tk.IntVar(value=8),
        }
        
        param_labels = ["视频宽度:", "视频高度:", "基准字号:", "滚动时长(s):", "固定时长(s):", "轨道占用(s):", "顶部轨道:", "底部轨道:"]
        for i, (key, var) in enumerate(self.xml_params.items()):
            ttk.Label(xml_params_grid, text=param_labels[i]).grid(row=i//4, column=(i%4)*2, padx=5, pady=2, sticky="w")
            ttk.Entry(xml_params_grid, textvariable=var, width=8).grid(row=i//4, column=(i%4)*2+1, padx=5, pady=2, sticky="ew")

        ttk.Button(xml_conv_frame, text="1. 生成ASS文件 (Generate ASS File)", command=self.run_xml_to_ass).pack(fill="x", padx=5, pady=5)

        # --- 步骤2: 翻译流程 ---
        func_frame = ttk.LabelFrame(main_frame, text="步骤 2: 翻译流程 (Translation Workflow)")
        func_frame.pack(fill="x", pady=5,  expand=True)

        btn_texts = [
            ("2. 检查ASS格式", self.run_check_ass_format),
            ("3. 检查对应格式", self.run_check_format_consistency),
            ("4. 新建空白 jp_ch.ass", self.run_create_empty_chinese_ass),
            ("5. 扫描已有翻译", self.run_scan_existing_translations),
            ("6. 提取待翻译内容", self.run_extract_needed_translations),
            ("7. 回填翻译内容", self.run_fill_in_translations),
            ("8. 分析待翻译内容重复项", self.run_analyze_needed_translations)
        ]
        
        for i, (text, command) in enumerate(btn_texts):
            button = ttk.Button(func_frame, text=text, command=command)
            button.grid(row=i // 2, column=i % 2, padx=5, pady=5, sticky="ew")
        
        func_frame.grid_columnconfigure(0, weight=1)
        func_frame.grid_columnconfigure(1, weight=1)

        # --- 高级功能部分 ---
        adv_func_frame = ttk.LabelFrame(self.root, text="高级功能 (Advanced Functions)")
        adv_func_frame.pack(padx=10, pady=10, fill="x")

        # --- 合并双语 ---
        ttk.Button(adv_func_frame, text="合并为双语字幕 (Merge to Bilingual)", command=self.run_merge_to_bilingual).pack(fill="x", padx=5, pady=5)
        
        # --- 压缩时间轴 ---
        compress_frame = ttk.Frame(adv_func_frame)
        compress_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(compress_frame, text="时间缩放值 (Value):").pack(side="left", padx=5)
        self.time_scale_value = tk.StringVar(value="1.0")
        ttk.Entry(compress_frame, textvariable=self.time_scale_value, width=10).pack(side="left", padx=5)
        ttk.Button(compress_frame, text="压缩/拉伸时间轴 (Compress/Stretch Timeline)", command=self.run_compress_timeline).pack(side="left", fill="x", expand=True, padx=5)

        # --- 新增: 合并密集弹幕 ---
        merge_dense_frame = ttk.LabelFrame(adv_func_frame, text="合并密集滚动弹幕 (Merge Dense Scrolling Comments)")
        merge_dense_frame.pack(fill="x", padx=5, pady=5)
        merge_params_grid = ttk.Frame(merge_dense_frame)
        merge_params_grid.pack(fill="x", pady=5)
        
        ttk.Label(merge_params_grid, text="合并阈值 (Thread):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.merge_thread = tk.IntVar(value=8)
        ttk.Entry(merge_params_grid, textvariable=self.merge_thread, width=8).grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(merge_params_grid, text="扫描时长(分钟) (Max Minutes):").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.merge_max_minutes = tk.IntVar(value=30)
        ttk.Entry(merge_params_grid, textvariable=self.merge_max_minutes, width=8).grid(row=0, column=3, padx=5, pady=2)
        ttk.Button(merge_dense_frame, text="执行合并 (Run Merge)", command=self.run_merge_dense_comments).pack(fill="x", padx=5, pady=5)

        # --- 日志输出部分 ---
        log_frame = ttk.LabelFrame(self.root, text="输出日志 (Output Log)")
        log_frame.pack(padx=10, pady=10, fill="both", expand=True)
        self.log_text = tk.Text(log_frame, wrap="word", height=15)
        self.log_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=log_scrollbar.set)

    # --- GUI 辅助方法 ---
    def _create_path_entry(self, parent, label_text, string_var, command):
        frame = ttk.Frame(parent)
        frame.pack(fill="x", padx=5, pady=2)
        label = ttk.Label(frame, text=label_text, width=28)
        label.pack(side="left")
        entry = ttk.Entry(frame, textvariable=string_var)
        entry.pack(side="left", fill="x", expand=True)
        button = ttk.Button(frame, text="浏览(Browse)", command=lambda: command(string_var))
        button.pack(side="right", padx=5)

    def _browse_xml_file(self, string_var):
        file_path = filedialog.askopenfilename(filetypes=[("XML files", "*.xml")])
        if file_path:
            p = Path(file_path)
            string_var.set(file_path)
            # 自动填充所有其他路径
            base_name = p.stem
            self.jp_ass_path.set(p.with_name(f"{base_name}_comments.ass"))
            self.jp_ch_ass_path.set(p.with_name(f"{base_name}_comments_ch.ass"))
            self.csv_path.set(p.with_name(f"{base_name}_hoyanku_data.csv"))
            self.already_txt_path.set(p.with_name(f"{base_name}_already_index_temp.txt"))
            self.need_honyaku_path.set(p.with_name(f"{base_name}_need_honyaku_temp.txt"))
            self.honyaku_temp_path.set(p.with_name(f"{base_name}_honyaku_temp.txt"))

    def _browse_file(self, string_var):
        file_path = filedialog.askopenfilename()
        if file_path:
            string_var.set(file_path)

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def _get_path(self, var, name, check_exists=True):
        path = var.get()
        if not path:
            messagebox.showerror("错误 (Error)", f"文件路径未设置: {name}")
            return None
        if check_exists and not os.path.exists(path):
            messagebox.showerror("错误 (Error)", f"文件不存在: {name}\n路径: {path}")
            return None
        return Path(path)

    # --- 通用 ASS 解析辅助方法 ---
    def _get_dialogue_parts(self, line):
        line = line.strip()
        if not line.startswith("Dialogue:"): return None, None, None
        parts = line.split(',', 9)
        if len(parts) != 10: return None, None, None
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
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{int(h):01}:{int(m):02}:{int(s):02}.{int((seconds - math.floor(seconds)) * 100):02}"

    def _clean_text_for_matching(self, text):
        if not isinstance(text, str): return ""
        return re.sub(r'[\s\u3000]', '', text)
        
    # --- 功能 1: XML to ASS (新) ---
    def run_xml_to_ass(self):
        self.clear_log()
        self.log("--- 开始执行功能1: 从XML生成ASS文件 ---")
        xml_file = self._get_path(self.xml_path, "Source XML")
        if not xml_file: return
        output_ass_file = self._get_path(self.jp_ass_path, "Output jp.ass", check_exists=False)
        if not output_ass_file: return

        try:
            params = {key: var.get() for key, var in self.xml_params.items()}
            self.log(f"使用参数: {params}")
        except tk.TclError:
            messagebox.showerror("错误", "参数无效，请输入正确的数字。")
            return

        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
        except FileNotFoundError:
            self.log(f"错误: 找不到 XML 文件 '{xml_file}'。")
            return
        except ET.ParseError:
            self.log(f"错误: XML 文件 '{xml_file}' 格式不正确，无法解析。")
            return

        ass_header = f"""[Script Info]
Title: {xml_file.stem}
ScriptType: v4.00+
WrapStyle: 0
PlayResX: {params['VIDEO_WIDTH']}
PlayResY: {params['VIDEO_HEIGHT']}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft YaHei UI,{params['BASE_FONT_SIZE']},&HFFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        COLOR_MAP = {'white':'&HFFFFFF&','red':'&H0000FF&','pink':'&HFF8080&','orange':'&H0080FF&','yellow':'&H00FFFF&',
                     'green':'&H00FF00&','cyan':'&HFFFF00&','blue':'&HFF0000&','purple':'&HFF00FF&','black':'&H000000&'}

        track_height = params['BASE_FONT_SIZE']
        num_scroll_tracks = params['VIDEO_HEIGHT'] // track_height
        scroll_track_availability = [0.0] * num_scroll_tracks
        top_track_availability = [0.0] * params['NUM_TOP_TRACKS']
        bottom_track_availability = [0.0] * params['NUM_BOTTOM_TRACKS']

        with open(output_ass_file, 'w', encoding='utf-8') as f:
            f.write(ass_header.strip())
            for chat in root.findall('chat'):
                try:
                    vpos_sec = int(chat.get('vpos')) / 100.0
                    raw_text = "".join(chat.itertext()).strip()
                    if not raw_text: continue

                    mail = chat.get('mail', '').split()
                    is_multiline = '\n' in raw_text
                    processed_text = raw_text.replace('\n', r'\N') if is_multiline else raw_text
                    
                    is_top = 'ue' in mail; is_bottom = 'shita' in mail
                    
                    font_size = params['BASE_FONT_SIZE']
                    if 'big' in mail: font_size = int(font_size * 1.25)
                    elif 'small' in mail: font_size = int(font_size * 0.8)

                    color_hex = '&HFFFFFF&'
                    for cmd in mail:
                        if cmd in COLOR_MAP: color_hex = COLOR_MAP[cmd]; break

                    effects = []
                    if color_hex != '&HFFFFFF&': effects.append(f"\\c{color_hex}")
                    if font_size != params['BASE_FONT_SIZE']: effects.append(f"\\fs{font_size}")
                    
                    start_time = vpos_sec
                    dialogue_line = ""

                    if is_top or is_bottom:
                        end_time = start_time + params['FIXED_DURATION']
                        chosen_track, y_pos = -1, 0
                        track_system = top_track_availability if is_top else bottom_track_availability
                        num_tracks_in_system = params['NUM_TOP_TRACKS'] if is_top else params['NUM_BOTTOM_TRACKS']
                        
                        for i in range(num_tracks_in_system):
                            if track_system[i] <= start_time: chosen_track = i; break
                        if chosen_track == -1: chosen_track = random.randint(0, num_tracks_in_system - 1)
                        
                        if is_top:
                            y_pos = chosen_track * (font_size)
                            effects.append(f"\\an8\\pos({params['VIDEO_WIDTH']/2}, {y_pos})")
                        else:
                            y_pos = params['VIDEO_HEIGHT'] - chosen_track * (font_size)
                            effects.append(f"\\an2\\pos({params['VIDEO_WIDTH']/2}, {y_pos})")
                        
                        track_system[chosen_track] = end_time
                        effect_str = "{" + "".join(effects) + "}"
                        dialogue_line = f"\nDialogue: 1,{self._seconds_to_hms(start_time)},{self._seconds_to_hms(end_time)},Default,,0,0,0,,{effect_str}{processed_text}"

                    else: # 滚动弹幕 (包括旧的多行逻辑)
                        end_time = start_time + params['SCROLL_DURATION']
                        text_width = len(re.sub(r'\\N', '', processed_text)) * font_size
                        
                        if is_multiline: # 字符画特殊处理
                            y_pos = params['VIDEO_HEIGHT'] / 2
                            effects.append(f"\\an5\\move({params['VIDEO_WIDTH'] + text_width / 2}, {y_pos}, {-text_width / 2}, {y_pos})")
                            layer = 2
                        else: # 普通滚动弹幕
                            chosen_track = -1
                            for i in range(num_scroll_tracks):
                                if scroll_track_availability[i] <= start_time: chosen_track = i; break
                            if chosen_track == -1: chosen_track = min(range(num_scroll_tracks), key=lambda i: scroll_track_availability[i])
                            
                            scroll_track_availability[chosen_track] = start_time + params['AVOID_BLOCK_TIME']
                            y_pos = (chosen_track * track_height)
                            effects.append(f"\\an4\\move({params['VIDEO_WIDTH']}, {y_pos}, {-text_width}, {y_pos})")
                            layer = 0
                        
                        effect_str = "{" + "".join(effects) + "}"
                        dialogue_line = f"\nDialogue: {layer},{self._seconds_to_hms(start_time)},{self._seconds_to_hms(end_time)},Default,,0,0,0,,{effect_str}{processed_text}"

                    f.write(dialogue_line)
                except (TypeError, ValueError) as e:
                    self.log(f"警告: 跳过一条格式错误的弹幕: chat={chat.attrib}, text='{raw_text[:30]}...', 错误: {e}")
                    continue
        
        self.log(f"成功！ASS字幕文件 '{output_ass_file.name}' 已生成。")
        messagebox.showinfo("成功", f"文件已生成:\n{output_ass_file.name}")
        self.log("--- 功能1: 执行完毕 ---\n")

    # --- 功能 2: 检查ASS格式---
    def run_check_ass_format(self):
        self.clear_log()
        self.log("--- 开始执行功能2: 检查ASS格式 ---")
        jp_ass_file = self._get_path(self.jp_ass_path, "jp.ass")
        if not jp_ass_file: return
        
        invalid_lines = []
        try:
            with open(jp_ass_file, 'r', encoding='utf-8-sig') as f: lines = f.readlines()
            
            format_line_found = False
            for i, line in enumerate(lines):
                if line.strip().startswith("[Events]"):
                    format_line_found = True
                    start_scan_index = i + 2 # Format行下一行开始
                    break
            
            if not format_line_found:
                self.log("错误: 文件中未找到 '[Events]'。")
                return

            for i in range(start_scan_index, len(lines)):
                line_num = i + 1; line = lines[i].strip()
                if not line: continue
                if not line.startswith("Dialogue:"):
                    invalid_lines.append(line_num); continue
                
                parts = line.split(',', 9)
                errors = []
                if len(parts) != 10: errors.append("逗号数量不正确")
                time_regex = re.compile(r'^\d+:\d{2}:\d{2}\.\d{2}$')
                if len(parts) > 2 and not time_regex.match(parts[1]): errors.append("开始时间格式错误")
                if len(parts) > 2 and not time_regex.match(parts[2]): errors.append("结束时间格式错误")
                if len(parts) == 10 and parts[9].count('{') != parts[9].count('}'): errors.append("花括号不匹配")
                
                if errors:
                    self.log(f"第 {line_num} 行错误: {'; '.join(errors)}")
                    invalid_lines.append(line_num)

            if not invalid_lines:
                self.log("检查完成。所有相关行格式均正确。")
                messagebox.showinfo("成功", "检查完成，所有相关行格式均正确。")
            else:
                self.log(f"\n检查完成。发现 {len(invalid_lines)} 个格式错误的行: {', '.join(map(str, sorted(list(set(invalid_lines)))))}")
                messagebox.showwarning("完成", f"检查发现 {len(invalid_lines)} 个错误行，详情请看日志。")

        except Exception as e:
            self.log(f"发生错误: {e}")
        self.log("--- 功能2: 执行完毕 ---\n")

    # --- 功能 3: 检查对应格式 ---
    def check_format_consistency_logic(self, silent=False):
        jp_ass_file = self._get_path(self.jp_ass_path, "jp.ass")
        jp_ch_ass_file = self._get_path(self.jp_ch_ass_path, "jp_ch.ass")
        if not jp_ass_file or not jp_ch_ass_file: return False
        
        try:
            with open(jp_ass_file, 'r', encoding='utf-8') as f1, open(jp_ch_ass_file, 'r', encoding='utf-8') as f2:
                for i, (line1, line2) in enumerate(zip(f1, f2)):
                    line_num = i + 1
                    if line1.strip().startswith("Dialogue:"):
                        prefix1, _, _ = self._get_dialogue_parts(line1)
                        prefix2, _, _ = self._get_dialogue_parts(line2)
                        if prefix1 != prefix2:
                            if not silent:
                                self.log(f"格式不匹配于第 {line_num} 行。")
                                messagebox.showwarning("不匹配", f"在第 {line_num} 行发现格式不匹配。")
                            return False
                    elif line1.strip() != line2.strip():
                         if not silent:
                                self.log(f"第 {line_num} 行不匹配 (非Dialogue行).")
                         return False
            if not silent:
                self.log("所有对应行格式均一致。")
                messagebox.showinfo("成功", "所有对应行格式均一致。")
            return True
        except Exception as e:
            if not silent: self.log(f"发生错误: {e}")
            return False

    def run_check_format_consistency(self):
        self.clear_log()
        self.log("--- 开始执行功能3: 检查对应格式 ---")
        self.check_format_consistency_logic()
        self.log("--- 功能3: 执行完毕 ---\n")

    # --- 功能 4: 新建空白 jp_ch.ass ---
    def run_create_empty_chinese_ass(self):
        self.clear_log()
        self.log("--- 开始执行功能4: 新建空白 jp_ch.ass ---")
        jp_ass_file = self._get_path(self.jp_ass_path, "jp.ass")
        jp_ch_ass_file = self._get_path(self.jp_ch_ass_path, "jp_ch.ass", check_exists=False)
        if not jp_ass_file or not jp_ch_ass_file: return

        try:
            with open(jp_ass_file, 'r', encoding='utf-8') as f_in, open(jp_ch_ass_file, 'w', encoding='utf-8') as f_out:
                for line in f_in:
                    if line.strip().startswith("Dialogue:"):
                        prefix, style, _ = self._get_dialogue_parts(line)
                        f_out.write(f"{prefix},{style}\n" if prefix else line)
                    else:
                        f_out.write(line)
            self.log(f"成功创建文件: {jp_ch_ass_file}")
            messagebox.showinfo("成功", f"成功创建文件:\n{jp_ch_ass_file}")
        except Exception as e:
            self.log(f"发生错误: {e}")
        self.log("--- 功能4: 执行完毕 ---\n")

    # --- 功能 5: 扫描已有翻译 ---
    def run_scan_existing_translations(self):
        self.clear_log()
        self.log("--- 开始执行功能5: 扫描已有翻译 ---")
        if not self.check_format_consistency_logic(silent=True):
            self.log("错误: 'jp.ass' 与 'jp_ch.ass' 格式不匹配，无法继续。")
            return

        jp_ass_file = self._get_path(self.jp_ass_path, "jp.ass")
        jp_ch_ass_file = self._get_path(self.jp_ch_ass_path, "jp_ch.ass")
        csv_file = self._get_path(self.csv_path, "hoyanku_data.csv")
        already_txt_file = self._get_path(self.already_txt_path, "already_index_temp.txt", check_exists=False)
        if not all([jp_ass_file, jp_ch_ass_file, csv_file, already_txt_file]): return

        try:
            trans_dict = {}
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        trans_dict[self._clean_text_for_matching(row[0])] = row[1]
            self.log(f"加载 {len(trans_dict)} 条翻译记录。")

            with open(jp_ass_file, 'r', encoding='utf-8') as f: jp_lines = f.readlines()
            ch_lines = list(jp_lines)
            found_indices = []
            
            for i, jp_line in enumerate(jp_lines):
                prefix, style, text = self._get_dialogue_parts(jp_line)
                if text is not None:
                    cleaned_text = self._clean_text_for_matching(text)
                    if cleaned_text in trans_dict:
                        translation = trans_dict[cleaned_text]
                        ch_lines[i] = f"{prefix},{style}{translation}\n"
                        found_indices.append(str(i + 1))
            
            self.log(f"扫描完成，共找到并更新 {len(found_indices)} 行。")
            with open(jp_ch_ass_file, 'w', encoding='utf-8') as f: f.writelines(ch_lines)
            with open(already_txt_file, 'w', encoding='utf-8') as f: f.write(','.join(found_indices))

            messagebox.showinfo("成功", f"操作完成！\n{len(found_indices)} 行已更新。")
        except Exception as e:
            self.log(f"发生错误: {e}")
        self.log("--- 功能5: 执行完毕 ---\n")

    # --- 功能 6: 提取待翻译内容 ---
    def run_extract_needed_translations(self):
        self.clear_log()
        self.log("--- 开始执行功能6: 提取待翻译内容 ---")
        jp_ass_file = self._get_path(self.jp_ass_path, "jp.ass")
        already_txt_file = self._get_path(self.already_txt_path, "already_index_temp.txt")
        need_honyaku_file = self._get_path(self.need_honyaku_path, "need_honyaku_temp.txt", check_exists=False)
        if not all([jp_ass_file, already_txt_file, need_honyaku_file]): return

        try:
            with open(already_txt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                already_indices = set(content.split(',')) if content else set()

            needed_strings = []
            with open(jp_ass_file, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if str(i + 1) not in already_indices:
                        _, _, text = self._get_dialogue_parts(line)
                        if text is not None: needed_strings.append(text)
            
            with open(need_honyaku_file, 'w', encoding='utf-8') as f:
                for s in needed_strings: f.write(s + '\n')
            
            self.log(f"成功提取 {len(needed_strings)} 条待翻译内容到: {need_honyaku_file.name}")
            messagebox.showinfo("成功", f"成功提取 {len(needed_strings)} 条待翻译内容。")
        except Exception as e:
            self.log(f"发生错误: {e}")
        self.log("--- 功能6: 执行完毕 ---\n")

    # --- 功能 7: 回填翻译内容 ---
    def run_fill_in_translations(self):
        self.clear_log()
        self.log("--- 开始执行功能7: 回填翻译内容 ---")
        jp_ch_ass_file = self._get_path(self.jp_ch_ass_path, "jp_ch.ass")
        honyaku_temp_file = self._get_path(self.honyaku_temp_path, "honyaku_temp.txt")
        already_txt_file = self._get_path(self.already_txt_path, "already_index_temp.txt")
        if not all([jp_ch_ass_file, honyaku_temp_file, already_txt_file]): return
        
        try:
            with open(already_txt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                already_indices = set(int(x) for x in content.split(',')) if content else set()
            with open(honyaku_temp_file, 'r', encoding='utf-8') as f:
                translated_lines = [line.strip() for line in f.readlines()]
            with open(jp_ch_ass_file, 'r', encoding='utf-8') as f:
                ch_lines = f.readlines()
            
            lines_to_update_indices = [i for i, line in enumerate(ch_lines) if line.strip().startswith("Dialogue:") and (i + 1) not in already_indices]
            
            if len(translated_lines) != len(lines_to_update_indices):
                msg = f"翻译文本数量 ({len(translated_lines)}) 与需回填行数 ({len(lines_to_update_indices)}) 不匹配!"
                self.log(f"错误: {msg}")
                messagebox.showerror("数量不匹配", msg)
                return

            for i, line_index in enumerate(lines_to_update_indices):
                prefix, style, _ = self._get_dialogue_parts(ch_lines[line_index])
                if prefix: ch_lines[line_index] = f"{prefix},{style}{translated_lines[i]}\n"

            with open(jp_ch_ass_file, 'w', encoding='utf-8') as f: f.writelines(ch_lines)
            self.log(f"成功将 {len(translated_lines)} 行翻译回填到 '{jp_ch_ass_file.name}'。")
            messagebox.showinfo("成功", f"成功完成！{len(translated_lines)} 行翻译已回填。")
        except Exception as e:
            self.log(f"发生错误: {e}")
        self.log("--- 功能7: 执行完毕 ---\n")

    # --- 功能 8: 分析待翻译内容重复项 ---
    def run_analyze_needed_translations(self):
        self.clear_log()
        self.log("--- 开始执行功能8: 分析待翻译内容重复项 ---")
        need_honyaku_file = self._get_path(self.need_honyaku_path, "need_honyaku_temp.txt")
        if not need_honyaku_file: return
        try:
            with open(need_honyaku_file, 'r', encoding='utf-8') as f: lines = f.readlines()
            cleaned_lines = [self._clean_text_for_matching(line.strip()) for line in lines]
            counter = Counter(cleaned_lines)
            most_common_items = counter.most_common(100)
            
            self.log("\n--- 分析结果：出现频率最高的前100项 (已忽略空格) ---")
            self.log("名次 | 出现次数 | 清理后的内容")
            self.log("---- | -------- | -----------")
            for i, (item, count) in enumerate(most_common_items):
                self.log(f"{i+1:<4} | {count:<8} | {item if item else '[空]'}")
            messagebox.showinfo("分析完成", f"分析完成！共统计 {len(counter)} 种不同内容。")
        except Exception as e:
            self.log(f"发生错误: {e}")
        self.log("--- 功能8: 执行完毕 ---\n")

    # --- 高级功能: 合并双语 ---
    def run_merge_to_bilingual(self):
        self.clear_log()
        self.log("--- 开始执行高级功能: 合并为双语字幕 ---")
        jp_ass_file = self._get_path(self.jp_ass_path, "jp.ass")
        jp_ch_ass_file = self._get_path(self.jp_ch_ass_path, "jp_ch.ass")
        if not jp_ass_file or not jp_ch_ass_file: return
        
        output_path = jp_ass_file.with_name(f"{jp_ass_file.stem}_bilingual.ass")
        try:
            with open(jp_ass_file, 'r', encoding='utf-8') as f_jp: jp_lines = f_jp.readlines()
            with open(jp_ch_ass_file, 'r', encoding='utf-8') as f_ch: ch_lines = f_ch.readlines()
            
            if len(jp_lines) != len(ch_lines):
                messagebox.showerror("错误", "文件行数不一致!"); return

            new_lines = []
            for i, jp_line in enumerate(jp_lines):
                if jp_line.strip().startswith("Dialogue:"):
                    prefix, style, jp_text = self._get_dialogue_parts(jp_line)
                    _, _, ch_text = self._get_dialogue_parts(ch_lines[i])
                    if prefix and ch_text is not None:
                        new_lines.append(f"{prefix},{style}{ch_text.strip()} | {jp_text.strip()}\n")
                    else:
                        new_lines.append(jp_line)
                else:
                    new_lines.append(jp_line)

            with open(output_path, 'w', encoding='utf-8') as f_out: f_out.writelines(new_lines)
            self.log(f"双语字幕文件已成功生成: {output_path}")
            messagebox.showinfo("成功", f"文件已保存至:\n{output_path}")
        except Exception as e:
            self.log(f"发生错误: {e}")
        self.log("--- 双语合并执行完毕 ---\n")

    # --- 高级功能: 压缩/拉伸时间轴 ---
    def run_compress_timeline(self):
        self.clear_log()
        self.log("--- 开始执行高级功能: 压缩/拉伸时间轴 ---")
        target_file = self._get_path(self.jp_ch_ass_path, "jp_ch.ass")
        if not target_file: return
        
        try:
            scale_value = float(self.time_scale_value.get())
            if scale_value <= 0: messagebox.showerror("错误", "时间缩放值必须是正数。"); return
        except (ValueError, TypeError):
            messagebox.showerror("错误", "无效的时间缩放值。"); return
        
        output_path = target_file.with_name(f"{target_file.stem}_scaled_{scale_value}.ass")
        try:
            with open(target_file, 'r', encoding='utf-8') as f_in: lines = f_in.readlines()
            new_lines = []
            for line in lines:
                if line.startswith("Dialogue:"):
                    parts = line.split(',', 9)
                    start_sec = self._hms_to_seconds(parts[1]) * scale_value
                    end_sec = self._hms_to_seconds(parts[2]) * scale_value
                    parts[1] = self._seconds_to_hms(start_sec)
                    parts[2] = self._seconds_to_hms(end_sec)
                    new_lines.append(",".join(parts))
                else:
                    new_lines.append(line)
            with open(output_path, 'w', encoding='utf-8') as f_out: f_out.writelines(new_lines)
            self.log(f"时间轴已成功缩放 {scale_value} 倍，文件已保存至: {output_path}")
            messagebox.showinfo("成功", f"文件已保存至:\n{output_path}")
        except Exception as e:
            self.log(f"发生错误: {e}")
        self.log("--- 时间轴调整执行完毕 ---\n")

    # --- 高级功能: 合并密集弹幕 (新) ---
    def run_merge_dense_comments(self):
        self.clear_log()
        self.log("--- 开始执行高级功能: 合并密集滚动弹幕 ---")
        input_file = self._get_path(self.jp_ch_ass_path, "jp_ch.ass")
        if not input_file: return
        
        output_path = input_file.with_name(f"{input_file.stem}_merged.ass")
        try:
            thread = self.merge_thread.get()
            max_minutes = self.merge_max_minutes.get()
        except tk.TclError:
            messagebox.showerror("错误", "合并参数无效，请输入整数。"); return

        try:
            header_and_styles, dialogue_lines = [], []
            with open(input_file, 'r', encoding='utf-8') as f:
                is_event_section = False
                for line in f:
                    if line.strip() == '[Events]': is_event_section = True
                    if is_event_section and line.strip().startswith('Dialogue:'):
                        dialogue_lines.append(line)
                    else:
                        header_and_styles.append(line)

            move_lines_with_indices = [(i, line) for i, line in enumerate(dialogue_lines) if r'\move' in line]
            other_lines = [line for i, line in enumerate(dialogue_lines) if r'\move' not in dialogue_lines[i]]
            
            # Helper to parse time
            def parse_time(t_str):
                h, m, s_ms = t_str.split(':')
                s, cs = s_ms.split('.')
                return timedelta(hours=int(h), minutes=int(m), seconds=int(s), milliseconds=int(cs)*10)

            move_lines_with_indices.sort(key=lambda x: parse_time(x[1].split(',')[1]))
            self.log(f"共找到 {len(move_lines_with_indices)} 条滚动弹幕。")
            
            processed_original_indices, newly_created_lines = set(), []
            
            for t_sec in range(max_minutes * 60):
                current_time = timedelta(seconds=t_sec)
                active_groups = defaultdict(list)
                
                for original_idx, line_str in move_lines_with_indices:
                    if original_idx in processed_original_indices: continue
                    parts = line_str.split(',', 9)
                    start_time, end_time = parse_time(parts[1]), parse_time(parts[2])

                    if start_time > current_time: break
                    if start_time <= current_time < end_time:
                        _, _, text = self._get_dialogue_parts(line_str)
                        active_groups[text.strip() if text else ""].append(original_idx)
                
                for content, indices_list in active_groups.items():
                    unprocessed_indices = [idx for idx in indices_list if idx not in processed_original_indices]
                    
                    while len(unprocessed_indices) >= thread:
                        self.log(f"在 {current_time} 检测到内容为 '{content}' 的弹幕 {len(unprocessed_indices)} 条，执行合并...")
                        indices_to_replace = unprocessed_indices[:thread]
                        processed_original_indices.update(indices_to_replace)
                        
                        template_line_str = dialogue_lines[indices_to_replace[0]]
                        prefix, style, text = self._get_dialogue_parts(template_line_str)
                        
                        # Set font size
                        fs_pattern = re.compile(r'(\\fs)(\d+)')
                        if fs_pattern.search(style):
                            new_style = fs_pattern.sub(r'\1{100}', style)
                        else:
                            new_style = style[:-1] + r'\fs100}'

                        new_big_line = f"{prefix},{new_style}{text}\n"
                        newly_created_lines.append(new_big_line)
                        unprocessed_indices = unprocessed_indices[thread:]
            
            final_dialogue_lines = list(other_lines)
            for i, line in enumerate(dialogue_lines):
                if r'\move' in line and i not in processed_original_indices:
                    final_dialogue_lines.append(line)
            final_dialogue_lines.extend(newly_created_lines)
            final_dialogue_lines.sort(key=lambda x: parse_time(x.split(',')[1]))

            with open(output_path, 'w', encoding='utf-8') as f:
                f.writelines(header_and_styles)
                f.writelines(final_dialogue_lines)

            self.log(f"处理完成！修改后的文件已保存至: {output_path}")
            messagebox.showinfo("成功", f"文件已保存至:\n{output_path}")
        except Exception as e:
            import traceback
            self.log(f"发生严重错误: {e}\n{traceback.format_exc()}")
            messagebox.showerror("异常", f"处理时发生异常: {e}")
        self.log("--- 密集弹幕合并执行完毕 ---\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = AssTranslatorApp(root)
    root.mainloop()