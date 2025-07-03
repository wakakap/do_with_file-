import os
import sys
import subprocess
from flask import Flask, jsonify, render_template, request, send_from_directory, abort
import backend_logic as logic

# --- 配置 和 啟動檢查部分保持不變 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANGA_PAGES_PATH = os.path.join(BASE_DIR, "MANGA_PAGES")
MANGA_COVER_PATH = os.path.join(BASE_DIR, "MANGA_COVER")
JAV_VIDEO_PATH = os.path.join(BASE_DIR, "JAV_VIDEO")
JAV_COVER_PATH = os.path.join(BASE_DIR, "JAV_COVER")
TAGS_FILE_PATH = os.path.join(BASE_DIR, "tags.json")
MAP_FILE_PATH = os.path.join(BASE_DIR, "map.txt")
REQUIRED_PATHS = {
    "漫畫頁面資料夾 (MANGA_PAGES_PATH)": MANGA_PAGES_PATH,
    "漫畫封面資料夾 (MANGA_COVER_PATH)": MANGA_COVER_PATH,
    "影片資料夾 (JAV_VIDEO_PATH)": JAV_VIDEO_PATH,
    "影片封面資料夾 (JAV_COVER_PATH)": JAV_COVER_PATH,
}
for name, path in REQUIRED_PATHS.items():
    if not os.path.isdir(path):
        print(f"!!! 啟動錯誤：必要的「{name}」不存在或不是一個有效的目錄。")
        print(f"    請手動建立或在 app.py 中檢查路徑設定： {os.path.abspath(path)}")
        sys.exit(1)
if not os.path.isfile(TAGS_FILE_PATH): print(f"!!! 啟動警告：標籤檔案 'tags.json' 不存在，標籤功能將無法使用。")
if not os.path.isfile(MAP_FILE_PATH): print(f"!!! 啟動警告：封面映射檔案 'map.txt' 不存在，將僅使用直接檔名匹配封面。")

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

all_tags = logic.load_tags(TAGS_FILE_PATH)
cover_map = logic.load_cover_map(MAP_FILE_PATH)
print("--- 應用程式啟動 ---")
print(f"--- 已成功載入 {len(all_tags)} 個項目的標籤 ---")
print(f"--- 已成功載入 {len(cover_map)} 條封面映射規則 ---")

def get_paths_for_mode(mode):
    if mode.upper() == 'JAV': return JAV_VIDEO_PATH, JAV_COVER_PATH
    return MANGA_PAGES_PATH, MANGA_COVER_PATH
def is_safe_path(base_path, requested_path):
    return os.path.abspath(requested_path).startswith(os.path.abspath(base_path))

# --- API 路由 ---
@app.route('/api/gallery')
def api_gallery():
    mode = request.args.get('mode', 'MANGA')
    gallery_req_path = request.args.get('path', '')
    root_path, _ = get_paths_for_mode(mode)
    if not gallery_req_path or not is_safe_path(root_path, gallery_req_path):
        return jsonify({"error": "Access Denied or Invalid Path"}), 403
    images = logic.get_gallery_images(gallery_req_path)
    return jsonify(images)

# --- 修改此路由 ---
@app.route('/api/browse')
def api_browse():
    mode = request.args.get('mode', 'MANGA')
    root_path, cover_path = get_paths_for_mode(mode)
    req_path = request.args.get('path', root_path)
    if not is_safe_path(root_path, req_path):
        return jsonify({"error": "Access Denied"}), 403
    # 將 root_path 傳遞給邏輯函式
    items = logic.get_directory_items(req_path, root_path, cover_path, all_tags, cover_map)
    return jsonify({ "current_path": req_path, "items": items })

# --- 修改此路由 ---
@app.route('/api/search')
def api_search():
    mode = request.args.get('mode', 'MANGA')
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'keyword')
    if not query: return jsonify({"search_term": "", "items": []})
    root_path, cover_path = get_paths_for_mode(mode)
    # 將 root_path 傳遞給邏輯函式
    if search_type == 'tag':
        items = logic.search_by_tag(root_path, cover_path, all_tags, cover_map, query)
    else:
        items = logic.search_all(root_path, cover_path, all_tags, cover_map, query)
    return jsonify({ "search_term": query, "items": items })

# --- 修改此路由 ---
@app.route('/api/media/<mode>/<type>/<path:filepath>')
def api_get_media(mode, type, filepath):
    # 這個路由現在只接收相對路徑，安全性更高
    root_path, cover_path = get_paths_for_mode(mode)
    if type == 'cover':
        base_path = cover_path
    elif mode == 'JAV' and type == 'video':
        base_path = JAV_VIDEO_PATH
    else: # 預設為頁面路徑 (用於圖片集)
        base_path = MANGA_PAGES_PATH
    
    # 將基礎路徑和相對路徑拼接成絕對路徑
    full_path = os.path.join(base_path, filepath)

    # 再次確認拼接後的路徑是否在允許範圍內
    if not is_safe_path(base_path, full_path):
        abort(404)
        
    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path)
    return send_from_directory(directory, filename)

@app.route('/api/open_folder')
def api_open_folder():
    path = request.args.get('path', '')
    if not path or not os.path.exists(path): return jsonify({"status": "error", "message": "Path not found."}), 404
    if not (is_safe_path(MANGA_PAGES_PATH, path) or is_safe_path(JAV_VIDEO_PATH, path)): return jsonify({"status": "error", "message": "Access Denied"}), 403
    try:
        if sys.platform == "win32": os.startfile(path if os.path.isdir(path) else os.path.dirname(path))
        elif sys.platform == "darwin": subprocess.call(["open", path])
        else: subprocess.call(["xdg-open", path])
        return jsonify({"status": "success"})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)