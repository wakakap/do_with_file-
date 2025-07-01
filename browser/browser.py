import tkinter
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageEnhance, ImageTk
import os
import sys
import re
import threading
import time
import glob
import subprocess # (新增) 导入subprocess库

try:
    import tkextrafont
except ImportError:
    messagebox.showerror("缺少庫 (Missing Library)", "需要 tkextrafont 庫來載入自訂字體。\n請執行 (Please run): pip install tkextrafont")
    sys.exit()

# --- UI佈局和尺寸配置 (UI Layout & Sizing) ---
RESIZE_DEBOUNCE_MS = 150
MANGA_CARD_MIN_WIDTH = 230
JAV_CARD_MIN_WIDTH = 380
CARD_PAD_X = 6
CARD_PAD_Y = 6
CARD_BORDER_COLOR = "#333333"
FONT_FILE_NAME = "LXGWWenKai-Light.ttf"
FONT_SIZE = 14
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.gif']

# --- 顏色主題 (Color Theme) ---
BACKGROUND_COLOR = "#242424"
TEXT_COLOR = "#FFFFFF"
BUTTON_COLOR = "#3B3B3B"
BUTTON_HOVER_COLOR = "#4A4A4A"
CARD_BACKGROUND_COLOR = "#2E2E2E"

def natural_sort_key(s):
    removal_pattern = r'\([^)]*\)|\[[^\]]*\]'
    cleaned_s = re.sub(removal_pattern, '', s)
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', cleaned_s)]

