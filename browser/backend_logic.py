import os
import re
import json
import shutil
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from serpapi import GoogleSearch

# --- 配置 ---
# ChromeDriver 的路径，如果已添加到系统 PATH，可以省略
CHROMEDRIVER_PATH = "E:\\下载\\picture\\chromedriver.exe" 
# 支持的图片文件扩展名
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.gif']

# --- 辅助函数 ---
def natural_sort_key(s):
    """
    提供自然排序的键。例如，可以正确地将 "item 2" 排在 "item 10" 之前。
    它通过分离字符串中的文本和数字部分来进行排序。
    """
    # 移除括号和方括号内的内容，避免影响排序
    removal_pattern = r'\([^)]*\)|\[[^\]]*\]'
    cleaned_s = re.sub(removal_pattern, '', s)
    # 查找字符串中的第一个数字序列
    match = re.search(r'\d+', cleaned_s)
    if not match: 
        # 如果没有数字，则按纯文本排序
        return (cleaned_s.strip().lower(), 0)
    # 分离文本部分和数字部分
    text_part = cleaned_s[:match.start()].strip().lower()
    num_part = int(match.group(0))
    # 返回一个元组，排序时会先比较文本部分，再比较数字部分
    return (text_part, num_part)

def _get_view_count(item_data):
    """从项目数据中提取总访问次数。"""
    for tag in item_data.get("tags", []):
        # 寻找格式为 '*' 跟着纯数字的tag
        if tag.startswith('*') and tag[1:].isdigit():
            try:
                return int(tag[1:])
            except ValueError:
                continue # 如果转换失败，则忽略此tag
    return 0

def load_tags(tags_file_path):
    """从指定的 JSON 文件加载标签数据。"""
    try:
        if os.path.exists(tags_file_path):
            with open(tags_file_path, 'r', encoding='utf-8') as f: 
                return json.load(f)
        return {}
    except (json.JSONDecodeError, IOError): 
        # 如果文件不存在、为空或格式错误，返回一个空字典
        return {}

