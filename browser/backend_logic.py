import os
import re
import json

IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.gif']

# natural_sort_key, load_tags, load_cover_map 等函式保持不變...
def natural_sort_key(s):
    removal_pattern = r'\([^)]*\)|\[[^\]]*\]'
    cleaned_s = re.sub(removal_pattern, '', s)
    match = re.search(r'\d+', cleaned_s)
    if not match: return (cleaned_s.strip().lower(), 0)
    text_part = cleaned_s[:match.start()].strip().lower()
    num_part = int(match.group(0))
    return (text_part, num_part)

def load_tags(tags_file_path):
    try:
        if os.path.exists(tags_file_path):
            with open(tags_file_path, 'r', encoding='utf-8') as f: return json.load(f)
        return {}
    except (json.JSONDecodeError, IOError): return {}

def load_cover_map(map_file_path):
    cover_map = []
    if not os.path.exists(map_file_path): return cover_map
    try:
        with open(map_file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#') or ',' not in line: continue
                parts = line.split(',', 1)
                source_regex_str, cover_template_str = parts[0].strip(), parts[1].strip()
                try:
                    regex_obj = re.compile(f"^{source_regex_str}$", re.IGNORECASE)
                    cover_map.append((regex_obj, cover_template_str))
                except re.error as e: print(f"警告: map.txt 第 {i} 行存在無效的正規表示式: {source_regex_str}\n錯誤: {e}")
    except Exception as e: print(f"讀取 map.txt 檔案失敗: {e}")
    return cover_map

def find_cover_filename(cover_path, base_name, cover_map):
    if not os.path.isdir(cover_path): return None
    for regex_obj, cover_template_str in cover_map:
        match_left = regex_obj.match(base_name)
        if match_left:
            try:
                captured_vars = match_left.groupdict()
                escaped_vars = {k: re.escape(v) for k, v in captured_vars.items()}
                final_cover_regex_str = cover_template_str.format(**escaped_vars)
                final_cover_regex_obj = re.compile(f"^{final_cover_regex_str}$", re.IGNORECASE)
                for f in os.listdir(cover_path):
                    if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS and final_cover_regex_obj.match(os.path.splitext(f)[0]):
                        return f
            except (KeyError, re.error): continue
    for ext in IMAGE_EXTENSIONS:
        potential_cover_name = base_name + ext
        if os.path.exists(os.path.join(cover_path, potential_cover_name)): return potential_cover_name
    return None

# --- 修改此函式 ---
def _create_item_data(full_path, root_path, cover_path, all_tags, cover_map):
    """輔助函式，根據一個完整路徑建立一個項目字典"""
    item_name = os.path.basename(full_path)
    name_no_ext = os.path.splitext(item_name)[0]
    is_dir = os.path.isdir(full_path)
    
    # 計算相對於媒體根目錄的路徑
    media_path = os.path.relpath(full_path, root_path)

    return {
        "name": item_name,
        "name_no_ext": name_no_ext,
        "full_path": full_path, # 絕對路徑，用於瀏覽
        "media_path": media_path.replace('\\', '/'), # 相對路徑，用於請求媒體資源，統一使用'/'
        "is_dir": is_dir,
        "is_special_dir": is_dir and item_name.endswith('_'),
        "tags": all_tags.get(name_no_ext, []),
        "cover_filename": find_cover_filename(cover_path, name_no_ext, cover_map)
    }

# --- 修改此函式以傳遞 root_path ---
def get_directory_items(current_path, root_path, cover_path, all_tags, cover_map):
    results = []
    try:
        for item_name in sorted(os.listdir(current_path), key=natural_sort_key):
            if item_name.startswith('.'):
                continue
            full_path = os.path.join(current_path, item_name)
            results.append(_create_item_data(full_path, root_path, cover_path, all_tags, cover_map))
        return results
    except Exception as e:
        return {"error": str(e)}

def get_gallery_images(gallery_path):
    try:
        all_files = os.listdir(gallery_path)
        image_files = [f for f in all_files if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS]
        sorted_images = sorted(image_files, key=natural_sort_key)
        return sorted_images
    except Exception as e:
        return {"error": str(e)}

# --- 修改此函式以傳遞 root_path ---
def search_all(root_path, cover_path, all_tags, cover_map, keyword):
    keyword_lower = keyword.lower()
    found_paths = set()
    
    for root, dirs, files in os.walk(root_path):
        all_item_names = dirs + files
        for item_name in all_item_names:
            if keyword_lower in item_name.lower():
                found_paths.add(os.path.join(root, item_name))
                continue
            item_key = os.path.splitext(item_name)[0]
            item_tags = all_tags.get(item_key, [])
            for tag in item_tags:
                if keyword_lower in tag.lower():
                    found_paths.add(os.path.join(root, item_name))
                    break
        dirs[:] = [d for d in dirs if not d.endswith('_')]
        
    results = [_create_item_data(p, root_path, cover_path, all_tags, cover_map) for p in sorted(list(found_paths), key=lambda p: natural_sort_key(os.path.basename(p)))]
    return results

# --- 修改此函式以傳遞 root_path ---
def search_by_tag(root_path, cover_path, all_tags, cover_map, tag_name):
    tagged_item_keys = {key for key, tags in all_tags.items() if tag_name in tags}
    found_paths = set()
    
    for root, dirs, files in os.walk(root_path):
        all_item_names = dirs + files
        for item_name in all_item_names:
            item_key = os.path.splitext(item_name)[0]
            if item_key in tagged_item_keys:
                found_paths.add(os.path.join(root, item_name))
        dirs[:] = [d for d in dirs if not d.endswith('_')]

    results = [_create_item_data(p, root_path, cover_path, all_tags, cover_map) for p in sorted(list(found_paths), key=lambda p: natural_sort_key(os.path.basename(p)))]
    return results