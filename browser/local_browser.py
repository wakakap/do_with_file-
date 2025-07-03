import tkinter
import customtkinter as ctk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageEnhance, ImageTk
import os
import sys
import re
import threading
import time
import subprocess
import json
import shutil

try:
    import tkextrafont
except ImportError:
    messagebox.showerror("缺少庫 (Missing Library)", "需要 tkextrafont 庫来載入自訂字體。\n請執行 (Please run): pip install tkextrafont")
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
TAGS_X_PADDING = 7

# --- 顏色主題 (Color Theme) ---
BACKGROUND_COLOR = "#242424"
TEXT_COLOR = "#FFFFFF"
BUTTON_COLOR = "#3B3B3B"
BUTTON_HOVER_COLOR = "#888888"
CARD_BACKGROUND_COLOR = "#494141"
LABEL_START_COLOR = (95,15,64)  # 深橙色 (Dark Orange)
LABEL_END_COLOR = (220,47,2)  # 浅橙色 (Light Orange)

def natural_sort_key(s):
    removal_pattern = r'\([^)]*\)|\[[^\]]*\]'
    cleaned_s = re.sub(removal_pattern, '', s)
    match = re.search(r'\d+', cleaned_s)
    if not match:
        return (cleaned_s.strip().lower(), 0)
    else:
        text_part = cleaned_s[:match.start()].strip().lower()
        num_part = int(match.group(0))
        return (text_part, num_part)

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
        self.in_search_mode = False

        self.tags_file_path = os.path.join(self.base_dir, "tags.json")
        self.tags_data = {}
        self.temp_tags_data = {}
        self.in_tag_edit_mode = False
        self.load_tags()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)

        self.header_container = ctk.CTkFrame(self, fg_color="transparent")
        self.header_container.grid(row=0, column=0, pady=(5,0), sticky="ew")
        self.header_container.grid_columnconfigure(0, weight=1)
        self.header_container.grid_columnconfigure(1, weight=0)

        self.header_frame = ctk.CTkFrame(self.header_container, fg_color="transparent")
        self.header_frame.grid(row=0, column=0)

        self.mode_switch_button = ctk.CTkButton(self.header_frame, text=f"切换至 JAV 模式", width=180, command=self.switch_mode)
        self.mode_switch_button.pack(side="left", padx=5)
        
        self.search_entry = ctk.CTkEntry(self.header_frame, placeholder_text="输入关键词搜索...", font=self.display_font, width=300)
        self.search_entry.pack(side="left", padx=5)
        
        self.search_button = ctk.CTkButton(self.header_frame, text="搜索", width=80, command=self.perform_search)
        self.search_button.pack(side="left", padx=5)
        
        self.search_entry.bind("<Return>", lambda event: self.perform_search())
        
        self.maintenance_controls_frame = ctk.CTkFrame(self.header_container, fg_color="transparent")
        self.maintenance_controls_frame.grid(row=0, column=1, sticky="e", padx=(0, 20))

        self.maintenance_button = ctk.CTkButton(self.maintenance_controls_frame, text="维护", width=80, command=self.toggle_maintenance_menu)
        self.maintenance_button.pack()
        self.default_button_color = self.maintenance_button.cget("fg_color")
        self.default_button_hover_color = self.maintenance_button.cget("hover_color")
        
        self.maintenance_menu = ctk.CTkFrame(self, fg_color=CARD_BACKGROUND_COLOR, border_color=CARD_BORDER_COLOR, border_width=1)
        gen_covers_button = ctk.CTkButton(self.maintenance_menu, text="生成封面", command=self.generate_covers)
        gen_covers_button.pack(fill="x", padx=5, pady=(5, 2))
        edit_tags_button = ctk.CTkButton(self.maintenance_menu, text="编辑Tag", command=self.enter_tag_edit_mode)
        edit_tags_button.pack(fill="x", padx=5, pady=2)

        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.grid(row=1, column=0, padx=10, pady=(5, 0), sticky="ew")
        self.current_path_label = ctk.CTkLabel(self.nav_frame, text="", font=ctk.CTkFont(size=12), text_color="#AAAAAA", anchor="w")
        self.current_path_label.pack(fill="x")
        
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color=BACKGROUND_COLOR)
        self.scrollable_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        
        self.open_folder_button = ctk.CTkButton(self, text="打开所在目录", width=140, command=self.open_current_directory)
        self.open_folder_button.place(relx=1.0, rely=1.0, x=-20, y=-20, anchor="se")
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.after(100, self.initialize_browser)
        self.bind_global_right_click()

    def toggle_maintenance_menu(self):
        if self.maintenance_menu.winfo_viewable():
            self.maintenance_menu.place_forget()
            if self.in_tag_edit_mode:
                self.prompt_save_tags_on_exit()
        else:
            # 使用 "winfo_reqwidth()" 来获取菜单所需的宽度，这个方法比 "winfo_width()" 更可靠
            menu_width = self.maintenance_menu.winfo_reqwidth()
            
            # 获取按钮的位置和尺寸信息
            button_x = self.maintenance_button.winfo_rootx()
            button_y = self.maintenance_button.winfo_rooty()
            button_height = self.maintenance_button.winfo_height()
            button_width = self.maintenance_button.winfo_width()

            # 计算菜单的x, y坐标，使其右侧与按钮的右侧对齐
            x = button_x - menu_width + button_width
            y = button_y + button_height

            self.maintenance_menu.place(x=x, y=y)
            self.maintenance_menu.lift()

    def hide_maintenance_menu(self, event=None):
        if self.maintenance_menu.winfo_viewable():
            mx, my = self.maintenance_menu.winfo_rootx(), self.maintenance_menu.winfo_rooty()
            mw, mh = self.maintenance_menu.winfo_width(), self.maintenance_menu.winfo_height()
            px, py = self.winfo_pointerxy()
            if not (mx < px < mx + mw and my < py < my + mh):
                self.toggle_maintenance_menu()

    def generate_covers(self):
        self.toggle_maintenance_menu()
        if self.is_transitioning:
            messagebox.showwarning("请稍候", "正在加载数据，请稍后再试。")
            return

        current_browse_path = self.path_stack[-1]
        
        if not os.path.isdir(current_browse_path):
            messagebox.showerror("错误", "当前的路径不是一个有效的文件夹。")
            return

        loading_label = ctk.CTkLabel(self, text="正在生成封面，请稍候...", font=self.display_font, fg_color=BACKGROUND_COLOR, corner_radius=10)
        loading_label.place(relx=0.5, rely=0.5, anchor="center")
        self.update_idletasks()

        threading.Thread(target=self._generate_covers_worker, args=(current_browse_path, loading_label), daemon=True).start()

    def _generate_covers_worker(self, path_to_scan, loading_label):
        temp_cover_path = os.path.join(self.cover_path, "temp_generated_covers")
        os.makedirs(temp_cover_path, exist_ok=True)
        generated_count = 0
        
        for root, dirs, _ in os.walk(path_to_scan):
            for dir_name in list(dirs):
                if not dir_name.endswith('_'):
                    continue
                
                dirs.remove(dir_name)
                
                base_name = dir_name[:-1]
                if self.find_cover(base_name) is None:
                    special_dir_path = os.path.join(root, dir_name)
                    try:
                        images = sorted(
                            [f for f in os.listdir(special_dir_path) if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS],
                            key=natural_sort_key
                        )
                        if images:
                            first_image_name = images[0]
                            source_file = os.path.join(special_dir_path, first_image_name)
                            ext = os.path.splitext(first_image_name)[1]
                            dest_file = os.path.join(temp_cover_path, f"{base_name}{ext}")
                            shutil.copy2(source_file, dest_file)
                            generated_count += 1
                    except Exception as e:
                        print(f"处理文件夹 '{special_dir_path}' 时出错: {e}")
        
        self.after(0, loading_label.destroy)
        self.after(10, lambda: messagebox.showinfo("操作完成", f"成功生成 {generated_count} 个新封面。\n它们已放置在以下临时文件夹中：\n{temp_cover_path}\n\n请手动检查并将其移动到主封面目录。"))

    def enter_tag_edit_mode(self):
        self.toggle_maintenance_menu()
        if self.is_transitioning: return
        self.in_tag_edit_mode = True
        self.temp_tags_data = json.loads(json.dumps(self.tags_data))
        self.maintenance_button.configure(text="保存Tag", fg_color="red", hover_color="#C00000", command=self.prompt_save_tags_on_exit)
        self.refresh_current_view()
        
    def exit_tag_edit_mode(self, save=False):
        if save:
            self.save_tags()
        self.in_tag_edit_mode = False
        self.temp_tags_data = {}
        self.maintenance_button.configure(text="维护",fg_color=self.default_button_color, hover_color=self.default_button_hover_color, command=self.toggle_maintenance_menu)
        self.refresh_current_view()

    def prompt_save_tags_on_exit(self):
        if self.tags_data == self.temp_tags_data:
            self.exit_tag_edit_mode(save=False)
            return

        answer = messagebox.askyesnocancel("保存更改", "您想要保存对Tag的修改吗？")
        if answer is True:
            self.exit_tag_edit_mode(save=True)
        elif answer is False:
            self.exit_tag_edit_mode(save=False)

    def refresh_current_view(self):
        if self.in_search_mode:
            # 如果在搜索模式下刷新，最好是退回到之前的目录
            self.go_back()
        else:
            self.browse_to(self.path_stack[-1])

    def load_tags(self):
        try:
            if os.path.exists(self.tags_file_path):
                with open(self.tags_file_path, 'r', encoding='utf-8') as f:
                    self.tags_data = json.load(f)
            else:
                self.tags_data = {}
        except (json.JSONDecodeError, IOError) as e:
            messagebox.showerror("Tag加载失败", f"无法读取 'tags.json': {e}")
            self.tags_data = {}

    def save_tags(self):
        # --- 新增的排序逻辑开始 ---
        tag_counts = {}
        for tags_list in self.temp_tags_data.values():
            for tag in tags_list:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        sorted_global_tags = sorted(tag_counts.keys(), key=lambda tag: (tag_counts[tag], tag), reverse=True)
        # 索引越小，代表tag越常用
        tag_order_map = {tag: i for i, tag in enumerate(sorted_global_tags)}
        sorted_temp_tags_data = {}
        for item_key, tags_list in self.temp_tags_data.items():
            sorted_tags_for_item = sorted(tags_list, key=lambda tag: tag_order_map.get(tag, 9999)) # 使用 .get 防止新加的tag不在map中
            sorted_temp_tags_data[item_key] = sorted_tags_for_item
        try:
            with open(self.tags_file_path, 'w', encoding='utf-8') as f:
                json.dump(sorted_temp_tags_data, f, indent=4, ensure_ascii=False)
            self.tags_data = sorted_temp_tags_data
            messagebox.showinfo("成功", "Tag已成功保存并排序。")

        except IOError as e:
            messagebox.showerror("Tag保存失败", f"无法写入 'tags.json': {e}")

    def update_card_tags_display(self, tags_frame, item_key):
        for widget in tags_frame.winfo_children():
            widget.destroy()

        available_width = self.card_min_width - 26
        x_cursor, y_cursor = 0, 0
        line_height = 24
        x_padding = TAGS_X_PADDING

        tags = self.temp_tags_data.get(item_key, []) if self.in_tag_edit_mode else self.tags_data.get(item_key, [])
        widgets_to_place = []

        if self.in_tag_edit_mode:
            for tag in tags:
                tag_unit_frame = ctk.CTkFrame(tags_frame, fg_color="transparent")
                tag_label = ctk.CTkLabel(tag_unit_frame, text=tag, font=(self.display_font.cget("family"), FONT_SIZE-2), fg_color="#555555", corner_radius=5, padx=4)
                tag_label.pack(side="left")
                del_button = ctk.CTkButton(tag_unit_frame, text="x", width=16, height=16, fg_color="#C00000", hover_color="red", command=lambda k=item_key, t=tag, f=tags_frame: self.delete_tag(k, t, f))
                del_button.pack(side="left", padx=(1,0))
                widgets_to_place.append(tag_unit_frame)
        else:
            start_rgb = LABEL_START_COLOR
            end_rgb = LABEL_END_COLOR
            num_tags = len(tags)

            for i, tag in enumerate(tags):
                if num_tags > 1:
                    ratio = i / (num_tags - 1)
                else:
                    ratio = 0

                r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
                g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
                b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
                hex_color = f'#{r:02x}{g:02x}{b:02x}'

                tag_label = ctk.CTkLabel(tags_frame, text=tag, font=(self.display_font.cget("family"), FONT_SIZE-2), fg_color=hex_color, corner_radius=5, padx=4)
                tag_label.bind("<Button-1>", lambda e, t=tag: self.perform_tag_search(t))
                widgets_to_place.append(tag_label)

        if self.in_tag_edit_mode:
            add_button = ctk.CTkButton(tags_frame, text="+", width=20, height=20, command=lambda k=item_key, f=tags_frame: self.add_tag(k, f))
            widgets_to_place.append(add_button)

        for widget in widgets_to_place:
            widget.update_idletasks()
            widget_width = widget.winfo_reqwidth()
            if x_cursor > 0 and x_cursor + widget_width > available_width:
                x_cursor, y_cursor = 0, y_cursor + line_height
            widget.place(x=x_cursor, y=y_cursor)
            x_cursor += widget_width + x_padding

        final_height = y_cursor + line_height if widgets_to_place else 1
        tags_frame.configure(height=final_height)

    def add_tag(self, item_key, tags_frame):
        dialog = ctk.CTkInputDialog(text="输入新Tag:", title="添加Tag")
        new_tag = dialog.get_input()

        if new_tag and new_tag.strip():
            new_tag = new_tag.strip()
            if item_key not in self.temp_tags_data: self.temp_tags_data[item_key] = []
            if new_tag not in self.temp_tags_data[item_key]:
                self.temp_tags_data[item_key].append(new_tag)
                self.update_card_tags_display(tags_frame, item_key)
            else: messagebox.showwarning("重复", f"Tag '{new_tag}' 已存在。")

    def delete_tag(self, item_key, tag, tags_frame):
        if item_key in self.temp_tags_data and tag in self.temp_tags_data[item_key]:
            self.temp_tags_data[item_key].remove(tag)
            if not self.temp_tags_data[item_key]: del self.temp_tags_data[item_key]
            self.update_card_tags_display(tags_frame, item_key)

    def perform_search(self):
        if self.is_transitioning: return
        keyword = self.search_entry.get().strip()
        if not keyword:
            if self.in_search_mode: self.browse_to(self.path_stack[-1])
            return
        
        self.is_transitioning, self.in_search_mode = True, True
        if self.stagger_after_id: self.after_cancel(self.stagger_after_id)
        self.stagger_after_id = None
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        
        loading_label = ctk.CTkLabel(self.scrollable_frame, text=f"正在搜索 \"{keyword}\"...", font=self.display_font, text_color=TEXT_COLOR)
        loading_label.pack(pady=50)
        self.current_path_label.configure(text=f"搜索结果: \"{keyword}\"")

        threading.Thread(target=self._search_worker, args=(keyword, loading_label), daemon=True).start()

    def _search_worker(self, keyword, loading_label):
        """
        在后台执行搜索操作。
        新逻辑: 同时搜索文件名和项目的Tag。
        """
        keyword_lower = keyword.lower()
        found_paths = set()  # 使用集合来自动处理重复项（例如文件名和Tag同时匹配的情况）

        # 遍历根目录下的所有文件和文件夹
        for root, dirs, files in os.walk(self.root_path):
            # 将当前目录中的文件夹和文件合并进行统一处理
            all_items = dirs + files
            
            for item_name in all_items:
                # 检查1: 关键词是否在文件名中
                if keyword_lower in item_name.lower():
                    found_paths.add(os.path.join(root, item_name))
                    continue  # 匹配成功，无需再检查Tag，直接处理下一个项目

                # 检查2: 如果文件名不匹配，则检查其关联的Tag
                item_key, _ = os.path.splitext(item_name)
                # 使用 .get() 安全地获取Tag列表，如果项目没有Tag则返回空列表
                item_tags = self.tags_data.get(item_key, [])
                for tag in item_tags:
                    if keyword_lower in tag.lower():
                        found_paths.add(os.path.join(root, item_name))
                        break  # Tag匹配成功，无需再检查此项目的其他Tag，跳出Tag循环

            # 从遍历列表中移除特殊文件夹"_"，防止进入其内部
            dirs[:] = [d for d in dirs if not d.endswith('_')]

        # 将集合转换为列表并进行自然排序
        sorted_results = sorted(list(found_paths), key=lambda path: natural_sort_key(os.path.basename(path)))
        
        # 在主线程中更新UI
        self.after(0, loading_label.destroy)
        
        # 如果没有找到任何结果，则显示提示信息
        if not sorted_results:
             no_results_label = ctk.CTkLabel(self.scrollable_frame, text=f"未找到与 \"{keyword}\" 相关的项目。", font=self.display_font)
             self.after(0, lambda: no_results_label.pack(pady=50))
             self.after(10, self.set_transition_false) # 确保UI状态被重置
        else:
             self.after(0, self._load_cards_staggered, sorted_results, 0)

    # --- 新增功能: Tag搜索 ---
    def perform_tag_search(self, tag_name):
        if self.is_transitioning: return
        self.is_transitioning, self.in_search_mode = True, True
        if self.stagger_after_id: self.after_cancel(self.stagger_after_id)
        self.stagger_after_id = None
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()

        loading_label = ctk.CTkLabel(self.scrollable_frame, text=f"正在按 Tag \"{tag_name}\" 搜索...", font=self.display_font, text_color=TEXT_COLOR)
        loading_label.pack(pady=50)
        self.current_path_label.configure(text=f"Tag 搜索结果: \"{tag_name}\"")
        threading.Thread(target=self._tag_search_worker, args=(tag_name, loading_label), daemon=True).start()

    def _tag_search_worker(self, tag_name, loading_label):
        tagged_item_keys = {key for key, tags in self.tags_data.items() if tag_name in tags}
        if not tagged_item_keys:
            self.after(0, loading_label.destroy)
            no_results_label = ctk.CTkLabel(self.scrollable_frame, text=f"未找到带有 Tag \"{tag_name}\" 的项目。", font=self.display_font)
            self.after(0, lambda: no_results_label.pack(pady=50))
            self.after(10, self.set_transition_false)
            return

        found_paths = []
        for root, dirs, files in os.walk(self.root_path):
            all_items = dirs + files
            for item_name in all_items:
                item_key, _ = os.path.splitext(item_name)
                if item_key in tagged_item_keys:
                    found_paths.append(os.path.join(root, item_name))
            dirs[:] = [d for d in dirs if not d.endswith('_')]
        
        sorted_results = sorted(list(set(found_paths)), key=lambda path: natural_sort_key(os.path.basename(path)))
        self.after(0, loading_label.destroy)
        self.after(0, self._load_cards_staggered, sorted_results, 0)

    def set_transition_false(self):
        self.is_transitioning = False

    def _load_cards_staggered(self, full_path_list, index):
        if index >= len(full_path_list) or not self.is_transitioning:
            self.is_transitioning, self.stagger_after_id = False, None
            return
        
        num_columns = max(1, (self.winfo_width() - 40) // (self.card_min_width + CARD_PAD_X * 2))
        row, col = index // num_columns, index % num_columns
        self.create_browser_card(self.scrollable_frame, full_path_list[index]).grid(row=row, column=col, padx=CARD_PAD_X, pady=CARD_PAD_Y, sticky="ns")
        self.stagger_after_id = self.after(10, self._load_cards_staggered, full_path_list, index + 1)
    
    def browse_to(self, path):
        if self.is_transitioning: return
        self.is_transitioning, self.in_search_mode = True, False
        self.scrollable_frame._parent_canvas.yview_moveto(0.0)
        
        if self.stagger_after_id: self.after_cancel(self.stagger_after_id)
        self.stagger_after_id = None
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        
        loading_label = ctk.CTkLabel(self.scrollable_frame, text="正在加载...", font=self.display_font, text_color=TEXT_COLOR)
        loading_label.pack(pady=50)
        
        def _prepare_data_and_load():
            try:
                all_items = os.listdir(path)
                items = [item for item in all_items if not item.startswith('.') or item.endswith('_')]
                sorted_items = sorted(items, key=natural_sort_key)
                full_path_list = [os.path.join(path, item) for item in sorted_items]
            except FileNotFoundError:
                messagebox.showerror("错误", f"路径不存在或无法访问: {path}")
                self.after(0, self.go_back)
                return
            
            self.after(0, loading_label.destroy)
            self.after(0, self._load_cards_staggered, full_path_list, 0)

        threading.Thread(target=_prepare_data_and_load, daemon=True).start()

    # --- 修改: 优化“返回”逻辑，使其能中断加载 ---
    def go_back(self, event=None):
        if self.stagger_after_id:
            self.after_cancel(self.stagger_after_id)
            self.stagger_after_id = None
            self.is_transitioning = False 
        if self.is_transitioning: return

        if self.maintenance_menu.winfo_viewable():
            self.toggle_maintenance_menu()
            return
        if self.in_tag_edit_mode:
            self.prompt_save_tags_on_exit()
            return

        if self.in_search_mode:
            self.search_entry.delete(0, "end")
            self.browse_to(self.path_stack[-1])
            return

        if len(self.path_stack) > 1:
            self.path_stack.pop()
            path = self.path_stack[-1]
            display_path = f"模式: {self.current_mode} | " + os.path.relpath(path, self.base_dir)
            self.current_path_label.configure(text=display_path)
            self.browse_to(path)
            
    def handle_left_click(self, path, is_dir, is_special):
        if self.is_transitioning or self.in_tag_edit_mode: return
        if is_special:
            image_files = sorted([f for f in os.listdir(path) if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS], key=natural_sort_key)
            if image_files: ImageReader(self, path, image_files, os.path.basename(path))
            else: messagebox.showwarning("空文件夹", "这个特殊的图片文件夹是空的。")
        elif is_dir:
            self.path_stack.append(path)
            display_path = f"模式: {self.current_mode} | " + os.path.relpath(path, self.base_dir)
            self.current_path_label.configure(text=display_path)
            self.search_entry.delete(0, "end")
            self.browse_to(path)
        else:
            try: os.startfile(path)
            except Exception as e: messagebox.showerror("打开失败", f"无法打开文件: {path}\n错误: {e}")
    
    def switch_mode(self):
        if self.is_transitioning or self.in_tag_edit_mode: return
        if self.current_mode == "MANGA":
            self.current_mode, self.card_min_width = "JAV", JAV_CARD_MIN_WIDTH
            self.mode_switch_button.configure(text="切换至 MANGA 模式")
        else:
            self.current_mode, self.card_min_width = "MANGA", MANGA_CARD_MIN_WIDTH
            self.mode_switch_button.configure(text="切换至 JAV 模式")
        self.update_paths_for_mode()
        self.load_cover_map()
        path = self.root_path
        display_path = f"模式: {self.current_mode} | " + os.path.relpath(path, self.base_dir)
        self.current_path_label.configure(text=display_path)
        self.search_entry.delete(0, "end")
        self.browse_to(path)

    def open_current_directory(self):
        if not self.path_stack: return
        current_path = self.path_stack[-1]
        if not os.path.isdir(current_path): current_path = os.path.dirname(current_path)
        try:
            if sys.platform == "win32": os.startfile(current_path)
            elif sys.platform == "darwin": subprocess.call(["open", current_path])
            else: subprocess.call(["xdg-open", current_path])
        except Exception as e: messagebox.showerror("打开失败", f"无法打开文件夹: {current_path}\n错误: {e}")

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
                    found_covers = [os.path.join(self.cover_path, f) for f in os.listdir(self.cover_path) if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS and final_cover_regex_obj.match(os.path.splitext(f)[0])]
                    if len(found_covers) == 1: return found_covers[0]
                except (KeyError, re.error): continue
        for ext in IMAGE_EXTENSIONS:
            potential_cover = os.path.join(self.cover_path, base_name + ext)
            if os.path.exists(potential_cover): return potential_cover
        return None

    # --- 修改: 调整事件绑定，限制左键点击范围 ---
    def create_browser_card(self, parent, full_path):
        item_name, name_no_ext = os.path.basename(full_path), os.path.splitext(os.path.basename(full_path))[0]
        is_dir, is_special_dir = os.path.isdir(full_path), os.path.isdir(full_path) and item_name.endswith('_')
        
        card_frame = ctk.CTkFrame(parent, fg_color=CARD_BACKGROUND_COLOR, border_color=CARD_BORDER_COLOR, border_width=1)
        card_frame.grid_columnconfigure(0, weight=1)

        photo = None
        cover_image_path = self.find_cover(name_no_ext)
        if cover_image_path:
            try:
                aspect_ratio = 538 / 800 if self.current_mode == 'JAV' else 3 / 2
                img_w = self.card_min_width - 10
                img_h = int(img_w * aspect_ratio)
                pil_image = Image.open(cover_image_path)
                photo = ctk.CTkImage(light_image=pil_image.resize((img_w, img_h), Image.Resampling.LANCZOS), size=(img_w, img_h))
            except Exception as e: print(f"无法加载或处理封面图: {cover_image_path}\n错误: {e}")
        
        # 定义统一的点击回调函数
        left_click_callback = lambda e, p=full_path, d=is_dir, s=is_special_dir: self.handle_left_click(p, d, s)
        right_click_callback = lambda event: self.go_back(event)

        if photo:
            image_label = ctk.CTkLabel(card_frame, text="", image=photo)
            image_label.grid(row=0, column=0, padx=6, pady=6)
            # 仅对图片本身绑定左键点击
            image_label.bind("<Button-1>", left_click_callback)
        else:
            placeholder_height = int((self.card_min_width - 10) * (3/2))
            text_placeholder = ctk.CTkLabel(card_frame, text=name_no_ext, wraplength=self.card_min_width - 20, font=self.display_font, height=placeholder_height, fg_color="#1E1E1E")
            text_placeholder.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
            # 仅对占位符本身绑定左键点击
            text_placeholder.bind("<Button-1>", left_click_callback)

        display_name = ("📁 " if is_dir else "📄 ") + (name_no_ext if not is_special_dir else name_no_ext[:-1] + "") #图集
        filename_label = ctk.CTkLabel(card_frame, text=display_name, wraplength=self.card_min_width - 20, justify=tkinter.LEFT, font=self.display_font, text_color=TEXT_COLOR)
        filename_label.grid(row=1, column=0, padx=10, pady=(5, 5), sticky="w")
        
        tags_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        tags_frame.grid(row=2, column=0, padx=4, pady=(0, 4), sticky="ew")
        self.update_card_tags_display(tags_frame, name_no_ext)

        # 将右键返回事件绑定到卡片的各个主要组件上，确保响应
        card_frame.bind("<Button-3>", right_click_callback)
        for widget in card_frame.winfo_children():
            # 不为Tag编辑按钮等特殊按钮绑定返回事件
            if isinstance(widget, ctk.CTkButton): continue
            widget.bind("<Button-3>", right_click_callback)
            # 确保子控件的子控件也能触发
            for sub_widget in widget.winfo_children():
                 if isinstance(sub_widget, ctk.CTkButton): continue
                 sub_widget.bind("<Button-3>", right_click_callback)

        return card_frame

    def load_cover_map(self):
        self.cover_map = []; map_path = os.path.join(self.base_dir, "map.txt")
        if not os.path.exists(map_path): return
        try:
            with open(map_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#') or ',' not in line: continue
                    parts = line.split(',', 1); source_regex_str, cover_template_str = parts[0].strip(), parts[1].strip()
                    try:
                        regex_obj = re.compile(f"^{source_regex_str}$", re.IGNORECASE)
                        self.cover_map.append((regex_obj, cover_template_str))
                    except re.error as e: print(f"警告: map.txt 第 {i} 行存在无效的正则表达式: {source_regex_str}\n错误: {e}")
        except Exception as e: print(f"读取 map.txt 文件失败: {e}")

    def bind_global_right_click(self):
        callback = lambda event: self.go_back(event)
        self.bind("<Button-3>", callback)
        self.header_container.bind("<Button-3>", callback)
        self.header_frame.bind("<Button-3>", callback)
        for widget in self.header_frame.winfo_children(): widget.bind("<Button-3>", callback)
        self.nav_frame.bind("<Button-3>", callback)
        self.current_path_label.bind("<Button-3>", callback)
        self.scrollable_frame.bind("<Button-3>", callback)

    def update_paths_for_mode(self):
        if self.current_mode == "MANGA": self.root_path, self.cover_path = self.manga_pages_path, self.manga_cover_path
        else: self.root_path, self.cover_path = self.jav_video_path, self.jav_cover_path
        self.path_stack = [self.root_path]

    def on_closing(self):
        if self.in_tag_edit_mode:
            self.prompt_save_tags_on_exit()
            if self.in_tag_edit_mode: return
        self.destroy()

    def setup_font(self):
        font_path = os.path.join(self.base_dir, FONT_FILE_NAME)
        try:
            if not os.path.exists(font_path): raise FileNotFoundError
            unique_font_family = f"AppFont-{id(self)}"; tkextrafont.Font(file=font_path, family=unique_font_family)
            self.display_font = ctk.CTkFont(family=unique_font_family, size=FONT_SIZE)
        except Exception:
            print("自定义字体加载失败，使用默认字体。")
            self.display_font = ctk.CTkFont(size=FONT_SIZE)

class ImageReader(ctk.CTkToplevel):
    def __init__(self, master, pages_dir, image_files, title):
        super().__init__(master)
        self.title(title)
        self.state('zoomed')
        self.configure(fg_color=BACKGROUND_COLOR)
        self.grab_set()
        self.update_idletasks()

        self.pages_dir, self.image_files = pages_dir, image_files
        self.current_page_index = 0
        self.initial_load_done, self.progress_bar_populated = False, False

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self.image_label = ctk.CTkLabel(self, text="正在准备图片...", fg_color=BACKGROUND_COLOR, font=master.display_font)
        self.image_label.grid(row=0, column=0, sticky="nsew")
        
        self.page_segments = []
        self.progress_color, self.progress_bg_color = "#3B8ED0", "#555555"
        self.progress_bar_frame = ctk.CTkFrame(self, width = 40, fg_color="transparent")
        self.progress_bar_frame.grid_propagate(False)
        self.progress_bar_frame.grid(row=0, column=1, sticky="ns", padx=(5, 10), pady=10)
        self.progress_bar_frame.bind("<Configure>", self._populate_progress_bar)

        self.is_fading, self.next_image_data, self.current_pil_image, self.fade_after_id = False, None, None, None
        
        self.image_label.bind("<Button-1>", self.handle_click)
        self.image_label.bind("<Button-3>", self.handle_click)
        self.after(20, self.load_initial_page)

    def _populate_progress_bar(self, event):
        if self.progress_bar_populated or not self.image_files: return
        self.progress_bar_populated = True
        
        container_height = self.progress_bar_frame.winfo_height()
        num_pages = len(self.image_files)
        total_padding = (num_pages - 1) * 1
        segment_height = max(1, (container_height - total_padding) / num_pages)

        self.progress_bar_frame.grid_columnconfigure(0, weight=0)
        self.progress_bar_frame.grid_columnconfigure(1, weight=1)

        for i in range(num_pages):
            self.progress_bar_frame.grid_rowconfigure(i, weight=1)
            if (i + 1) % 10 == 0 or i == 0:
                num_label = ctk.CTkLabel(self.progress_bar_frame, text=str(i + 1), font=ctk.CTkFont(size=10), text_color="#FFFFFF")
                num_label.grid(row=i, column=0, sticky="e", padx=(0, 4))

            segment = ctk.CTkFrame(self.progress_bar_frame, height=segment_height, fg_color=self.progress_bg_color, corner_radius=2)
            segment.grid(row=i, column=1, sticky="ew", pady=0.5)
            segment.bind("<Button-1>", lambda event, index=i: self.go_to_page(index))
            self.page_segments.append(segment)
        self._update_progress_bar_colors()

    def _update_progress_bar_colors(self):
        for i, segment in enumerate(self.page_segments):
            segment.configure(fg_color=self.progress_color if i <= self.current_page_index else self.progress_bg_color)

    def go_to_page(self, page_index):
        if self.is_fading or not self.initial_load_done or page_index == self.current_page_index: return
        self._transition_to_page(page_index)

    def load_initial_page(self):
        if not self.initial_load_done:
            self.initial_load_done = True
            self._load_and_display_sync(self.current_page_index)
            self._update_progress_bar_colors()

    def handle_click(self, event):
        if self.is_fading or not self.initial_load_done: return
        target_index = -1
        if event.num == 1 and self.current_page_index < len(self.image_files) - 1:
            target_index = self.current_page_index + 1
        elif event.num == 3 and self.current_page_index > 0:
            target_index = self.current_page_index - 1
        if target_index != -1: self._transition_to_page(target_index)

    def _transition_to_page(self, target_index):
        self.is_fading, self.next_image_data = True, None
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
        except Exception as e: print(f"Error in background loading: {e}"); self.next_image_data = "error"

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
        progress = min((time.time() - start_time) / duration, 1.0)
        current_alpha = int(255 - (255 - 77) * progress)
        if self.current_pil_image:
            temp_img = self.current_pil_image.copy(); temp_img.putalpha(current_alpha)
            self.image_label.configure(image=ctk.CTkImage(light_image=temp_img, size=temp_img.size))
        if progress < 1.0: self.fade_after_id = self.after(15, lambda: self._fade_out_animation(start_time, duration))
        else: self.fade_after_id = None

    def _load_and_display_sync(self, index):
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
        self.image_label.configure(text="", image=ctk.CTkImage(light_image=self.current_pil_image, size=self.current_pil_image.size))

if __name__ == "__main__":
    app = FileSystemBrowser()
    app.mainloop()