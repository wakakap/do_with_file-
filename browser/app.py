import os
import sys
import subprocess
import threading
from flask import Flask, jsonify, render_template, request, send_from_directory, abort
import backend_logic as logic

# --- Configuration and Startup Checks (No changes needed) ---
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

# --- Global Data Loading ---
all_tags = logic.load_tags(TAGS_FILE_PATH)
cover_map = logic.load_cover_map(MAP_FILE_PATH)
print("--- 應用程式啟動 ---")
print(f"--- 已成功載入 {len(all_tags)} 個項目的標籤 ---")
print(f"--- 已成功載入 {len(cover_map)} 條封面映射規則 ---")

# --- Helper Functions ---
def get_paths_for_mode(mode):
    if mode.upper() == 'JAV': return JAV_VIDEO_PATH, JAV_COVER_PATH
    return MANGA_PAGES_PATH, MANGA_COVER_PATH

def is_safe_path(base_path, requested_path):
    # Resolve both paths to their absolute real paths to prevent symlink tricks
    abs_base = os.path.realpath(base_path)
    abs_req = os.path.realpath(requested_path)
    return abs_req.startswith(abs_base)

# --- API Routes ---

@app.route('/api/gallery')
def api_gallery():
    mode = request.args.get('mode', 'MANGA')
    gallery_req_path = request.args.get('path', '')
    root_path, _ = get_paths_for_mode(mode)
    # Important: The gallery path should be an absolute path passed from the frontend
    if not gallery_req_path or not is_safe_path(root_path, gallery_req_path):
        return jsonify({"error": "Access Denied or Invalid Path"}), 403
    images = logic.get_gallery_images(gallery_req_path)
    return jsonify(images)

@app.route('/api/browse')
def api_browse():
    mode = request.args.get('mode', 'MANGA')
    root_path, cover_path = get_paths_for_mode(mode)
    # Default to root_path if 'path' is not provided
    req_path = request.args.get('path', root_path)
    if not is_safe_path(root_path, req_path):
        return jsonify({"error": "Access Denied"}), 403
    items = logic.get_directory_items(req_path, root_path, cover_path, all_tags, cover_map)
    return jsonify({ "current_path": req_path, "items": items })

@app.route('/api/search')
def api_search():
    mode = request.args.get('mode', 'MANGA')
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'keyword')
    if not query: return jsonify({"search_term": "", "items": []})
    root_path, cover_path = get_paths_for_mode(mode)
    if search_type == 'tag':
        items = logic.search_by_tag(root_path, cover_path, all_tags, cover_map, query)
    else:
        items = logic.search_all(root_path, cover_path, all_tags, cover_map, query)
    return jsonify({ "search_term": query, "items": items })

@app.route('/api/media/<mode>/<type>/<path:filepath>')
def api_get_media(mode, type, filepath):
    root_path, cover_path = get_paths_for_mode(mode)
    if type == 'cover':
        base_path = cover_path
    elif mode.upper() == 'JAV' and type == 'video':
        base_path = JAV_VIDEO_PATH
    elif mode.upper() == 'MANGA' and type == 'pages':
        # For gallery images, the 'filepath' should be 'base_media_path/image_name.jpg'
        # The base_media_path is relative to the MANGA_PAGES_PATH
        base_path = MANGA_PAGES_PATH
    else:
        abort(404) # Invalid type or mode combination
    
    # Safely join paths and prevent path traversal
    full_path = os.path.normpath(os.path.join(base_path, filepath))
    
    if not is_safe_path(base_path, full_path):
        abort(404)
        
    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path)
    return send_from_directory(directory, filename)

@app.route('/api/open_folder')
def api_open_folder():
    path = request.args.get('path', '')
    if not path or not os.path.exists(path): return jsonify({"status": "error", "message": "Path not found."}), 404
    # Check against both possible base paths
    if not (is_safe_path(MANGA_PAGES_PATH, path) or is_safe_path(JAV_VIDEO_PATH, path)): 
        return jsonify({"status": "error", "message": "Access Denied"}), 403
    try:
        # Use a more secure and reliable way to open folders
        if sys.platform == "win32": os.startfile(path if os.path.isdir(path) else os.path.dirname(path))
        elif sys.platform == "darwin": subprocess.call(["open", path])
        else: subprocess.call(["xdg-open", path])
        return jsonify({"status": "success"})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

# --- NEW MAINTENANCE API ENDPOINTS ---

@app.route('/api/auto_import_tags', methods=['POST'])
def api_auto_import_tags():
    """
    API端点，用于触发基于项目名称的自动Tag导入。
    """
    if not request.is_json:
        return jsonify({"status": "error", "message": "请求必须是JSON格式。"}), 400
    
    data = request.get_json()
    item_name = data.get('item_name')

    if not item_name:
        return jsonify({"status": "error", "message": "未提供 'item_name'。"}), 400

    # 调用核心逻辑函数
    result = logic.auto_import_tags(item_name)
    
    # 根据逻辑函数的结果返回响应
    if result['status'] == 'success':
        return jsonify(result)
    else:
        return jsonify(result), 500

@app.route('/api/tags', methods=['GET', 'POST'])
def api_tags():
    global all_tags
    if request.method == 'GET':
        return jsonify(all_tags)
    
    if request.method == 'POST':
        # Check for content type to prevent errors
        if not request.is_json:
            return jsonify({"status": "error", "message": "Invalid request: Content-Type must be application/json."}), 400
        
        new_tags_data = request.get_json()
        result = logic.save_tags(TAGS_FILE_PATH, new_tags_data)
        
        if result['status'] == 'success':
            # Reload tags into memory after successful save
            all_tags = logic.load_tags(TAGS_FILE_PATH)
            print(f"--- 已成功保存並重新載入 {len(all_tags)} 個項目的標籤 ---")
            return jsonify(result)
        else:
            return jsonify(result), 500

@app.route('/api/generate_covers', methods=['POST'])
def api_generate_covers():
    # This process can be slow, so it should run in the background.
    # The API will return immediately.
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid request: Content-Type must be application/json."}), 400
        
    data = request.get_json()
    mode = data.get('mode', 'MANGA')
    current_path = data.get('path', '')

    root_path, cover_path = get_paths_for_mode(mode)

    if not current_path or not is_safe_path(root_path, current_path):
         return jsonify({"status": "error", "message": "Invalid or unsafe path provided."}), 400

    # Running the logic in a separate thread to not block the server
    def worker():
        print(f"--- 開始生成封面，掃描路徑: {current_path} ---")
        result = logic.generate_covers_logic(current_path, cover_path, cover_map)
        print(f"--- 封面生成完畢: {result['generated_count']} 個新封面。 臨時目錄: {result['temp_path']} ---")

    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()

    return jsonify({
        "status": "started", 
        "message": "Cover generation process has been started in the background. Check the server console for completion status."
    })

# --- Main App Route ---
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)