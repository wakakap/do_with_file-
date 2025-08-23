import os
import sys
import subprocess
import threading
from flask import Flask, jsonify, render_template, request, send_from_directory, abort
import backend_logic as logic
from flask_cors import CORS

# --- 配置和启动检查 ---
BASE_DIR = "H:\\BROWSER"
# 定义数据文件的全局路径
TAGS_FILE_PATH = os.path.join(BASE_DIR, "tags.json")
MAP_FILE_PATH = os.path.join(BASE_DIR, "map.txt")

# 定义所有模式及其对应的文件夹名称
MODES_CONFIG = {
    'MANGA': {'pages': 'MANGA_PAGES', 'cover': 'MANGA_COVER'},
    'JAV': {'pages': 'JAV_PAGES', 'cover': 'JAV_COVER'},
    'ANIME': {'pages': 'ANIME_PAGES', 'cover': 'ANIME_COVER'},
    'MUSIC': {'pages': 'MUSIC_PAGES', 'cover': 'MUSIC_COVER'},
    'NOVEL': {'pages': 'NOVEL_PAGES', 'cover': 'NOVEL_COVER'},
    'OTHER': {'pages': 'OTHER_PAGES', 'cover': 'OTHER_COVER'},
}

for mode, config in MODES_CONFIG.items():
    for key, folder_name in config.items():
        path = os.path.join(BASE_DIR, folder_name)
        if not os.path.isdir(path):
            print(f"!!! 啟動錯誤：必要的資料夾「{folder_name}」不存在。")
            print(f"    路徑: {os.path.abspath(path)}")
            sys.exit(1)

# 启动时检查数据文件
if not os.path.isfile(TAGS_FILE_PATH): print(f"!!! 啟動警告：標籤檔案 'tags.json' 不存在，標籤功能將無法使用。")
if not os.path.isfile(MAP_FILE_PATH): print(f"!!! 啟動警告：封面映射檔案 'map.txt' 不存在，將僅使用直接檔名匹配封面。")

# 初始化 Flask 应用
app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False

# --- 辅助函数 ---
def is_safe_path(base_path, requested_path):
    """安全检查函数，防止路径遍历攻击。确保请求的路径是在指定的根目录之下。"""
    abs_base = os.path.realpath(base_path)
    abs_req = os.path.realpath(requested_path)
    return abs_req.startswith(abs_base)

# --- 资源管理 ---
# 全局数据（跨模式共享）
all_tags = logic.load_tags(TAGS_FILE_PATH)
cover_map = logic.load_cover_map(MAP_FILE_PATH)
# 缓存按需加载的模式特定资源
MODE_RESOURCES = {}
# 线程锁
auto_import_lock = threading.Lock()
view_count_lock = threading.Lock()

def get_paths_for_mode(mode):
    """根据模式返回对应的内容和封面路径。"""
    mode_upper = mode.upper()
    config = MODES_CONFIG.get(mode_upper, MODES_CONFIG['MANGA'])
    pages_path = os.path.join(BASE_DIR, config['pages'])
    cover_path = os.path.join(BASE_DIR, config['cover'])
    return pages_path, cover_path

def build_item_key_map_for_mode(scan_path):
    """为指定路径构建 item_key -> full_path 的映射。"""
    key_map = {}
    for root, dirs, files in os.walk(scan_path):
        for name in files + dirs:
            item_key = os.path.splitext(name)[0]
            if item_key not in key_map:
                key_map[item_key] = os.path.join(root, name)
        dirs[:] = [d for d in dirs if not logic.is_gallery(os.path.join(root, d))]
    return key_map

def load_resources_for_mode(mode):
    """按需加载指定模式的资源（主要是key_map），并缓存结果。"""
    mode_upper = mode.upper()
    if mode_upper not in MODE_RESOURCES:
        print(f"--- 首次加载模式 '{mode_upper}' 的资源... ---")
        pages_path, _ = get_paths_for_mode(mode_upper)
        key_map = build_item_key_map_for_mode(pages_path)
        MODE_RESOURCES[mode_upper] = {'key_map': key_map}
        print(f"--- 模式 '{mode_upper}' 加载完毕，找到 {len(key_map)} 个项目。 ---")

print("--- 應用程式啟動 ---")
print(f"--- 已成功載入 {len(all_tags)} 個項目的標籤 ---")
print(f"--- 已成功載入 {len(cover_map)} 條封面映射規則 ---")
print("--- 模式资源将在首次访问时按需加载 ---")

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