class FileSystemBrowser(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("文件系统媒体浏览器 (File System Media Browser)")
        self.after(10, lambda: self.state('zoomed'))
        ctk.set_appearance_mode("Dark")

        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        self.manga_pages_path = os.path.join(self.base_dir, "MANGA_PAGES")
        self.manga_cover_path = os.path.join(self.base_dir, "MANGA_COVER")
        self.jav_video_path = os.path.join(self.base_dir, "JAV_VIDEO")
        self.jav_cover_path = os.path.join(self.base_dir, "JAV_COVER")

        self.current_mode = "MANGA"
        self.root_path = ""
        self.cover_path = ""
        self.update_paths_for_mode()
        self.card_min_width = MANGA_CARD_MIN_WIDTH

        self.setup_font()
        self.cover_map = []
        self.load_cover_map()
        self.is_transitioning = False
        self.stagger_after_id = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, pady=(5,0), sticky="ew")
        self.mode_switch_button = ctk.CTkButton(self.header_frame, text=f"切換至 JAV 模式", width=180, command=self.switch_mode)
        self.mode_switch_button.pack(side="top")
        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.grid(row=1, column=0, padx=10, pady=(0, 0), sticky="ew")
        self.nav_frame.grid_columnconfigure(0, weight=1)
        self.current_path_label = ctk.CTkLabel(self.nav_frame, text="", font=ctk.CTkFont(size=12), text_color="#AAAAAA", anchor="w")
        self.current_path_label.pack(fill="x")
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color=BACKGROUND_COLOR)
        self.scrollable_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.open_folder_button = ctk.CTkButton(self, text="打开所在目录", width=140, command=self.open_current_directory)
        self.open_folder_button.place(relx=1.0, rely=1.0, x=-20, y=-20, anchor="se")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.after(100, self.initialize_browser)
        self.bind_global_right_click()
    
    def open_current_directory(self):
        if not self.path_stack: return
        current_path = self.path_stack[-1]
        if not os.path.isdir(current_path):
            current_path = os.path.dirname(current_path)
        try:
            if sys.platform == "win32": os.startfile(current_path)
            elif sys.platform == "darwin": subprocess.call(["open", current_path])
            else: subprocess.call(["xdg-open", current_path])
        except Exception as e:
            messagebox.showerror("打开失败", f"无法打开文件夹: {current_path}\n错误: {e}")

    def browse_to(self, path):
        if self.is_transitioning: return
        self.is_transitioning = True
        if self.stagger_after_id: self.after_cancel(self.stagger_after_id); self.stagger_after_id = None
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        loading_label = ctk.CTkLabel(self.scrollable_frame, text="正在加载...", font=self.display_font, text_color=TEXT_COLOR)
        loading_label.pack(pady=50)
        def _prepare_data_and_load():
            try: items = sorted(os.listdir(path), key=natural_sort_key)
            except FileNotFoundError:
                messagebox.showerror("错误", f"路径不存在或无法访问: {path}")
                self.after(0, self.go_back)
                return
            self.after(0, lambda: loading_label.destroy())
            self.after(0, lambda: self._load_cards_staggered(path, items, 0))
        threading.Thread(target=_prepare_data_and_load, daemon=True).start()

    def _load_cards_staggered(self, path, items, index):
        if index >= len(items):
            self.is_transitioning = False
            self.stagger_after_id = None
            return
        num_columns = max(1, (self.winfo_width() - 40) // (self.card_min_width + CARD_PAD_X * 2))
        row, col = index // num_columns, index % num_columns
        item_name = items[index]
        full_path = os.path.join(path, item_name)
        self.create_browser_card(self.scrollable_frame, full_path).grid(row=row, column=col, padx=CARD_PAD_X, pady=CARD_PAD_Y, sticky="ns")
        self.stagger_after_id = self.after(30, lambda: self._load_cards_staggered(path, items, index + 1))

    def handle_left_click(self, path, is_dir, is_special):
        if self.is_transitioning: return
        if is_special:
            # --- (核心修改处) ---
            image_files = sorted(
                [f for f in os.listdir(path) if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS],
                key=natural_sort_key # 使用新的排序规则
            )
            # --- (修改结束) ---
            if image_files: ImageReader(self, path, image_files, os.path.basename(path))
            else: messagebox.showwarning("空文件夹", "这个特殊的图片文件夹是空的。")
        elif is_dir:
            self.path_stack.append(path)
            display_path = f"模式: {self.current_mode} | " + os.path.relpath(path, self.base_dir)
            self.current_path_label.configure(text=display_path)
            self.browse_to(path)
        else:
            try: os.startfile(path)
            except Exception as e: messagebox.showerror("打开失败", f"无法打开文件: {path}\n错误: {e}")

    def go_back(self):
        if self.is_transitioning: return
        if len(self.path_stack) > 1:
            self.path_stack.pop()
            path = self.path_stack[-1]
            display_path = f"模式: {self.current_mode} | " + os.path.relpath(path, self.base_dir)
            self.current_path_label.configure(text=display_path)
            self.browse_to(path)
            
    def switch_mode(self):
        if self.is_transitioning: return
        if self.current_mode == "MANGA":
            self.current_mode = "JAV"
            self.mode_switch_button.configure(text="切換至 MANGA 模式")
            self.card_min_width = JAV_CARD_MIN_WIDTH
        else:
            self.current_mode = "MANGA"
            self.mode_switch_button.configure(text="切換至 JAV 模式")
            self.card_min_width = MANGA_CARD_MIN_WIDTH
        self.update_paths_for_mode()
        self.initialize_browser()

    def initialize_browser(self):
        self.load_cover_map()
        path = self.root_path
        display_path = f"模式: {self.current_mode} | " + os.path.relpath(path, self.base_dir)
        self.current_path_label.configure(text=display_path)
        self.browse_to(path)

    def find_cover(self, base_name):
        if not os.path.isdir(self.cover_path): return None
        for regex_obj, cover_regex_template in self.cover_map:
            match_left = regex_obj.match(base_name)
            if match_left:
                try:
                    captured_vars = match_left.groupdict()
                    escaped_vars = {k: re.escape(v) for k, v in captured_vars.items()}
                    final_cover_regex_str = cover_regex_template.format(**escaped_vars)
                    final_cover_regex_obj = re.compile(f"^{final_cover_regex_str}$", re.IGNORECASE)
                    found_covers = []
                    for cover_filename in os.listdir(self.cover_path):
                        cover_base, cover_ext = os.path.splitext(cover_filename)
                        if cover_ext.lower() not in IMAGE_EXTENSIONS: continue
                        if final_cover_regex_obj.match(cover_base):
                            found_covers.append(os.path.join(self.cover_path, cover_filename))
                    if len(found_covers) == 1: return found_covers[0]
                    elif len(found_covers) > 1:
                        file_list = "\n - ".join(os.path.basename(p) for p in found_covers)
                        messagebox.showerror("封面匹配歧义", f"为 '{base_name}' 查找封面时出现问题。\n\n" f"使用的规则 '{cover_regex_template}' 匹配到了多个文件：\n - {file_list}\n\n" "请检查您的封面文件命名或修改 map.txt 规则以确保唯一性。")
                        return None
                except (KeyError, re.error) as e:
                    print(f"map.txt 规则处理错误: {e}")
                    continue
        for ext in IMAGE_EXTENSIONS:
            potential_cover = os.path.join(self.cover_path, base_name + ext)
            if os.path.exists(potential_cover): return potential_cover
        return None

    def create_browser_card(self, parent, full_path):
        item_name = os.path.basename(full_path)
        name_no_ext, _ = os.path.splitext(item_name)
        is_dir = os.path.isdir(full_path)
        is_special_dir = is_dir and item_name.endswith('_')
        card_frame = ctk.CTkFrame(parent, fg_color=CARD_BACKGROUND_COLOR, border_color=CARD_BORDER_COLOR, border_width=1)
        card_frame.grid_columnconfigure(0, weight=1)
        cover_image_path = self.find_cover(name_no_ext)
        photo = None
        if cover_image_path:
            try:
                if self.current_mode == 'JAV': aspect_ratio = 538 / 800
                else: aspect_ratio = 3 / 2
                img_w, img_h = self.card_min_width - 10, int((self.card_min_width - 10) * aspect_ratio)
                pil_image = Image.open(cover_image_path)
                resized_pil_image = pil_image.resize((img_w, img_h), Image.Resampling.LANCZOS)
                photo = ctk.CTkImage(light_image=resized_pil_image, size=(img_w, img_h))
            except Exception as e: print(f"无法加载或处理封面图: {cover_image_path}\n错误: {e}"); pass
        if photo:
            image_label = ctk.CTkLabel(card_frame, text="", image=photo)
            image_label.grid(row=0, column=0, padx=5, pady=5)
        else:
            text_placeholder = ctk.CTkLabel(card_frame, text=name_no_ext, wraplength=self.card_min_width - 20, font=self.display_font, height=int((self.card_min_width - 10) * (3/2)), fg_color="#1E1E1E")
            text_placeholder.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        display_name = "📁 " + name_no_ext if is_dir else "📄 " + name_no_ext
        filename_label = ctk.CTkLabel(card_frame, text=display_name, wraplength=self.card_min_width - 20, justify=tkinter.LEFT, font=self.display_font, text_color=TEXT_COLOR)
        filename_label.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="w")
        callback_back = lambda event: self.go_back()
        for widget in card_frame.winfo_children() + [card_frame]:
            widget.bind("<Button-1>", lambda e, p=full_path, d=is_dir, s=is_special_dir: self.handle_left_click(p, d, s))
            widget.bind("<Button-3>", callback_back)
        return card_frame

    def load_cover_map(self):
        self.cover_map = []
        map_path = os.path.join(self.base_dir, "map.txt")
        if not os.path.exists(map_path): return
        try:
            with open(map_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#') or ',' not in line: continue
                    parts = line.split(',', 1)
                    source_regex_str, cover_template_str = parts[0].strip(), parts[1].strip()
                    try:
                        full_regex_str = f"^{source_regex_str}$"
                        regex_obj = re.compile(full_regex_str, re.IGNORECASE)
                        self.cover_map.append((regex_obj, cover_template_str))
                    except re.error as e: print(f"警告: map.txt 第 {i} 行存在无效的正则表达式: {source_regex_str}\n错误: {e}")
        except Exception as e: print(f"读取 map.txt 文件失败: {e}")

    def bind_global_right_click(self):
        callback = lambda event: self.go_back()
        self.bind("<Button-3>", callback)
        self.header_frame.bind("<Button-3>", callback)
        self.nav_frame.bind("<Button-3>", callback)
        self.current_path_label.bind("<Button-3>", callback)
        self.mode_switch_button.bind("<Button-3>", callback)
        self.scrollable_frame.bind("<Button-3>", callback)

    def update_paths_for_mode(self):
        if self.current_mode == "MANGA": self.root_path, self.cover_path = self.manga_pages_path, self.manga_cover_path
        else: self.root_path, self.cover_path = self.jav_video_path, self.jav_cover_path
        self.path_stack = [self.root_path]

    def on_closing(self):
        if messagebox.askokcancel("退出程序", "您确定要关闭浏览器吗？"): self.destroy()

    def setup_font(self):
        font_path = os.path.join(self.base_dir, FONT_FILE_NAME)
        try:
            if not os.path.exists(font_path): raise FileNotFoundError
            unique_font_family = f"AppFont-{id(self)}"; tkextrafont.Font(file=font_path, family=unique_font_family)
            self.display_font = ctk.CTkFont(family=unique_font_family, size=FONT_SIZE)
        except Exception: print("自定义字体加载失败，使用默认字体。"); self.display_font = ctk.CTkFont(size=FONT_SIZE)

    def center_toplevel(self, top):
        top.update_idletasks(); w,h = top.winfo_width(), top.winfo_height(); sw,sh = top.winfo_screenwidth(), top.winfo_screenheight()
        x,y = (sw - w) // 2, (sh - h) // 2; top.geometry(f"{w}x{h}+{x}+{y}")


class ImageReader(ctk.CTkToplevel):
    def __init__(self, master, pages_dir, image_files, title):
        super().__init__(master)
        self.title(title)
        self.state('zoomed')
        self.configure(fg_color=BACKGROUND_COLOR)
        self.grab_set()
        self.update_idletasks()

        self.pages_dir = pages_dir
        self.image_files = image_files
        self.current_page_index = 0
        
        self.initial_load_done = False
        self.progress_bar_populated = False # (新增) 确保进度条只被创建一次

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self.image_label = ctk.CTkLabel(self, text="正在准备图片...", fg_color=BACKGROUND_COLOR, font=master.display_font)
        self.image_label.grid(row=0, column=0, sticky="nsew")
        
        self.page_segments = []
        self.progress_color = "#3B8ED0"
        self.progress_bg_color = "#555555"

        self.progress_bar_frame = ctk.CTkFrame(
            self,
            width = 40,
            fg_color="transparent"
        )
        self.progress_bar_frame.grid_propagate(False)
        self.progress_bar_frame.grid(row=0, column=1, sticky="ns", padx=(5, 10), pady=10)
        
        # --- (核心修改 2) 绑定Configure事件，以便在获得尺寸后才创建进度条 ---
        self.progress_bar_frame.bind("<Configure>", self._populate_progress_bar)

        self.is_fading = False
        self.next_image_data = None
        self.current_pil_image = None
        self.fade_after_id = None
        
        self.image_label.bind("<Button-1>", self.handle_click)
        self.image_label.bind("<Button-3>", self.handle_click)
        
        self.after(20, self.load_initial_page)

    def _populate_progress_bar(self, event):
        """(新增) 在容器尺寸确定后，创建并填充进度条的线段。"""
        if self.progress_bar_populated or not self.image_files:
            return
        
        self.progress_bar_populated = True
        
        # 获取容器的实际高度
        container_height = self.progress_bar_frame.winfo_height()
        num_pages = len(self.image_files)
        
        # (核心修改 3) 手动计算每个线段的高度
        # 为了留出间隙，我们从总高度里减去 (页数-1) * 1像素的间隙高度
        total_padding = (num_pages - 1) * 1 # pady=0.5 上下各有
        segment_height = (container_height - total_padding) / num_pages
        segment_height = max(1, segment_height) # 确保最小高度为1

        self.progress_bar_frame.grid_columnconfigure(0, weight=0)
        self.progress_bar_frame.grid_columnconfigure(1, weight=1)

        for i in range(num_pages):
            # 为每一行设置权重，让标签和线段在垂直方向上居中
            self.progress_bar_frame.grid_rowconfigure(i, weight=1)

            if (i + 1) % 10 == 0 or i == 0:
                num_label = ctk.CTkLabel(
                    self.progress_bar_frame, text=str(i + 1), font=ctk.CTkFont(size=10), text_color="#FFFFFF"
                )
                num_label.grid(row=i, column=0, sticky="e", padx=(0, 4))

            segment = ctk.CTkFrame(
                self.progress_bar_frame,
                height=segment_height, # 使用计算出的高度
                fg_color=self.progress_bg_color, corner_radius=2
            )
            segment.grid(row=i, column=1, sticky="ew", pady=0.5) # 使用0.5的pady制造1像素的间隙
            segment.bind("<Button-1>", lambda event, index=i: self.go_to_page(index))
            self.page_segments.append(segment)
        
        # 创建完成后，立即根据当前页码更新一次颜色
        self._update_progress_bar_colors()

    def _update_progress_bar_colors(self):
        """根据当前页码更新所有线段的颜色。"""
        for i, segment in enumerate(self.page_segments):
            if i <= self.current_page_index:
                segment.configure(fg_color=self.progress_color)
            else:
                segment.configure(fg_color=self.progress_bg_color)

    def go_to_page(self, page_index):
        """当点击进度条线段时，调用统一的过渡动画函数。"""
        if self.is_fading or not self.initial_load_done or page_index == self.current_page_index:
            return
        self._transition_to_page(page_index)

    def load_initial_page(self):
        if not self.initial_load_done:
            self.initial_load_done = True
            self._load_and_display_sync(self.current_page_index)
            self._update_progress_bar_colors()

    def handle_click(self, event):
        """点击图片翻页时，也调用统一的过渡动画函数。"""
        if self.is_fading or not self.initial_load_done: return
        target_index = -1
        if event.num == 1 and self.current_page_index < len(self.image_files) - 1:
            target_index = self.current_page_index + 1
        elif event.num == 3 and self.current_page_index > 0:
            target_index = self.current_page_index - 1
        if target_index != -1:
            self._transition_to_page(target_index)

    def _transition_to_page(self, target_index):
        """统一的页面切换过渡函数。"""
        self.is_fading = True
        self.next_image_data = None
        threading.Thread(target=self._load_image_in_background, args=(target_index,), daemon=True).start()
        self._fade_out_animation()
        self._check_for_loaded_image(target_index)

    def _load_image_in_background(self, index_to_load):
        try:
            img_path = os.path.join(self.pages_dir, self.image_files[index_to_load])
            canvas_w, canvas_h = self.winfo_screenwidth(), self.winfo_screenheight()
            padding = 40
            img = Image.open(img_path).convert("RGBA")
            img.thumbnail((canvas_w - padding, canvas_h - padding), Image.Resampling.LANCZOS)
            self.next_image_data = img
        except Exception as e:
            print(f"Error in background loading: {e}"); self.next_image_data = "error"

    def _check_for_loaded_image(self, target_index):
        if self.next_image_data is not None:
            if self.fade_after_id: self.after_cancel(self.fade_after_id); self.fade_after_id = None
            if self.next_image_data == "error":
                self.image_label.configure(text=f"无法载入图片:\n{os.path.basename(self.image_files[target_index])}", image=None)
            else:
                self.current_page_index = target_index
                self._display_image(self.next_image_data)
                self._update_progress_bar_colors()
            self.is_fading = False
        elif self.is_fading: self.after(20, lambda: self._check_for_loaded_image(target_index))

    def _fade_out_animation(self, start_time=None, duration=0.5):
        if start_time is None: start_time = time.time()
        elapsed = time.time() - start_time; progress = min(elapsed / duration, 1.0)
        current_alpha = int(255 - (255 - 77) * progress)
        if self.current_pil_image:
            temp_img = self.current_pil_image.copy(); temp_img.putalpha(current_alpha)
            ctk_image = ctk.CTkImage(light_image=temp_img, size=temp_img.size)
            self.image_label.configure(image=ctk_image)
        if progress < 1.0: self.fade_after_id = self.after(15, lambda: self._fade_out_animation(start_time, duration))
        else: self.fade_after_id = None

    def _load_and_display_sync(self, index):
        """同步加载，用于初始加载或需要即时响应的跳转。"""
        try:
            img_path = os.path.join(self.pages_dir, self.image_files[index])
            canvas_w, canvas_h = self.winfo_screenwidth(), self.winfo_screenheight()
            padding = 40
            if canvas_w < 50 or canvas_h < 50: canvas_w, canvas_h = 1280, 900
            img = Image.open(img_path).convert("RGBA"); img.thumbnail((canvas_w - padding, canvas_h - padding), Image.Resampling.LANCZOS)
            self._display_image(img)
        except Exception as e:
            print(f"Error loading initial image: {e}"); self.image_label.configure(text=f"无法载入图片:\n{os.path.basename(self.image_files[index])}", image=None)
            
    def _display_image(self, pil_image):
        self.current_pil_image = pil_image
        ctk_image = ctk.CTkImage(light_image=self.current_pil_image, size=self.current_pil_image.size)
        self.image_label.configure(text="", image=ctk_image)

if __name__ == "__main__":
    app = FileSystemBrowser()
    app.mainloop()