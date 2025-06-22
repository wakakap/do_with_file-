import tkinter
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import glob
import sys
try:
    import tkextrafont
except ImportError:
    messagebox.showerror("缺少庫", "需要 tkextrafont 庫來載入自訂字體。\n請執行: pip install tkextrafont")
    sys.exit()

# /你的工作目录/
# ├── .exe  ( .py 脚本)
# └───/VIDEO/
# │   ├───/项目A/
# │   │   └─── A.mov
# │   │
# │   ├───/项目B-启动仪式/
# │   │   └─── B.avi
# │   │
# │   └───/项目C/
# │       └─── C.mp4
# └───/JPG/
#     ├───/项目A.jpg
#     ├───/项目B.jpg
#     └───/项目c.jpg

# --- UI佈局和尺寸配置 ---
ITEM_CARD_MIN_WIDTH = 320 # 稍微調整卡片寬度以適應新風格
ASPECT_RATIO = 800 / 538
ITEM_IMAGE_HEIGHT = int(ITEM_CARD_MIN_WIDTH / ASPECT_RATIO)
RESIZE_DEBOUNCE_MS = 150
CARD_PAD_X = 6       # 稍微增加左右間距
CARD_PAD_Y = 6       # 稍微增加上下間距
CARD_BORDER_COLOR = "#333333" # 深灰色，作為卡片邊框或背景區隔
FONT_FILE_NAME = "LXGWWenKai-Light.ttf"
FONT_SIZE = 14
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv']

# --- 顏色主題 ---
BACKGROUND_COLOR = "#242424"  # 深灰色背景
TEXT_COLOR = "#FFFFFF"      # 白色文字
BUTTON_COLOR = "#3B3B3B"    # 稍亮的深灰色按鈕
BUTTON_HOVER_COLOR = "#4A4A4A" # 按鈕懸浮顏色
CARD_BACKGROUND_COLOR = "#2E2E2E" # 卡片背景色

