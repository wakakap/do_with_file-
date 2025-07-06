import os
import sys
import subprocess
import threading
from flask import Flask, jsonify, render_template, request, send_from_directory, abort
import backend_logic as logic

# --- 配置和启动检查 ---
# 获取当前文件所在的目录作为根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 定义各个必要的媒体文件夹路径
MANGA_PAGES_PATH = os.path.join(BASE_DIR, "MANGA_PAGES")
MANGA_COVER_PATH = os.path.join(BASE_DIR, "MANGA_COVER")
JAV_VIDEO_PATH = os.path.join(BASE_DIR, "JAV_VIDEO")
JAV_COVER_PATH = os.path.join(BASE_DIR, "JAV_COVER")
# 定义数据文件的路径
TAGS_FILE_PATH = os.path.join(BASE_DIR, "tags.json")
MAP_FILE_PATH = os.path.join(BASE_DIR, "map.txt")

# 将需要检查的路径放入一个字典，方便遍历
REQUIRED_PATHS = {
    "漫畫頁面資料夾 (MANGA_PAGES_PATH)": MANGA_PAGES_PATH,
    "漫畫封面資料夾 (MANGA_COVER_PATH)": MANGA_COVER_PATH,
    "影片資料夾 (JAV_VIDEO_PATH)": JAV_VIDEO_PATH,
    "影片封面資料夾 (JAV_COVER_PATH)": JAV_COVER_PATH,
}
# 启动时检查所有必要的文件夹是否存在，如果不存在则打印错误信息并退出程序
for name, path in REQUIRED_PATHS.items():
    if not os.path.isdir(path):
        print(f"!!! 啟動錯誤：必要的「{name}」不存在或不是一個有效的目錄。")
        print(f"    請手動建立或在 app.py 中檢查路徑設定： {os.path.abspath(path)}")
        sys.exit(1)
# 启动时检查数据文件，如果不存在则打印警告信息
if not os.path.isfile(TAGS_FILE_PATH): print(f"!!! 啟動警告：標籤檔案 'tags.json' 不存在，標籤功能將無法使用。")
if not os.path.isfile(MAP_FILE_PATH): print(f"!!! 啟動警告：封面映射檔案 'map.txt' 不存在，將僅使用直接檔名匹配封面。")

# 初始化 Flask 应用
app = Flask(__name__)
# 配置 Flask 返回的 JSON 不使用 ASCII 编码，以正确显示中文等字符
app.config['JSON_AS_ASCII'] = False

# --- 全局数据加载 ---
# 在应用启动时，一次性从文件加载所有标签和封面映射规则到内存中
all_tags = logic.load_tags(TAGS_FILE_PATH)
cover_map = logic.load_cover_map(MAP_FILE_PATH)
print("--- 應用程式啟動 ---")
print(f"--- 已成功載入 {len(all_tags)} 個項目的標籤 ---")
print(f"--- 已成功載入 {len(cover_map)} 條封面映射規則 ---")

# --- 线程锁 ---
auto_import_lock = threading.Lock()

# --- 辅助函数 ---
def get_paths_for_mode(mode):
    """根据前端请求的模式（'JAV' 或 'MANGA'），返回对应的内容和封面路径。"""
    if mode.upper() == 'JAV': return JAV_VIDEO_PATH, JAV_COVER_PATH
    return MANGA_PAGES_PATH, MANGA_COVER_PATH

def is_safe_path(base_path, requested_path):
    """安全检查函数，防止路径遍历攻击。确保请求的路径是在指定的根目录之下。"""
    # 将路径转换为真实的绝对路径，以防止符号链接等攻击
    abs_base = os.path.realpath(base_path)
    abs_req = os.path.realpath(requested_path)
    # 检查请求路径是否以基础路径开头
    return abs_req.startswith(abs_base)

# --- API 路由 ---

