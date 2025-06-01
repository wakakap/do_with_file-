# 用b的文本替换a的文本，保留a的时间戳
import re
import os
import tkinter as tk
from tkinter import filedialog, messagebox

def replace_srt_text(a_srt_path, b_srt_path, output_srt_path):
    """
    Replaces the text content of a.srt with text from b.srt sequentially,
    and saves the result to a new SRT file.

    Args:
        a_srt_path (str): The file path to the source SRT (a.srt).
        b_srt_path (str): The file path to the SRT containing new text (b.srt).
        output_srt_path (str): The file path to save the modified SRT.
    """

    # Check if input files exist
    if not os.path.exists(a_srt_path):
        messagebox.showerror("Error", f"Source SRT file not found at '{a_srt_path}'")
        return
    if not os.path.exists(b_srt_path):
        messagebox.showerror("Error", f"Replacement SRT file not found at '{b_srt_path}'")
        return

    # Regular expression to capture SRT blocks: ID, timestamps, and text
    srt_block_regex = re.compile(
        r'^(\d+)\n'  # Subtitle number (e.g., 1)
        r'(\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})\n'  # Timestamps
        r'([\s\S]*?)'  # Subtitle text (non-greedy, matches anything including newlines)
        r'(?=\n\d+\n|\Z)', # Positive lookahead for next subtitle number or end of file
        re.MULTILINE
    )

    try:
        with open(a_srt_path, 'r', encoding='utf-8') as f_a:
            content_a = f_a.read()
        
        with open(b_srt_path, 'r', encoding='utf-8') as f_b:
            content_b = f_b.read()

        # Find all text blocks in both SRT files
        matches_a = list(srt_block_regex.finditer(content_a))
        matches_b = list(srt_block_regex.finditer(content_b))

        output_srt_lines = []

        # Iterate through matched blocks from a.srt
        for i, match_a in enumerate(matches_a):
            current_id_a = match_a.group(1)
            current_timestamps_a = match_a.group(2)
            original_text_a = match_a.group(3).strip()

            new_text_b = ""
            if i < len(matches_b):
                new_text_b = matches_b[i].group(3).strip()
            else:
                new_text_b = original_text_a
                # Removed print statement for GUI version; use messagebox if needed
                # messagebox.showwarning("Warning", f"b.srt has fewer subtitles than a.srt. Keeping original text for subtitle {current_id_a} and subsequent.")

            block_reconstructed = f"{current_id_a}\n{current_timestamps_a}\n{new_text_b}\n\n"
            output_srt_lines.append(block_reconstructed)
            
            # If b.srt ran out on an earlier iteration, we still need to process remaining a.srt blocks
            if i >= len(matches_b) and i > 0:
                break # Exit the loop if b ran out

        # Handle cases where b.srt might have more subtitles than a.srt
        if len(matches_b) > len(matches_a):
            messagebox.showwarning("Warning", "b.srt has more subtitles than a.srt. Remaining subtitles from b.srt will not be included.")

        # Join the reconstructed blocks and write to the output file
        with open(output_srt_path, 'w', encoding='utf-8') as f_out:
            f_out.write("".join(output_srt_lines).strip())
        
        messagebox.showinfo("Success", f"Successfully replaced text and saved to '{output_srt_path}'")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

class SrtReplacerApp:
    def __init__(self, master):
        self.master = master
        master.title("SRT Text Replacer")

        self.a_srt_path = tk.StringVar()
        self.b_srt_path = tk.StringVar()
        self.output_srt_path = tk.StringVar()

        # --- Input A.SRT (File to be modified) ---
        tk.Label(master, text="SRT to be modified (a.srt):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.a_entry = tk.Entry(master, textvariable=self.a_srt_path, width=50)
        self.a_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(master, text="Browse", command=self.browse_a_srt).grid(row=0, column=2, padx=5, pady=5)

        # --- Input B.SRT (File with new text) ---
        tk.Label(master, text="SRT with new text (b.srt):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.b_entry = tk.Entry(master, textvariable=self.b_srt_path, width=50)
        self.b_entry.grid(row=1, column=1, padx=5, pady=5)
        tk.Button(master, text="Browse", command=self.browse_b_srt).grid(row=1, column=2, padx=5, pady=5)

        # --- Output SRT File ---
        tk.Label(master, text="Output SRT file:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.output_entry = tk.Entry(master, textvariable=self.output_srt_path, width=50)
        self.output_entry.grid(row=2, column=1, padx=5, pady=5)
        tk.Button(master, text="Browse", command=self.browse_output_srt).grid(row=2, column=2, padx=5, pady=5)

        # --- Process Button ---
        tk.Button(master, text="Process SRT Files", command=self.process_files).grid(row=3, column=1, pady=10)

    def browse_a_srt(self):
        filename = filedialog.askopenfilename(
            title="Select SRT file to be modified (a.srt)",
            filetypes=[("SRT files", "*.srt"), ("All files", "*.*")]
        )
        if filename:
            self.a_srt_path.set(filename)

    def browse_b_srt(self):
        filename = filedialog.askopenfilename(
            title="Select SRT file with new text (b.srt)",
            filetypes=[("SRT files", "*.srt"), ("All files", "*.*")]
        )
        if filename:
            self.b_srt_path.set(filename)

    def browse_output_srt(self):
        filename = filedialog.asksaveasfilename(
            title="Save modified SRT file as",
            defaultextension=".srt",
            filetypes=[("SRT files", "*.srt"), ("All files", "*.*")]
        )
        if filename:
            self.output_srt_path.set(filename)

    def process_files(self):
        a_path = self.a_srt_path.get()
        b_path = self.b_srt_path.get()
        output_path = self.output_srt_path.get()

        if not a_path or not b_path or not output_path:
            messagebox.showwarning("Input Error", "Please select all three file paths.")
            return

        replace_srt_text(a_path, b_path, output_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = SrtReplacerApp(root)
    root.mainloop()