@app.route('/api/browse')
def api_browse():
    mode = request.args.get('mode', 'MANGA')
    root_path, cover_path = get_paths_for_mode(mode)
    req_path = request.args.get('path', root_path)
    if not is_safe_path(root_path, req_path):
        return jsonify({"error": "Access Denied"}), 403
    items = logic.get_directory_items(req_path, root_path, cover_path, all_tags, cover_map)
    return jsonify({"current_path": req_path, "items": items})

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
    return jsonify({"search_term": query, "items": items})

@app.route('/api/album_details')
def api_album_details():
    """API端点：获取专辑文件夹的音轨和封面。"""
    mode = request.args.get('mode', 'MUSIC')
    album_req_path = request.args.get('path', '')
    pages_path, cover_path = get_paths_for_mode(mode)
    
    if not album_req_path or not is_safe_path(pages_path, album_req_path):
        return jsonify({"error": "Access Denied or Invalid Path"}), 403
    details = logic.get_album_details(album_req_path, cover_path, cover_map)
    return jsonify(details)

@app.route('/api/anime_details')
def api_anime_details():
    """API端点：获取动画文件夹的剧集和字幕。"""
    mode = request.args.get('mode', 'ANIME')
    anime_req_path = request.args.get('path', '')
    root_path, _ = get_paths_for_mode(mode)
    
    if not anime_req_path or not is_safe_path(root_path, anime_req_path):
        return jsonify({"error": "Access Denied or Invalid Path"}), 403
        
    details = logic.get_anime_details(anime_req_path)
    return jsonify(details)

@app.route('/api/media/<mode>/<type>/<path:filepath>')
def api_get_media(mode, type, filepath):
    """通用媒体文件服务路由，现已修正对ANIME模式的支持。"""
    root_path, cover_path = get_paths_for_mode(mode)
    base_path = None
    
    mode_upper = mode.upper()
    type_lower = type.lower()
    file_ext = os.path.splitext(filepath)[1].lower()

    if type_lower == 'cover':
        base_path = cover_path
    # 视频和音频文件的路由逻辑保持不变
    elif mode_upper == 'JAV' and type_lower == 'video':
        base_path = root_path
    elif mode_upper == 'MUSIC' and type_lower == 'audio':
        base_path = root_path
    # 'pages' 类型现在也包含视频、epub和字幕
    elif mode_upper in ['MANGA', 'NOVEL', 'OTHER', 'ANIME', 'MUSIC'] and type_lower == 'pages':
        base_path = root_path
    else:
        # 如果类型不匹配，直接中止
        print(f"[调试] 路由中止: 不支持的 mode/type 组合 - {mode}/{type}")
        abort(404)
    
    if not base_path:
        print(f"[调试] 路由中止: 未能确定 base_path")
        abort(404)

    full_path = os.path.normpath(os.path.join(base_path, filepath))
    
    # --- [服务器端调试 1] ---
    # print(f"[调试] 请求媒体: mode={mode}, type={type}, filepath={filepath}")
    # print(f"[调试] 计算出的完整路径: {full_path}")
    
    if not is_safe_path(base_path, full_path):
        print(f"[调试] 安全检查失败: 请求的路径 '{full_path}' 不在基础路径 '{base_path}' 下")
        abort(403) # 使用 403 Forbidden 更合适
        
    if not os.path.exists(full_path):
        print(f"[调试] 文件未找到: {full_path}")
        abort(404)

    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path)
    
    # --- 关键修改：为不同字幕格式设置正确的MIME类型 ---
    if file_ext in logic.SUBTITLE_EXTENSIONS:
        mimetype = 'text/plain' # 默认值
        if file_ext == '.vtt':
            mimetype = 'text/vtt'
        elif file_ext == '.srt':
            # 'application/x-subrip' 是一个更具体的类型，但 'text/plain' 也被广泛接受
            mimetype = 'text/plain' 
        
        print(f"[调试] 发送字幕文件: '{filename}'，MIME类型: '{mimetype}'")
        return send_from_directory(
            directory,
            filename,
            mimetype=mimetype,
            as_attachment=False # 确保浏览器内联显示而不是下载
        )
    
    # 对于其他文件，使用默认的发送方式
    # print(f"[调试] 发送普通媒体文件: '{filename}'")
    return send_from_directory(directory, filename)

@app.route('/api/open_folder')
def api_open_folder():
    path = request.args.get('path', '')
    if not path or not os.path.exists(path): return jsonify({"status": "error", "message": "Path not found."}), 404
    
    is_safe = False
    for mode in MODES_CONFIG:
        pages_path, _ = get_paths_for_mode(mode)
        if is_safe_path(pages_path, path):
            is_safe = True
            break
    if not is_safe:
        return jsonify({"status": "error", "message": "Access Denied"}), 403
        
    try:
        if sys.platform == "win32":
            os.startfile(path if os.path.isdir(path) else os.path.dirname(path))
        elif sys.platform == "darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- 维护功能 API 端点 ---