def load_cover_map(map_file_path):
    """从 map.txt 文件加载封面映射规则。"""
    cover_map = []
    if not os.path.exists(map_file_path): return cover_map
    try:
        with open(map_file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                # 跳过空行、注释行或格式不正确的行
                if not line or line.startswith('#') or ',' not in line: continue
                # 文件格式为：源文件名正则表达式,封面文件名模板
                parts = line.split(',', 1)
                source_regex_str, cover_template_str = parts[0].strip(), parts[1].strip()
                try:
                    # 编译正则表达式，并添加到映射列表中
                    regex_obj = re.compile(f"^{source_regex_str}$", re.IGNORECASE)
                    cover_map.append((regex_obj, cover_template_str))
                except re.error as e: 
                    # 如果正则表达式无效，则打印警告
                    print(f"警告: map.txt 第 {i} 行存在無效的正規表示式: {source_regex_str}\n錯誤: {e}")
    except Exception as e: 
        print(f"讀取 map.txt 檔案失敗: {e}")
    return cover_map

def find_cover_filename(cover_path, base_name, cover_map):
    """根据基础名称（不含扩展名）和映射规则，在封面目录中查找对应的封面文件名。"""
    if not os.path.isdir(cover_path): return None
    # 尝试直接匹配同名文件
    for ext in IMAGE_EXTENSIONS:
        potential_cover_name = base_name + ext
        if os.path.exists(os.path.join(cover_path, potential_cover_name)): 
            return potential_cover_name
    # 使用 map.txt 中的映射规则    
    for regex_obj, cover_template_str in cover_map:
        match_left = regex_obj.match(base_name)
        if match_left:
            try:
                captured_vars = match_left.groupdict() # 获取正则捕获的命名组
                # 对捕获到的变量进行转义，以安全地用于构建新的正则表达式
                escaped_vars = {k: re.escape(v) for k, v in captured_vars.items()}
                # 使用捕获的变量填充封面文件名模板
                final_cover_regex_str = cover_template_str.format(**escaped_vars)
                final_cover_regex_obj = re.compile(f"^{final_cover_regex_str}$", re.IGNORECASE)
                # 遍历封面目录，查找匹配最终规则的文件
                for f in os.listdir(cover_path):
                    if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS and final_cover_regex_obj.match(os.path.splitext(f)[0]):
                        return f
            except (KeyError, re.error): 
                # 如果模板格式化失败或正则错误，则跳过此规则
                continue
    return None

def _create_item_data(full_path, root_path, cover_path, all_tags, cover_map):
    """为单个文件或目录创建一个标准化的数据字典，供前端使用。"""
    item_name = os.path.basename(full_path)
    name_no_ext = os.path.splitext(item_name)[0]
    is_dir = os.path.isdir(full_path)
    # 计算相对于媒体根目录的路径，用于构建API URL
    media_path = os.path.relpath(full_path, root_path)
    return {
        "name": item_name,
        "name_no_ext": name_no_ext,
        "full_path": full_path,
        "media_path": media_path.replace('\\', '/'), # 统一路径分隔符为'/'
        "is_dir": is_dir,
        "is_special_dir": is_dir and item_name.endswith('_'), # 以'_'结尾的目录是特殊目录（画廊）
        "tags": all_tags.get(name_no_ext, []), # 从内存中的标签数据获取标签
        "cover_filename": find_cover_filename(cover_path, name_no_ext, cover_map) # 查找封面
    }

def get_directory_items(current_path, root_path, cover_path, all_tags, cover_map):
    """获取指定目录下的所有项目（文件和子目录）的列表。"""
    results = []
    try:
        # 使用自然排序对目录内容进行排序
        for item_name in sorted(os.listdir(current_path), key=natural_sort_key):
            if item_name.startswith('.'): # 忽略隐藏文件
                continue
            full_path = os.path.join(current_path, item_name)
            results.append(_create_item_data(full_path, root_path, cover_path, all_tags, cover_map))
        return results
    except Exception as e:
        return {"error": str(e)}

def get_gallery_images(gallery_path):
    """获取特殊目录（画廊）内的所有图片文件，并进行自然排序。"""
    try:
        all_files = os.listdir(gallery_path)
        # 筛选出图片文件
        image_files = [f for f in all_files if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS]
        # 对图片进行自然排序
        sorted_images = sorted(image_files, key=natural_sort_key)
        return sorted_images
    except Exception as e:
        return {"error": str(e)}

def search_all(root_path, cover_path, all_tags, cover_map, keyword):
    """在指定根目录下递归搜索所有匹配关键词的项目。"""
    keyword_lower = keyword.lower() # 转换为小写以进行不区分大小写的比较
    found_paths = set() # 使用集合来自动去重
    for root, dirs, files in os.walk(root_path):
        all_item_names = dirs + files
        for item_name in all_item_names:
            # 检查文件名是否匹配
            if keyword_lower in item_name.lower():
                found_paths.add(os.path.join(root, item_name))
                continue
            item_key = os.path.splitext(item_name)[0]
            item_tags = all_tags.get(item_key, [])
            # 检查标签是否匹配
            for tag in item_tags:
                if keyword_lower in tag.lower():
                    found_paths.add(os.path.join(root, item_name))
                    break
        # 优化：不进入特殊目录（画廊）内部进行搜索，因为它们被视为一个整体
        dirs[:] = [d for d in dirs if not d.endswith('_')]
    # 将找到的路径转换为标准项目数据格式并排序
    results = [_create_item_data(p, root_path, cover_path, all_tags, cover_map) for p in sorted(list(found_paths), key=lambda p: natural_sort_key(os.path.basename(p)))]
    return results

def search_by_tag(root_path, cover_path, all_tags, cover_map, tag_name):
    """根据指定的标签名进行搜索。"""
    # 1. 首先从所有标签中筛选出包含目标标签的项目键名
    tagged_item_keys = {key for key, tags in all_tags.items() if tag_name in tags}
    found_paths = set()
    # 2. 遍历文件系统，查找键名匹配的项目
    for root, dirs, files in os.walk(root_path):
        all_item_names = dirs + files
        for item_name in all_item_names:
            item_key = os.path.splitext(item_name)[0]
            if item_key in tagged_item_keys:
                found_paths.add(os.path.join(root, item_name))
        dirs[:] = [d for d in dirs if not d.endswith('_')]
    results = [_create_item_data(p, root_path, cover_path, all_tags, cover_map) for p in sorted(list(found_paths), key=lambda p: natural_sort_key(os.path.basename(p)))]
    return results

# --- 新的维护功能函数 ---

def get_stats_data(tags_file_path):
    """
    解析 tags.json 文件，提取所有项目的访问统计数据。
    """
    stats = []
    all_tags_data = load_tags(tags_file_path)
    
    for item_key, tags in all_tags_data.items():
        total_views = 0
        page_views = {}
        
        # 寻找总访问量tag
        total_view_tag = next((t for t in tags if t.startswith('*') and t[1:].isdigit()), None)
        if total_view_tag:
            total_views = int(total_view_tag[1:])
        
        # 寻找页面访问量tag
        page_view_tags = [t for t in tags if t.startswith('*p')]
        for tag in page_view_tags:
            # 格式: *p<num>:<count>
            match = re.match(r'\*p(\d+):(\d+)', tag)
            if match:
                page_num = match.group(1)
                count = int(match.group(2))
                page_views[page_num] = count
        
        # 只有在有访问记录时才添加到统计中
        if total_views > 0 or page_views:
            stats.append({
                "item_key": item_key,
                "total_views": total_views,
                "page_views": page_views
            })
            
    # 按总访问量从高到低排序
    sorted_stats = sorted(stats, key=lambda x: x['total_views'], reverse=True)
    return sorted_stats

def save_tags(tags_file_path, tags_data):
    """将前端发来的标签数据保存到 tags.json 文件中，并进行排序。"""
    try:
        # --- 排序逻辑 ---
        tag_counts = {}
        for tags_list in tags_data.values():
            # 只统计非计数的普通标签
            for tag in [t for t in tags_list if not t.startswith('*')]:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        sorted_global_tags = sorted(tag_counts.keys(), key=lambda tag: (tag_counts[tag], tag), reverse=True)
        tag_order_map = {tag: i for i, tag in enumerate(sorted_global_tags)}
        
        sorted_tags_data = {}
        for item_key, tags_list in tags_data.items():
            if isinstance(tags_list, list):
                # 分离访问计数标签和普通标签
                view_tags = [t for t in tags_list if t.startswith('*')]
                normal_tags = [t for t in tags_list if not t.startswith('*')]
                
                # 只对普通标签进行排序
                sorted_normal_tags = sorted(normal_tags, key=lambda tag: tag_order_map.get(tag, 9999))
                
                # 将访问计数标签放回列表前面，然后跟上排序后的普通标签
                sorted_tags_data[item_key] = view_tags + sorted_normal_tags
            else:
                sorted_tags_data[item_key] = tags_list

        with open(tags_file_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_tags_data, f, indent=4, ensure_ascii=False)
        return {"status": "success", "message": "Tags saved successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def update_view_count(tags_file_path, item_key, page_index=None):
    """
    更新指定项目或其页面的访问次数。
    这是一个独立的、快速的读-改-写操作，不涉及复杂的排序。
    """
    try:
        tags_data = load_tags(tags_file_path)
        item_tags = tags_data.get(item_key, [])
        
        # 定义要查找和更新的标签前缀
        # page_index 为 None 时，是总访问量；否则是页面访问量
        if page_index is None:
            # 总访问量格式: *123
            prefix = '*'
            view_tag_index = -1
            for i, tag in enumerate(item_tags):
                # 确保它是一个纯粹的数字计数标签
                if tag.startswith(prefix) and tag[1:].isdigit():
                    view_tag_index = i
                    break
            
            if view_tag_index != -1:
                old_tag = item_tags[view_tag_index]
                count = int(old_tag[len(prefix):]) + 1
                item_tags[view_tag_index] = f"{prefix}{count}"
            else:
                item_tags.insert(0, f"{prefix}1")
        else:
            # 页面访问量格式: *p1:25
            page_num = page_index + 1
            prefix = f'*p{page_num}:'
            view_tag_index = -1
            for i, tag in enumerate(item_tags):
                if tag.startswith(prefix):
                    view_tag_index = i
                    break
            
            if view_tag_index != -1:
                old_tag = item_tags[view_tag_index]
                count = int(old_tag[len(prefix):]) + 1
                item_tags[view_tag_index] = f"{prefix}{count}"
            else:
                item_tags.insert(0, f"{prefix}1")

        tags_data[item_key] = item_tags
        
        with open(tags_file_path, 'w', encoding='utf-8') as f:
            json.dump(tags_data, f, indent=4, ensure_ascii=False)
            
        return {"status": "success"}
    except Exception as e:
        print(f"Error updating view count for '{item_key}': {e}")
        return {"status": "error", "message": str(e)}

def generate_covers_logic(path_to_scan, cover_path, cover_map):
    """
    扫描指定路径，为没有封面的特殊目录（以'_'结尾）生成封面。
    它会复制特殊目录中的第一张图片到一个临时文件夹中。
    """
    temp_cover_path = os.path.join(cover_path, "temp_generated_covers")
    os.makedirs(temp_cover_path, exist_ok=True) # 确保临时目录存在
    generated_count = 0
    errors = []

    for root, dirs, _ in os.walk(path_to_scan):
        for dir_name in list(dirs):
            if not dir_name.endswith('_'):
                continue
            
            dirs.remove(dir_name)
            
            base_name = dir_name[:-1]
            if find_cover_filename(cover_path, dir_name, cover_map) is None:
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
                        
                        if not os.path.exists(dest_file):
                            shutil.copy2(source_file, dest_file)
                            generated_count += 1
                except Exception as e:
                    errors.append(f"Error processing '{special_dir_path}': {e}")
    
    return {
        "status": "completed",
        "generated_count": generated_count,
        "temp_path": temp_cover_path,
        "errors": errors
    }

def auto_import_tags(item_name):
    """
    自动导入标签的核心逻辑。
    步骤：1. Google搜索 -> 2. 获取DMM链接 -> 3. Selenium打开链接 -> 4. 处理年龄确认 -> 5. BS4解析页面 -> 6. 提取Tags
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return {"status": "error", "message": "SERPAPI_API_KEY 环境变量未设置。"}
    
    cleaned_name = item_name[:-1] if item_name.endswith('_') else item_name
    search_query = f'{cleaned_name} dmm'
    print(f"正在为 '{cleaned_name}' 自动导入Tag，搜索查询: '{search_query}'")
    
    try:
        params = {"q": search_query, "engine": "google", "google_domain": "google.co.jp", "gl": "jp", "hl": "ja", "api_key": api_key}
        search = GoogleSearch(params)
        results = search.get_dict()
        dmm_url = next((res["link"] for res in results.get("organic_results", []) if "dmm" in res.get("link", "")), None)
        if not dmm_url:
            return {"status": "error", "message": "在搜索结果首页未找到 dmm 的链接。"}
        print(f"找到DMM链接: {dmm_url}")
    except Exception as e:
        return {"status": "error", "message": f"Google搜索阶段出错: {e}"}

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = None
    try:
        service = Service(CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(dmm_url)

        print("正在检查是否存在年龄确认或'OFF'按钮...")
        confirmation_handled = False

        try:
            age_check_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'age_check')][contains(., 'はい')]"))
            )
            print("发现'はい'年龄确认按钮，正在处理...")
            original_window = driver.current_window_handle
            age_check_button.click()
            WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
            for window_handle in driver.window_handles:
                if window_handle != original_window:
                    driver.switch_to.window(window_handle)
                    break
            print("已成功切换到新标签页。")
            driver.close()
            driver.switch_to.window(original_window)
            confirmation_handled = True
            print("'はい'按钮处理完毕。")
        except TimeoutException:
            print("未在5秒内找到'はい'按钮，接下来检查'OFF'按钮。")

        if not confirmation_handled:
            try:
                off_switch = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[./span[text()='OFF']]"))
                )
                print("发现'OFF'切换按钮，正在点击...")
                driver.execute_script("arguments[0].click();", off_switch)
                confirmation_handled = True
                print("'OFF'按钮处理完毕。")
            except TimeoutException:
                print("也未在5秒内找到'OFF'按钮。")

        if not confirmation_handled:
            print("最终未发现任何需要处理的确认按钮，将直接继续。")

        print("等待最终页面内容加载...")
        commercial_page_loaded = EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), '作品詳細')]"))
        doujin_page_loaded = EC.presence_of_element_located((By.CSS_SELECTOR, ".author a, .informationList"))
        WebDriverWait(driver, 20).until(EC.any_of(commercial_page_loaded, doujin_page_loaded))
        print("最终页面关键元素已加载。")
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        found_tags = set()

        if "/doujin/" in driver.current_url:
            print("解析 Doujin 页面...")
            found_tags.add("同人")
            author_icon = soup.select_one('span[class*="author"]')
            if author_icon:
                author_tag = author_icon.find_next_sibling('a')
            if author_tag:
                author_name = author_tag.get_text(strip=True)
                found_tags.add(author_name)
                print(f"找到作者: {author_name}")
            else:
                print("警告: 未能定位到作者。")
            info_texts = soup.select('.informationList__txt')
            for txt in info_texts:
                if match := re.search(r'(\d{4})/\d{2}/\d{2}', txt.get_text()):
                    found_tags.add(match.group(1))
                    break
        else:
            print("解析商业作品页面...")
            details_header = soup.find('h2', string=re.compile(r'^\s*作品詳細\s*$'))
            if details_header:
                details_section = details_header.find_parent()
                info_items = details_section.find_all('dl')
                for item in info_items:
                    label_tag = item.find('dt'); data_tag = item.find('dd')
                    if not (label_tag and data_tag): continue
                    label_text = label_tag.get_text(strip=True)
                    if "作家" == label_text:
                        if author_link := data_tag.find('a'): found_tags.add(author_link.get_text(strip=True))
                    elif "掲載誌・レーベル" == label_text:
                        if label_link := data_tag.find('a'): found_tags.add(label_link.get_text(strip=True))
                    elif "配信開始日" == label_text:
                        if match := re.search(r'(\d{4})/\d{2}/\d{2}', data_tag.get_text()): found_tags.add(match.group(1))
                    elif "カテゴリー" == label_text:
                        if category_link := data_tag.find('a'): 
                            text = category_link.get_text(strip=True)[:2]
                            if text == "アダ": text = "成人"
                            found_tags.add(text)
            else:
                print("警告：在最终页面中仍未找到 '作品詳細' 标题。")

        print(f"抓取完成，找到的Tags: {list(found_tags)}")
        return {"status": "success", "tags": list(found_tags)}

    except Exception as e:
        print(f"Selenium抓取过程中发生错误: {e}")
        return {"status": "error", "message": f"Selenium抓取失败: {e}"}
    finally:
        if driver:
            driver.quit()