@app.route('/api/gallery')
def api_gallery():
    """API端点：获取指定画廊（即以'_'结尾的特殊目录）内的所有图片列表。"""
    mode = request.args.get('mode', 'MANGA') # 获取模式
    gallery_req_path = request.args.get('path', '') # 获取请求的画廊路径
    root_path, _ = get_paths_for_mode(mode)
    
    # 安全性检查：确保请求的路径是有效的，并且在允许访问的根目录内
    if not gallery_req_path or not is_safe_path(root_path, gallery_req_path):
        return jsonify({"error": "Access Denied or Invalid Path"}), 403
        
    # 调用后端逻辑获取图片列表
    images = logic.get_gallery_images(gallery_req_path)
    return jsonify(images)

@app.route('/api/browse')
def api_browse():
    """API端点：浏览指定目录下的文件和文件夹。"""
    mode = request.args.get('mode', 'MANGA')
    root_path, cover_path = get_paths_for_mode(mode)
    # 如果前端没有提供 'path' 参数，则默认为根目录
    req_path = request.args.get('path', root_path)
    
    # 安全性检查：防止访问允许范围之外的目录
    if not is_safe_path(root_path, req_path):
        return jsonify({"error": "Access Denied"}), 403
        
    # 调用后端逻辑获取目录内容
    items = logic.get_directory_items(req_path, root_path, cover_path, all_tags, cover_map)
    # 将当前路径和项目列表一同返回给前端
    return jsonify({ "current_path": req_path, "items": items })

@app.route('/api/search')
def api_search():
    """API端点：根据关键词或标签进行搜索。"""
    mode = request.args.get('mode', 'MANGA')
    query = request.args.get('q', '') # 搜索查询词
    search_type = request.args.get('type', 'keyword') # 搜索类型，'keyword' 或 'tag'
    if not query: return jsonify({"search_term": "", "items": []})
    
    root_path, cover_path = get_paths_for_mode(mode)
    
    # 根据搜索类型调用不同的后端逻辑函数
    if search_type == 'tag':
        items = logic.search_by_tag(root_path, cover_path, all_tags, cover_map, query)
    else:
        items = logic.search_all(root_path, cover_path, all_tags, cover_map, query)
        
    return jsonify({ "search_term": query, "items": items })

@app.route('/api/media/<mode>/<type>/<path:filepath>')
def api_get_media(mode, type, filepath):
    """API端点：提供媒体文件（如封面、漫画页、视频）。这是一个通用的文件服务路由。"""
    root_path, cover_path = get_paths_for_mode(mode)
    
    # 根据请求的 type 决定文件所在的基础路径
    if type == 'cover':
        base_path = cover_path
    elif mode.upper() == 'JAV' and type == 'video':
        base_path = JAV_VIDEO_PATH
    elif mode.upper() == 'MANGA' and type == 'pages':
        base_path = MANGA_PAGES_PATH
    else:
        abort(404) # 如果模式和类型组合无效，则返回404错误
    
    # 使用安全的方式拼接路径
    full_path = os.path.normpath(os.path.join(base_path, filepath))
    
    # 再次进行安全检查，确保最终路径没有越界
    if not is_safe_path(base_path, full_path):
        abort(404)
        
    # 使用 Flask 的 send_from_directory 函数安全地发送文件
    directory = os.path.dirname(full_path)
    filename = os.path.basename(full_path)
    return send_from_directory(directory, filename)

@app.route('/api/open_folder')
def api_open_folder():
    """API端点：在服务器的桌面上打开指定的文件夹。这是一个本地应用功能。"""
    path = request.args.get('path', '')
    if not path or not os.path.exists(path): return jsonify({"status": "error", "message": "Path not found."}), 404
    
    # 安全性检查：确保要打开的目录在 MANGA 或 JAV 的根目录之下
    if not (is_safe_path(MANGA_PAGES_PATH, path) or is_safe_path(JAV_VIDEO_PATH, path)): 
        return jsonify({"status": "error", "message": "Access Denied"}), 403
        
    try:
        # 根据不同操作系统，使用不同的命令打开文件夹
        if sys.platform == "win32":
            # 如果是目录，直接打开；如果是文件，打开其所在的目录
            os.startfile(path if os.path.isdir(path) else os.path.dirname(path))
        elif sys.platform == "darwin": # macOS
            subprocess.call(["open", path])
        else: # Linux
            subprocess.call(["xdg-open", path])
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- 新的维护功能 API 端点 ---

