import os
import time
import re
import requests

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# ====== 配置参数 ======
URL_LIST_FILE = 'E:\\BROWSER\\urls.txt'
SAVE_ROOT = 'E:\\BROWSER\\dl'
CHROMEDRIVER_PATH = 'E:\\下载\\picture\\chromedriver.exe'
SCROLL_PAUSE_TIME = 3
MAX_IDLE_ROUNDS = 9

# ====== Selenium 初始化 ======
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--log-level=3')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=chrome_options)

# ====== 工具函数 ======

def sanitize_filename(name):
    """去掉 Windows/Unix 不允许的字符"""
    return re.sub(r'[\\/:*?"<>|]', '_', name)


def scroll_to_load_all_images(driver, pause_time=2, max_idle_rounds=5):
    """
    无限下拉加载，直到图片数连续几轮没有增加
    """
    previous_count = 0
    idle_rounds = 0

    while idle_rounds < max_idle_rounds:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)

        images = driver.find_elements(By.TAG_NAME, 'img')
        current_count = len(images)
        print(f"  📷 当前已加载图片数: {current_count}")

        if current_count <= previous_count:
            idle_rounds += 1
            print(f"  ⚠️ 没有新图片（空转 {idle_rounds}/{max_idle_rounds}）")
        else:
            idle_rounds = 0

        previous_count = current_count

    print(f"✅ 滚动加载完成，总图片数: {previous_count}")


def extract_image_urls(driver):
    images = driver.find_elements(By.TAG_NAME, 'img')
    urls = []
    for img in images:
        src = img.get_attribute('src')
        if src and src.startswith('http'):
            urls.append(src)
    return urls


def download_images(img_urls, save_folder):
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    # 先数一数现有图片数
    existing_files = [f for f in os.listdir(save_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    existing_count = len(existing_files)
    print(f"✅ 目标文件夹已有 {existing_count} 张图片，将从 {existing_count + 1} 开始命名")

    # 继续下载剩下的
    for idx, url in enumerate(img_urls[existing_count:], start=existing_count + 1):
        filename = f"{idx:03}.jpg"
        filepath = os.path.join(save_folder, filename)
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                print(f"    ✔️ 已保存: {filename}")
            else:
                print(f"    ⚠️ 下载失败，状态码 {response.status_code}: {url}")
        except Exception as e:
            print(f"    ⚠️ 错误: {e}")



def process_url(url):
    print(f"\n=== 处理: {url} ===")
    driver.get(url)
    time.sleep(3)

    # 无限滚动加载
    scroll_to_load_all_images(driver, pause_time=SCROLL_PAUSE_TIME, max_idle_rounds=MAX_IDLE_ROUNDS)

    # 获取网页标题作为子文件夹名
    title = driver.title.strip()
    folder_name = sanitize_filename(title)
    sub_folder = os.path.join(SAVE_ROOT, folder_name)

    print(f"✅ 网页标题: {title}")

    # 提取图片链接
    img_urls = extract_image_urls(driver)
    print(f"✅ 共找到图片: {len(img_urls)} 张")

    if not img_urls:
        print("⚠️ 没有找到图片，跳过。")
        return

    # 下载
    download_images(img_urls, sub_folder)
    print(f"✅ 已全部保存到: {sub_folder}")


def main():
    # 确保总保存文件夹存在
    if not os.path.exists(SAVE_ROOT):
        os.makedirs(SAVE_ROOT)

    # 读取URL列表
    if not os.path.isfile(URL_LIST_FILE):
        print(f"❌ 未找到文件: {URL_LIST_FILE}")
        return

    with open(URL_LIST_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]

    if not urls:
        print("❌ 文件里没有任何网址")
        return

    print(f"✅ 读取到 {len(urls)} 个网址。")

    # 逐个处理
    for url in urls:
        try:
            process_url(url)
        except Exception as e:
            print(f"❌ 处理失败: {url}\n错误: {e}")

    driver.quit()
    print("\n🎉 所有任务完成。")


if __name__ == '__main__':
    main()