@app.route('/api/structured_stats')
def api_structured_stats():
    """API端点：获取按文件结构组织的访问统计数据。"""
    combined_key_map = {}
    all_root_paths = []
    # --- 核心修改点: 在构建 key_map 时同时存入 mode ---
    for mode in MODES_CONFIG:
        load_resources_for_mode(mode)
        # 现在的 value 是一个包含 path 和 mode 的字典
        for key, path in MODE_RESOURCES[mode]['key_map'].items():
            combined_key_map[key] = {'path': path, 'mode': mode}
        all_root_paths.append(get_paths_for_mode(mode)[0])

    stats_data = logic.get_structured_stats_data(
        TAGS_FILE_PATH, 
        combined_key_map, 
        all_root_paths
    )
    return jsonify(stats_data)

@app.route('/api/record_view', methods=['POST'])
def api_record_view():
    data = request.get_json()
    if not data: return jsonify({"status": "error", "message": "Invalid request"}), 400
    item_key = data.get('item_key')
    # 从 'page_index' 泛化为 'identifier'
    identifier = data.get('identifier') 
    if not item_key: return jsonify({"status": "error", "message": "item_key is required"}), 400

    with view_count_lock:
        result = logic.update_view_count(TAGS_FILE_PATH, item_key, identifier)
    
    if result['status'] == 'success':
        global all_tags
        all_tags = logic.load_tags(TAGS_FILE_PATH)
    return jsonify(result)

@app.route('/api/record_stats_view', methods=['POST'])
def api_record_stats_view():
    data = request.get_json()
    if not data or 'full_path' not in data:
        return jsonify({"status": "error", "message": "Invalid request"}), 400
    
    full_path = data.get('full_path')
    all_root_paths = [get_paths_for_mode(mode)[0] for mode in MODES_CONFIG]
    
    with view_count_lock: # 复用现有的线程锁
        result = logic.record_view_recursive(TAGS_FILE_PATH, full_path, all_root_paths)
    
    if result['status'] == 'success':
        global all_tags
        all_tags = logic.load_tags(TAGS_FILE_PATH) # 重新加载标签数据
    return jsonify(result)

@app.route('/api/auto_import_tags', methods=['POST'])
def api_auto_import_tags():
    if not auto_import_lock.acquire(blocking=False):
        return jsonify({"status": "error", "message": "另一个导入操作正在进行，请稍后再试。"}), 429
    try:
        data = request.get_json()
        if not data: return jsonify({"status": "error", "message": "请求必须是JSON格式。"}), 400
        item_name = data.get('item_name')
        if not item_name: return jsonify({"status": "error", "message": "未提供 'item_name'。"}), 400
        result = logic.auto_import_tags(item_name)
        return jsonify(result) if result.get('status') == 'success' else (jsonify(result), 500)
    finally:
        auto_import_lock.release()

@app.route('/api/tags', methods=['GET', 'POST'])
def api_tags():
    global all_tags
    if request.method == 'GET':
        return jsonify(all_tags)
    if request.method == 'POST':
        new_tags_data = request.get_json()
        if not new_tags_data: return jsonify({"status": "error", "message": "Invalid request"}), 400
        result = logic.save_tags(TAGS_FILE_PATH, new_tags_data)
        if result['status'] == 'success':
            all_tags = logic.load_tags(TAGS_FILE_PATH)
            print(f"--- 已成功保存並重新載入 {len(all_tags)} 個項目的標籤 ---")
            return jsonify(result)
        else:
            return jsonify(result), 500

@app.route('/api/generate_covers', methods=['POST'])
def api_generate_covers():
    data = request.get_json()
    if not data: return jsonify({"status": "error", "message": "Invalid request"}), 400
    mode = data.get('mode', 'MANGA')
    current_path = data.get('path', '')
    root_path, cover_path = get_paths_for_mode(mode)
    if not current_path or not is_safe_path(root_path, current_path):
         return jsonify({"status": "error", "message": "Invalid or unsafe path provided."}), 400

    def worker():
        print(f"--- 開始生成封面，掃描路徑: {current_path} ---")
        result = logic.generate_covers_logic(current_path, cover_path, cover_map)
        print(f"--- 封面生成完畢: {result['generated_count']} 個新封面。 臨時目錄: {result['temp_path']} ---")

    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started", "message": "Cover generation process started."})

# --- 主应用路由 ---
# 这个路由会自动在 templates/index.html 找到文件
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test_page():
    """Route to serve the minimal test page."""
    return render_template('test.html')

# 这个路由会自动在 templates/stats.html 找到文件
@app.route('/stats')
def stats_page():
    return render_template('stats.html')

# --- 程序入口 ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)