@app.route('/api/auto_import_tags', methods=['POST'])
def api_auto_import_tags():
    """API端点：触发基于项目名称的自动Tag导入（调用爬虫逻辑）。"""
    if not auto_import_lock.acquire(blocking=False):
    # 如果无法获取锁，说明有其他导入操作正在进行
        return jsonify({"status": "error", "message": "另一个导入操作正在进行，请稍后再试。"}), 429
    try:
        # 确保请求是 JSON 格式
        if not request.is_json:
            return jsonify({"status": "error", "message": "请求必须是JSON格式。"}), 400
        
        data = request.get_json()
        item_name = data.get('item_name')

        if not item_name:
            return jsonify({"status": "error", "message": "未提供 'item_name'。"}), 400

        # 调用后端的爬虫和解析逻辑
        result = logic.auto_import_tags(item_name)
        
        # 根据后端逻辑的返回结果，向前台返回成功或失败的响应
        if result['status'] == 'success':
            return jsonify(result)
        else:
            return jsonify(result), 500
    finally:
        # 确保在操作完成后释放锁
        auto_import_lock.release()

@app.route('/api/tags', methods=['GET', 'POST'])
def api_tags():
    """API端点：用于获取和保存标签数据。"""
    global all_tags # 声明我们将要修改全局变量 all_tags
    
    # 如果是 GET 请求，直接返回当前内存中的所有标签
    if request.method == 'GET':
        return jsonify(all_tags)
    
    # 如果是 POST 请求，用于保存新的标签数据
    if request.method == 'POST':
        if not request.is_json:
            return jsonify({"status": "error", "message": "Invalid request: Content-Type must be application/json."}), 400
        
        new_tags_data = request.get_json()
        # 调用后端逻辑函数，将新数据保存到 tags.json 文件
        result = logic.save_tags(TAGS_FILE_PATH, new_tags_data)
        
        if result['status'] == 'success':
            # 保存成功后，重新从文件加载标签到内存，确保数据同步
            all_tags = logic.load_tags(TAGS_FILE_PATH)
            print(f"--- 已成功保存並重新載入 {len(all_tags)} 個項目的標籤 ---")
            return jsonify(result)
        else:
            return jsonify(result), 500

@app.route('/api/generate_covers', methods=['POST'])
def api_generate_covers():
    """API端点：触发封面生成过程。这是一个耗时操作，因此在后台线程中运行。"""
    if not request.is_json:
        return jsonify({"status": "error", "message": "Invalid request: Content-Type must be application/json."}), 400
        
    data = request.get_json()
    mode = data.get('mode', 'MANGA')
    current_path = data.get('path', '')

    root_path, cover_path = get_paths_for_mode(mode)

    # 安全检查
    if not current_path or not is_safe_path(root_path, current_path):
         return jsonify({"status": "error", "message": "Invalid or unsafe path provided."}), 400

    # 定义一个工作函数，将在新线程中执行
    def worker():
        print(f"--- 開始生成封面，掃描路徑: {current_path} ---")
        result = logic.generate_covers_logic(current_path, cover_path, cover_map)
        print(f"--- 封面生成完畢: {result['generated_count']} 個新封面。 臨時目錄: {result['temp_path']} ---")

    # 创建并启动一个守护线程来执行封面生成，这样API可以立即返回，不会阻塞
    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()

    # 立即返回响应，告知前端任务已在后台开始
    return jsonify({
        "status": "started", 
        "message": "Cover generation process has been started in the background. Check the server console for completion status."
    })

# --- 主应用路由 ---
@app.route('/')
def index():
    """主页路由，渲染并返回 index.html 前端页面。"""
    return render_template('index.html')

# --- 程序入口 ---
if __name__ == '__main__':
    # 启动 Flask 开发服务器，监听所有网络接口的 5000 端口
    app.run(host='0.0.0.0', port=5000, debug=True)