class ImageVideoBrowser(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("奖励自己浏览器")
        self.geometry("1100x750")
        ctk.set_appearance_mode("Dark") # 設定為暗色模式
        ctk.set_default_color_theme("blue") # 雖然是暗色模式，主題色可以保留藍色，影響例如按鈕高亮等

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        self.card_widgets = []
        self._resize_timer = None
        self._current_num_columns = 0
        self.setup_font()

        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color=BACKGROUND_COLOR) # 主框架背景色
        self.scrollable_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.scrollable_frame.columnconfigure(0, weight=1) # 確保內容置中

        self.bind("<Configure>", self.on_window_resize)
        self.after(100, self.auto_load_on_startup)

    def setup_font(self):
        font_path = os.path.join(self.base_dir, FONT_FILE_NAME)
        try:
            if not os.path.exists(font_path):
                raise FileNotFoundError
            unique_font_family = f"AppFont-{id(self)}"
            tkextrafont.Font(file=font_path, family=unique_font_family)
            self.display_font = ctk.CTkFont(family=unique_font_family, size=FONT_SIZE, weight="bold")
            print(f"成功載入自訂字體: {FONT_FILE_NAME}")
        except Exception as e:
            print(f"警告: 載入自訂字體失敗 ({e})。將使用系統預設字體。")
            self.display_font = ctk.CTkFont(size=FONT_SIZE, weight="bold")

    def auto_load_on_startup(self):
        jpg_folder = os.path.join(self.base_dir, "JPG")
        if not os.path.isdir(jpg_folder):
            messagebox.showerror("啟動錯誤", f"程式目錄下未找到 'JPG' 資料夾。")
            return
        self.load_images(jpg_folder)

    def load_images(self, folder_path):
        for card in self.card_widgets:
            card.destroy()
        self.card_widgets.clear()
        self._current_num_columns = 0
        image_paths = sorted(glob.glob(os.path.join(folder_path, '*.jpg')) + glob.glob(os.path.join(folder_path, '*.jpeg')))
        if not image_paths:
            ctk.CTkLabel(self.scrollable_frame, text="'JPG' 資料夾中沒有找到任何圖片。", text_color=TEXT_COLOR).pack(pady=20)
            return
        for image_path in image_paths:
            card = self.create_image_card(image_path)
            self.card_widgets.append(card)
        self.reflow_layout()

    def create_image_card(self, image_path):
        card_frame = ctk.CTkFrame(self.scrollable_frame, fg_color=CARD_BACKGROUND_COLOR, border_color=CARD_BORDER_COLOR, border_width=1) # 卡片背景和邊框
        card_frame.grid_columnconfigure(0, weight=1)

        img = Image.open(image_path)
        img = img.resize((ITEM_CARD_MIN_WIDTH - 10, ITEM_IMAGE_HEIGHT - 10), Image.Resampling.LANCZOS) # 稍微縮小圖片，留出內邊距
        photo = ImageTk.PhotoImage(img)

        image_label = ctk.CTkLabel(card_frame, text="", image=photo, fg_color=CARD_BACKGROUND_COLOR) # 確保圖片標籤背景一致
        image_label.image = photo
        image_label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        filename_full = os.path.basename(image_path)
        filename_no_ext = os.path.splitext(filename_full)[0]
        filename_label = ctk.CTkLabel(
            card_frame,
            text=filename_no_ext,
            wraplength=ITEM_CARD_MIN_WIDTH - 30,
            justify=tkinter.LEFT,
            font=self.display_font,
            text_color=TEXT_COLOR,
            fg_color=CARD_BACKGROUND_COLOR # 確保文字標籤背景一致
        )
        filename_label.grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")

        for widget in [card_frame, image_label, filename_label]:
            widget.bind("<Button-1>", lambda e, p=image_path: self.view_image_popup(p))
            widget.bind("<Button-3>", lambda e, p=image_path: self.play_corresponding_video(p))

        return card_frame

    def on_window_resize(self, event=None):
        if self._resize_timer:
            self.after_cancel(self._resize_timer)
        self._resize_timer = self.after(RESIZE_DEBOUNCE_MS, self.reflow_layout)

    def reflow_layout(self):
        if not self.card_widgets:
            return
        container_width = self.scrollable_frame.winfo_width()
        if container_width <= 1:
            return

        card_total_width = ITEM_CARD_MIN_WIDTH + (CARD_PAD_X * 2)
        num_columns = max(1, container_width // card_total_width)

        if num_columns == self._current_num_columns:
            return

        self.scrollable_frame.grid_remove()
        self.update_idletasks()

        self._current_num_columns = num_columns

        for card in self.card_widgets:
            card.grid_forget()

        self.scrollable_frame.grid_columnconfigure(list(range(num_columns)), weight=1)

        for i, card in enumerate(self.card_widgets):
            row = i // num_columns
            col = i % num_columns
            card.grid(row=row, column=col, padx=CARD_PAD_X, pady=CARD_PAD_Y, sticky="ns")

        self.scrollable_frame.grid()

    def view_image_popup(self, image_path):
        try:
            top = ctk.CTkToplevel(self)
            top.title(os.path.basename(image_path))

            img = Image.open(image_path)
            screen_width = self.winfo_screenwidth() - 100
            screen_height = self.winfo_screenheight() - 150
            img.thumbnail((screen_width, screen_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            img_label = ctk.CTkLabel(top, text="", image=photo, fg_color=BACKGROUND_COLOR) # 彈出視窗背景色
            img_label.image = photo
            img_label.pack(padx=20, pady=20)

            # --- 彈出視窗居中 ---
            top.update_idletasks()
            w = top.winfo_width()
            h = top.winfo_height()
            sw = top.winfo_screenwidth()
            sh = top.winfo_screenheight()
            x = (sw - w) // 2
            y = (sh - h) // 2
            top.geometry(f"+{x}+{y}")

            top.grab_set()
        except Exception as e:
            messagebox.showerror("錯誤", f"無法開啟圖片: {e}")

    def play_corresponding_video(self, image_path):
        video_root_folder = os.path.join(self.base_dir, "VIDEO")
        if not os.path.isdir(video_root_folder):
            messagebox.showerror("錯誤", "程式目錄下未找到 'VIDEO' 資料夾。")
            return
        image_filename = os.path.basename(image_path)
        parts = image_filename.split(' ', 1)
        prefix = parts[-0] # 这里原代码有误，已修正为 parts[-0] 或 parts[-1] 取最后一个部分。根据您的逻辑应该是取第一个空格前的部分，所以应为 parts[-0]
        prefix_lower = prefix.lower()
        target_video_folder = None
        for item_name in os.listdir(video_root_folder):
            full_item_path = os.path.join(video_root_folder, item_name)
            if os.path.isdir(full_item_path) and item_name.lower().startswith(prefix_lower):
                target_video_folder = full_item_path
                break
        if not target_video_folder:
            messagebox.showwarning("未找到", f"在 'VIDEO' 資料夾中，沒有找到任何以 '{prefix}' 開頭的子資料夾。")
            return
        found_video_file = None
        for file_in_folder in os.listdir(target_video_folder):
            if os.path.splitext(file_in_folder)[1].lower() in VIDEO_EXTENSIONS:
                found_video_file = os.path.join(target_video_folder, file_in_folder)
                break
        if found_video_file:
            try:
                os.startfile(found_video_file)
            except Exception as e:
                messagebox.showerror("播放失敗", f"找到影片 {os.path.basename(found_video_file)} 但無法播放: {e}")
        else:
            messagebox.showwarning("未找到", f"在資料夾 '{os.path.basename(target_video_folder)}' 中沒有找到任何影片檔案。")

if __name__ == "__main__":
    app = ImageVideoBrowser()
    app.mainloop()