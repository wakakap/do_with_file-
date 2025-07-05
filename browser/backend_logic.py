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
CHROMEDRIVER_PATH = "E:\\下载\\picture\\chromedriver.exe" 


IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.gif']

# --- Helper Functions (No changes needed) ---
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

def _create_item_data(full_path, root_path, cover_path, all_tags, cover_map):
    item_name = os.path.basename(full_path)
    name_no_ext = os.path.splitext(item_name)[0]
    is_dir = os.path.isdir(full_path)
    media_path = os.path.relpath(full_path, root_path)
    return {
        "name": item_name,
        "name_no_ext": name_no_ext,
        "full_path": full_path,
        "media_path": media_path.replace('\\', '/'),
        "is_dir": is_dir,
        "is_special_dir": is_dir and item_name.endswith('_'),
        "tags": all_tags.get(name_no_ext, []),
        "cover_filename": find_cover_filename(cover_path, name_no_ext, cover_map)
    }

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

# --- NEW FUNCTIONS FOR MAINTENANCE ---

def save_tags(tags_file_path, tags_data):
    """
    Saves the tags data to tags.json, including sorting logic.
    """
    try:
        # Sorting logic from local_browser.py
        tag_counts = {}
        for tags_list in tags_data.values():
            for tag in tags_list:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        sorted_global_tags = sorted(tag_counts.keys(), key=lambda tag: (tag_counts[tag], tag), reverse=True)
        tag_order_map = {tag: i for i, tag in enumerate(sorted_global_tags)}
        
        sorted_tags_data = {}
        for item_key, tags_list in tags_data.items():
            # Ensure tags_list is actually a list before sorting
            if isinstance(tags_list, list):
                sorted_tags_for_item = sorted(tags_list, key=lambda tag: tag_order_map.get(tag, 9999))
                sorted_tags_data[item_key] = sorted_tags_for_item
            else:
                # If for some reason it's not a list, keep it as is to avoid errors
                sorted_tags_data[item_key] = tags_list

        with open(tags_file_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_tags_data, f, indent=4, ensure_ascii=False)
        return {"status": "success", "message": "Tags saved successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def generate_covers_logic(path_to_scan, cover_path, cover_map):
    """
    Generates missing covers for special directories ('*_').
    """
    temp_cover_path = os.path.join(cover_path, "temp_generated_covers")
    os.makedirs(temp_cover_path, exist_ok=True)
    generated_count = 0
    errors = []

    for root, dirs, _ in os.walk(path_to_scan):
        # Create a copy of dirs to iterate over, as we modify it in place
        for dir_name in list(dirs):
            if not dir_name.endswith('_'):
                continue
            
            # This prevents os.walk from going into the special directory
            dirs.remove(dir_name)
            
            base_name = dir_name[:-1]
            # Check if a cover already exists using the same logic as find_cover_filename
            if find_cover_filename(cover_path, base_name, cover_map) is None:
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
                        
                        # To prevent overwriting, check if file exists in temp folder already
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
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return {"status": "error", "message": "SERPAPI_API_KEY 环境变量未设置。"}

    cleaned_name = item_name[:-1] if item_name.endswith('_') else item_name
    search_query = f'{cleaned_name} dmm'
    print(f"正在为 '{cleaned_name}' 自动导入Tag，搜索查询: '{search_query}'")
    
    # 步骤 1: Google搜索获取URL
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

    # 步骤 2: 使用Selenium加载URL并处理页面
    options = Options()
    options.add_argument("--headless") # 在调试时可以注释掉此行，以便亲眼看到浏览器操作
    options.add_argument("--disable-gpu")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = None
    try:
        service = Service(CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(dmm_url)

        # --- 处理年龄确认 ---
        try:
            # 1. 获取原始窗口的句柄
            original_window = driver.current_window_handle
            
            age_check_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'age_check')][contains(., 'はい')]"))
            )
            print("发现年龄确认页面，正在点击 'はい'...")
            
            # 2. 点击按钮 (这会打开新标签页)
            age_check_button.click()
            
            # 3. 等待新标签页出现 (等待窗口数量增加)
            WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
            
            # 4. 找到新标签页的句柄并切换
            for window_handle in driver.window_handles:
                if window_handle != original_window:
                    driver.switch_to.window(window_handle)
                    break
            print("已成功切换到新标签页。")
            
            # 5. (推荐) 关闭旧的标签页
            driver.close()
            # 6. (推荐) 再次将焦点切回我们唯一需要的标签页
            driver.switch_to.window(driver.window_handles[0])

        except TimeoutException:
            print("未发现年龄确认页面，直接在当前页面继续。")

        # --- 等待最终页面内容加载 ---
        print("等待最终页面内容加载...")
        commercial_page_loaded = EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), '作品詳細')]"))
        doujin_page_loaded = EC.presence_of_element_located((By.CSS_SELECTOR, ".author a, .informationList"))

        WebDriverWait(driver, 20).until(EC.any_of(commercial_page_loaded, doujin_page_loaded))
        print("最终页面关键元素已加载。")
        
        # 获取最终页面的源代码并解析
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        found_tags = set()

        # ... 后续解析逻辑保持不变 ...
        if "/doujin/" in driver.current_url: # 使用 driver.current_url 更可靠
            print("解析 Doujin 页面...")
            found_tags.add("同人"); found_tags.add("成人")
            author_tag = None
            # 1. 寻找 class 包含 "author" 的 span 元素
            author_icon = soup.select_one('span[class*="author"]')
            if author_icon:
                # 2. 如果找到，就获取它后面的 a 标签
                author_tag = author_icon.find_next_sibling('a')

            if author_tag:
                author_name = author_tag.get_text(strip=True)
                found_tags.add(author_name)
                print(f"找到作者: {author_name}")
            else:
                print("警告: 未能通过灵活选择器定位到作者。")
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
                        if category_link := data_tag.find('a'): found_tags.add(category_link.get_text(strip=True)[:2])
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