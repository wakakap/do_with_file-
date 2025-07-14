# -*- coding: utf-8 -*-
# 我在做一个翻译弹幕文件ass的项目，用python帮我实现以下功能，并把功能集成在一个界面上。我的设计思路是: 翻译的文件是jp.ass，新建文件jp_ch.ass，储存数据的hoyanku_data.csv。文件浏览选择jp.ass，功能1“检查ass”: 读取jp.ass，找到Format开头的行，然后从下一行逐行扫描，每一行必须满足的格式是：Dialogue: 0,0:00:00.00,0:00:09.00,Default,,0,0,0,,{xxx}string 你需要检查开头是否是Dialogue: 逗号数量是否正确，时间格式是否正确，{xxx}部分是否缺失{}。返回所有不满足的行序号。功能2“检查对应格式”：选择jp_ch.ass和jp.ass两个文件路径（设计出用户可拖拽进界面就填入路径的形式），然后逐行扫描两个文件，只有序号相同的行才会比较，忽略掉每行string部分，前面的Dialogue: 0,0:00:00.00,0:00:09.00,Default,,0,0,0,,{xxx}部分如果不一致，则返回这一行的序号，每次运行返回第一个不相同的行序号即可。功能3“新建jp_ch.ass”：选择jp.ass路径，把每一行都原封不动地复制，但删除掉每行string部分，保存到相同路径下“jp_ch.ass”。功能4“扫描已有翻译”：选择jp.ass，jp_ch.ass和hoyanku_data.csv三个文件路径，先运行功能2，如果功能2所有行相同再运行：扫描jp.ass每行，把其中的string部分提取出来在hoyanku_data中搜索，如果存在对应翻译记录，则把jp_ch.ass中相同行的string内容替换成对应的翻译，并同时记录找到有对应翻译记录时的行号，最后全部扫描完后，把行号保存在同目录的already_index_temp.txt文件里,用逗号分隔。功能5：读取already_index_temp.txt路径和jp.ass路径，把jp.ass中没在already_index_temp.txt中出现且满足Dialogue:开头的行进行扫描，提取每行的string部分，然后每个string占一行保存在同目录的need_honyaku_temp.text文件中，用于记录需要让AI翻译的内容。功能6：我会把自己用其他方式把need_honyaku_temp.text中的内容翻译好，保存到同目录的honyaku_temp.text文件中。这里选择honyaku_temp.text和already_index_temp.txt的路径，然后把honyaku_temp.text中的每行内容提取出来，逐行付给没在already_index_temp.txt中出现的jp_ch.ass行的string部分，already_index_temp.txt扫描到最后行后看对应的是否恰好是jp_ch.ass中没在already_index_temp.txt中出现的行的最后一行。是的话返回成功完成。否则弹出有错误。给我实现这些功能的完整代码
##帮我把该日文内容翻译成简体中文，注意这些来自于ニコニコ的评论，注意语言风格要符合，如果内容是常见的英文对应的假名，翻译成中文时可以直接使用英文单词，保留其他特殊字符。直接给我翻译后的中文，每行对应原日文的一行，不要出现少行、多行的情况。你经常犯一个错误，倘若连续出现相同的翻译结果，你容易缺行，请特别小心。
## 在这个基础上在扩展新加几个功能，新加功能1：把jp_ch.ass文件和jp.ass文件的文字内容合并写成中文(日文)的形式替换掉原先的每行内容，然后保存得到一个新的doublesub.ass文件在同目录。新加功能2：让用户可以输入一个压缩数值value，然后把jp_ch.ass的出现时间全部改为t*value保存为新文件jp_ch_value.ass。新加功能3(重构弹幕)重大更新：我想实现一个功能重构弹幕。读取jp_ch_value.ass先做一些统计，例如弹幕相同内容的出现总数，以及是什么时刻总数增加的（这里你根据我之后描述的功能确定怎么高效计算）。然后让所有非\move的弹幕在出现时间时从屏幕右上角同一地方高速（时间为参数可调）射进左侧（斜线移动，或者曲线，旋转等，可加入随机性），然后从屏幕左侧离开。进入的弹幕的不透明度均为0.5，然后记录那些整个时间段出现次数大于thread（默认为5）的弹幕，并让这些弹幕在出现后停留在屏幕左下方，大小和射入的弹幕大小一样（作为参数设置），固定的弹幕不透明都为1。并且每次有相同内容的弹幕出现射入，就会把这个固定的弹幕变大重新固定（100个相同的进场时为10倍大，其它以此类推），如果有多个固定弹幕，其排布规则是类似于密切堆放，互相不覆盖，从左下角往右上角延申，并且越大的弹幕约在左下方，这里的算法可能很复杂，随着加入弹幕会不断重排，你需要好好规划怎么写代码。如果空间不够，让固定堆放的弹幕可以自然溢出屏幕上方和右方。但左下角始终放此时最大的弹幕。你需要按我说的计算出新的弹幕的ass文件，并把它保存到ultra_comments.ass。给我新增加的代码部分。
# 
# 然后检测行内是否含有\move，非\move的弹幕的行除了之前的出现时间压缩外保持不变。重点是彻底改变\move的弹幕的运动逻辑。用户需要输入屏幕尺寸（默认1920x1080），初始每个轨道的高h和轨道间隔的高h0，从而计算出轨道数量。注意这些轨道数量之后会变化并且起初弹幕分配轨道的逻辑是，当轮到这个弹幕时，则选择上一个弹幕的下一个轨道进入，如果是最后一个轨道，则进入第一个轨道。，有空轨道则进入，如果都没有，则占用第一个轨道等如果含有，则把所有这样的弹幕改为以0.2秒时间从右侧滚到屏幕左侧并停留，\move的参数，例如\move(2032.5, 265, -112.5, 265)改为\move(2032.5, 265, 112.5, 265)这样的参数，即第三位数字改为正值，的弹幕的运动逻辑，让弹幕瞬间到达然后得到一个新的文件doublesub_value.ass保存在同目录下。
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
import csv
from pathlib import Path
from collections import Counter ### NEW ###: 导入Counter用于计数
import random

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

        # --- 高级功能部分 ---
        adv_func_frame = ttk.LabelFrame(self.root, text="高级功能 (Advanced Functions)")
        adv_func_frame.pack(padx=10, pady=10, fill="x")

        # --- 功能8: 合并双语 ---
        merge_frame = ttk.Frame(adv_func_frame)
        merge_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(merge_frame, text="8. 合并为双语字幕 (Merge to Bilingual)", command=self.run_merge_to_bilingual).pack(fill="x")

        # --- 功能9: 压缩时间轴 ---
        compress_frame = ttk.Frame(adv_func_frame)
        compress_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(compress_frame, text="时间缩放值 (Value):").pack(side="left", padx=5)
        self.time_scale_value = tk.StringVar(value="1.0")
        ttk.Entry(compress_frame, textvariable=self.time_scale_value, width=10).pack(side="left", padx=5)
        ttk.Button(compress_frame, text="9. 压缩/拉伸时间轴 (Compress/Stretch Timeline)", command=self.run_compress_timeline).pack(side="left", fill="x", expand=True, padx=5)

        # --- 功能10: 重构弹幕 ---
        reconstruct_frame = ttk.LabelFrame(adv_func_frame, text="10. 重构高级弹幕 (Reconstruct Advanced Danmaku)")
        reconstruct_frame.pack(fill="x", padx=5, pady=5)
        
        params_grid = ttk.Frame(reconstruct_frame)
        params_grid.pack(fill="x", pady=5)

        # 参数定义
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

        # --- 日志输出部分 (这部分是原有的，放在所有功能区之后) ---
        log_frame = ttk.LabelFrame(self.root, text="输出日志 (Output Log)")

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
    
    # --- 新增辅助方法 ---

    def _hms_to_seconds(self, time_str):
        """将 H:MM:SS.ss 格式的时间字符串转换为秒"""
        try:
            h, m, s = time_str.split(':')
            return int(h) * 3600 + int(m) * 60 + float(s)
        except Exception:
            self.log(f"警告: 无法解析时间戳 '{time_str}'，返回0。")
            return 0.0

    def _seconds_to_hms(self, seconds):
        """将秒转换为 H:MM:SS.ss 格式的字符串"""
        if seconds < 0: seconds = 0
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    def _parse_ass_header(self, lines):
        """解析ASS头部信息，获取分辨率"""
        res_x, res_y = 1920, 1080 # 默认值
        for line in lines:
            line = line.strip()
            if line.lower().startswith("playresx:"):
                try:
                    res_x = int(line.split(':')[1].strip())
                except ValueError:
                    self.log(f"警告: 无法解析 PlayResX: '{line}'")
            elif line.lower().startswith("playresy:"):
                try:
                    res_y = int(line.split(':')[1].strip())
                except ValueError:
                    self.log(f"警告: 无法解析 PlayResY: '{line}'")
            elif line.strip() == "[Events]":
                break # 事件部分开始，无需继续读取
        self.log(f"解析到屏幕分辨率: {res_x}x{res_y}")
        return res_x, res_y

    def _estimate_bbox(self, text, font_size):
        """基于字体大小和文本长度估算弹幕的边界框（宽和高）"""
        # 这是一个非常粗略的估算，实际渲染效果取决于字体
        # 假设：大多数字符宽度是字体大小的 0.6 倍
        width = int(font_size * len(text) * 0.6)
        height = int(font_size * 1.2) # 给予一些行高空间
        return width, height

    def _calculate_layout(self, comments_to_place, screen_w, screen_h):
        """
        核心布局算法：将弹幕从左下角开始进行堆叠排列
        输入: comments_to_place (一个列表，元素为 (文本, 宽度, 高度, 原始对象))
        返回: 一个字典 {文本: (x, y)}
        """
        positions = {}
        # 按弹幕高度（或面积）降序排序，大的先放
        comments_to_place.sort(key=lambda item: item[2], reverse=True)

        margin = 10  # 弹幕离屏幕边缘的距离
        spacing = 5    # 弹幕之间的间距

        cursor_x = margin
        # Y坐标从屏幕底部开始，减去行高
        cursor_y = screen_h - margin
        row_height = 0

        for text, w, h, _ in comments_to_place:
            if cursor_x + w > screen_w - margin:
                # 当前行空间不足，换行
                cursor_x = margin
                cursor_y -= (row_height + spacing)
                row_height = 0
            
            # 使用 \an7 (左下角对齐)，所以坐标就是弹幕的左下角点
            positions[text] = (cursor_x, cursor_y)
            
            cursor_x += w + spacing
            row_height = max(row_height, h)
        
        return positions

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

    # --- 新增功能实现 ---
    # --- 合并 ---
    def run_merge_to_bilingual(self):
        self.clear_log()
        self.log("--- 开始执行功能8: 合并为双语字幕 ---")
        jp_ass_file = self._get_path(self.jp_ass_path, "jp.ass")
        jp_ch_ass_file = self._get_path(self.jp_ch_ass_path, "jp_ch.ass")
        if not jp_ass_file or not jp_ch_ass_file: return
        
        output_path = jp_ass_file.with_name("doublesub.ass")

        try:
            with open(jp_ass_file, 'r', encoding='utf-8') as f_jp, \
                 open(jp_ch_ass_file, 'r', encoding='utf-8') as f_ch:
                jp_lines = f_jp.readlines()
                ch_lines = f_ch.readlines()
            
            if len(jp_lines) != len(ch_lines):
                self.log("错误: jp.ass 和 jp_ch.ass 文件行数不一致，无法合并。")
                messagebox.showerror("错误", "文件行数不一致!")
                return

            new_lines = []
            for i, jp_line in enumerate(jp_lines):
                if jp_line.strip().startswith("Dialogue:"):
                    prefix, style, jp_text = self._get_dialogue_parts(jp_line)
                    _, _, ch_text = self._get_dialogue_parts(ch_lines[i])

                    if prefix is None or ch_text is None:
                        new_lines.append(jp_line) # 如果格式有问题，保留原样
                        continue
                    
                    # 合并成 "中文(日文)" 格式
                    merged_text = f"{ch_text.strip()}({jp_text.strip()})"
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

    # --- 功能9: 压缩/拉伸时间轴 ---
    def run_compress_timeline(self):
        self.clear_log()
        self.log("--- 开始执行功能9: 压缩/拉伸时间轴 ---")
        jp_ch_ass_file = self._get_path(self.jp_ch_ass_path, "jp_ch.ass")
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

    # --- 功能10: 重构高级弹幕 (已修正版本) ---
    def run_reconstruct_danmaku(self):
        self.clear_log()
        self.log("--- 开始执行功能10: 重构高级弹幕 (v2 - 已修正时间解析) ---")
        # 使用 jp_ch_ass_path，因为通常这是经过处理的、需要重构的文件
        # 用户可以根据实际情况选择文件，这里标签只是一个提示
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
            
            # 1. 分析文件
            self.log("步骤 1/5: 分析弹幕内容和时间...")
            screen_w, screen_h = self._parse_ass_header(lines)
            header_lines = []
            dialogue_lines = []
            # 分离头部和Dialogue行
            in_events_section = False
            for l in lines:
                if l.strip() == '[Events]':
                    in_events_section = True
                if l.strip().startswith("Dialogue:") and in_events_section:
                    dialogue_lines.append(l)
                else:
                    header_lines.append(l)

            comment_data = {} # { text: {"count": N, "events": [start_time, ...]} }
            for line in dialogue_lines:
                prefix, style, text = self._get_dialogue_parts(line)
                text = text.strip()
                if not text or prefix is None or '\\move' in style: continue
                
                ### MODIFIED ###: 修正时间戳解析的索引
                # 正确的格式是: Dialogue: Layer,Start,End,Style,...
                # prefix.split(',') 后:
                # [0] = 'Dialogue: 0' (Layer)
                # [1] = '0:00:00.49'  (Start)
                # [2] = '0:00:16.48'  (End)
                # [3] = 'Default'     (Style)
                line_parts = prefix.split(',')
                if len(line_parts) < 3:
                    self.log(f"警告: 跳过格式不完整的行: {line.strip()}")
                    continue

                start_sec = self._hms_to_seconds(line_parts[1])
                # end_sec = self._hms_to_seconds(line_parts[2]) # end_sec 在此功能中非必需

                if text not in comment_data:
                    comment_data[text] = {"count": 0, "events": []}
                comment_data[text]["count"] += 1
                comment_data[text]["events"].append(start_sec)
            
            for text in comment_data:
                comment_data[text]["events"].sort()

            self.log(f"分析完成，找到 {len(comment_data)} 种不同弹幕。")
            
            # 2. 生成“飞入”弹幕
            self.log("步骤 2/5: 生成飞入弹幕效果...")
            new_dialogues = []
            for text, data in comment_data.items():
                for start_time in data["events"]:
                    end_time = start_time + move_duration
                    # 随机化Y轴，避免完全重叠
                    start_y = random.randint(0, int(screen_h * 0.6))
                    end_y = random.randint(int(screen_h * 0.2), int(screen_h * 0.8))
                    
                    move_tag = f"\\move({screen_w}, {start_y}, 0, {end_y}, 0, {int(move_duration * 1000)})"
                    style_tag = f"{{{move_tag}\\1a&H80&}}" # 半透明
                    
                    line = f"Dialogue: 0,{self._seconds_to_hms(start_time)},{self._seconds_to_hms(end_time)},Default,,0,0,0,,{style_tag}{text}\n"
                    new_dialogues.append(line)
            
            self.log(f"已生成 {len(new_dialogues)} 条飞入弹幕。")

            # 3. 识别热门弹幕并生成事件时间点
            self.log("步骤 3/5: 处理固定弹幕布局...")
            hot_comments = {t: d for t, d in comment_data.items() if d["count"] >= threshold}
            if not hot_comments:
                self.log("没有达到阈值的热门弹幕，跳过固定弹幕生成。")
            else:
                self.log(f"找到 {len(hot_comments)} 种热门弹幕。")
                
                event_times = sorted(list(set(
                    time for text in hot_comments for time in hot_comments[text]["events"]
                )))

                if not event_times:
                     self.log("热门弹幕没有有效的时间事件，跳过。")
                else:
                    event_times.append(event_times[-1] + 30) # 添加一个结束点
                    
                    # 4. 按时间间隔计算并生成“固定”弹幕
                    current_counts = Counter()
                    for i in range(len(event_times) - 1):
                        interval_start = event_times[i]
                        interval_end = event_times[i+1]
                        
                        # 更新当前时间点的弹幕计数
                        for text, data in hot_comments.items():
                            if interval_start in data["events"]:
                                current_counts[text] += data["events"].count(interval_start)
                        
                        # 准备布局计算
                        comments_to_place = []
                        for text, count in current_counts.items():
                            scale_factor = 1 + (9 * (count**0.5 / 100**0.5)) if count > 1 else 1
                            current_font_size = base_font_size * scale_factor
                            w, h = self._estimate_bbox(text, current_font_size)
                            comments_to_place.append((text, w, h, {"count": count, "scale": scale_factor}))
                        
                        if not comments_to_place: continue

                        # 执行布局
                        layout = self._calculate_layout(comments_to_place, screen_w, screen_h)
                        
                        # 生成该时间段的Dialogue行
                        for text, (x,y) in layout.items():
                            count_data = next(item[3] for item in comments_to_place if item[0] == text)
                            scale_percent = int(count_data["scale"] * 100)
                            
                            style_tag = f"\\an7\\pos({x},{y})\\fscx{scale_percent}\\fscy{scale_percent}\\fs{base_font_size}\\1a&H00&"
                            line = f"Dialogue: 1,{self._seconds_to_hms(interval_start)},{self._seconds_to_hms(interval_end)},Default,,0,0,0,,{{{style_tag}}}{text}\n"
                            new_dialogues.append(line)

            # 5. 写入最终文件
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