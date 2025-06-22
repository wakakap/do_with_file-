import os
import re
import requests
import sys
import time

# --- 配置区 ---

# GPT-SoVITS API接口地址
API_URL = "http://localhost:9880/tts"
# 模型路径 (请确保路径正确)
GPT_WEIGHTS_PATH = "D:\\GPT-SoVITS_\\GPT-SoVITS-v4-20250422fix\\GPT_weights_v4\\zundamon-e10.ckpt"
SOVITS_WEIGHTS_PATH = "D:\\GPT-SoVITS_\\GPT-SoVITS-v4-20250422fix\\SoVITS_weights_v4\\zundamon_e1_s99_l32.pth"

# 英文替换为中文的对应表 (不区分大小写)
EN_TO_ZH_MAP = {
    'amazon': '亚马逊',
    'abema': '啊百马',
    # 在这里添加更多对应关系，例如:
    'google': '谷歌',
    'youtube': '油管',
    'twitter': '推特',
    'facebook': '脸书',
    'instagram': '因斯特古拉姆',
    'tver': '梯瓦儿',
    'netflix': '网飞',
    'disney': '迪士尼',
    'hulu': '呼噜',
    'line': '烂',
    'mono': '莫诺',
    'u-next': '优奈克斯特',
    'niconico': '妮口妮口',
    'at-x': '艾踢艾克斯',
    'ani-one': '阿尼碗',
    'bilibili': '哔哩哔哩',
    'ip': '哀劈',
    'dj': '缔结',
    'wotagei': '哦塔盖',
    'call' : '靠',
    'egoist': '伊狗斯特',
    'sekin': '塞可因',
    'himehina': '黑莓黑呐',
    'vtuber': '微吐呗儿',
    'hime': '黑莓',
    'hina': '黑呐',
    'bubblin': '巴布林',
    'nijisanji': '彩虹社',
    'hololive': '喉楼莱芜',
    'dancehall': '当斯后',
    'echo': '伊口',
    'kizunaai': '绊爱',
}

# API请求参数
GPT_SOVITS_PARAMS = {
    # 参考音频设置
    "ref_audio_path": "D:\\GPT-SoVITS_\\zundamon\\今日は最高の一日だった！課題とか全然やってないけど、まぁ、明日頑張ればいいよね.wav",
    "prompt_text": "今日は最高の一日だった！課題とか全然やってないけど、まぁ、明日頑張ればいいよね",
    "prompt_lang": "ja",
    # 默认的文本和语言设置
    "text_lang": "zh",  # 可选: ja, zh, en
    # 合成参数
    "top_k": 5, 
    "top_p": 1, 
    "temperature": 1, 
    "text_split_method": 
    "cut5",
    "batch_size": 1, 
    "batch_threshold": 0.75, 
    "split_bucket": True,
    "speed_factor": 1.15, 
    "fragment_interval": 0.3, 
    "seed": -1,
    "parallel_infer": True, 
    "media_type": "wav", 
    "streaming_mode": False,
    "repetition_penalty": 1.35, 
    "sample_steps": 24, 
    "super_sampling": False,
}

def switch_models(gpt_path, sovits_path):
    """切换GPT和SoVITS模型"""
    print("\n--- 🔄 正在切换模型 ---")
    # 切换GPT模型
    if gpt_path:
        print(f"  切换GPT模型: {os.path.basename(gpt_path)}")
        try:
            r = requests.get(f"http://127.0.0.1:9880/set_gpt_weights", params={"weights_path": gpt_path}, timeout=20)
            if r.ok and r.json().get("message") == "success": print("  ✔️ GPT模型切换成功。")
            else: print(f"  ❌ GPT模型切换失败。状态码: {r.status_code}"); return False
        except requests.exceptions.RequestException as e: print(f"  ❌ 切换GPT模型时网络错误: {e}"); return False
    # 切换SoVITS模型
    if sovits_path:
        print(f"  切换SoVITS模型: {os.path.basename(sovits_path)}")
        try:
            r = requests.get(f"http://127.0.0.1:9880/set_sovits_weights", params={"weights_path": sovits_path}, timeout=20)
            if r.ok and r.json().get("message") == "success": print("  ✔️ SoVITS模型切换成功。")
            else: print(f"  ❌ SoVITS模型切换失败。状态码: {r.status_code}"); return False
        except requests.exceptions.RequestException as e: print(f"  ❌ 切换SoVITS模型时网络错误: {e}"); return False
    print("--- ✅ 模型切换完成 ---\n")
    return True

def parse_srt_file(file_path):
    """解析SRT文件，提取字幕序号和文本"""
    print(f"🔍 正在解析SRT文件: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
    except Exception as e: print(f"❌ 错误: 无法读取SRT文件，原因: {e}"); return None
    pattern = re.compile(r'(\d+)\s*\n(?:\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3})\s*\n([\s\S]*?)(?=\n\n|\Z)', re.MULTILINE)
    subtitles = [{'index': m.group(1), 'text': ' '.join(m.group(2).strip().splitlines())} for m in pattern.finditer(content)]
    if subtitles: print(f"✅ 找到 {len(subtitles)} 条字幕。")
    else: print("⚠️ 警告: 文件中未找到有效的字幕条目。")
    return subtitles

def sanitize_filename(text, max_length=50):
    """清理文本，使其可以安全地用作文件名的一部分。"""
    sanitized = re.sub(r'[\\/*?:"<>|]', '', text)
    sanitized = sanitized.replace(' ', '')
    return sanitized[:max_length]

def replace_english_words(text):
    """根据 EN_TO_ZH_MAP 表，将文本中的英文单词替换为对应的中文。"""
    if not any(c.isalpha() for c in text): return text # 如果没有字母，直接返回
    def get_replacement(match):
        word = match.group(0)
        return EN_TO_ZH_MAP.get(word.lower(), word) # 查找小写版本，找不到则返回原词
    return re.sub(r'[a-zA-Z]+(?:-[a-zA-Z]+)*', get_replacement, text, flags=re.IGNORECASE)

def generate_audio_for_text(text, text_lang, output_path):
    if os.path.exists(output_path):
        print(f"   ⚠️ 文件已存在，跳过合成: {os.path.basename(output_path)}")
        return True # 无需执行
    payload = GPT_SOVITS_PARAMS.copy()
    payload['text'], payload['text_lang'] = text, text_lang
    print(f"   合成中 (语言: {text_lang}): \"{text[:50]}...\"")
    try:
        response = requests.post(API_URL, json=payload, timeout=120)
        if response.ok and 'audio/wav' in response.headers.get('Content-Type', ''):
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"   ✔️ 音频已保存: {os.path.basename(output_path)}")
            return True
        else:
            print(f"   ❌ API错误 (状态码: {response.status_code}): {response.text[:250]}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ 网络错误: 无法连接到API服务器 {API_URL}。原因: {e}")
        return False

def main():
    srt_file_path = "E:\\抽吧唧\\himehina\\pr.srt"
    output_dir = "E:\\抽吧唧\\himehina\\sub"
    os.makedirs(output_dir, exist_ok=True)

    if not switch_models(GPT_WEIGHTS_PATH, SOVITS_WEIGHTS_PATH): sys.exit(1)
    subtitles = parse_srt_file(srt_file_path)
    if not subtitles: sys.exit(1)

    total, success_count = len(subtitles), 0
    print(f"\n🚀 开始为 {total} 条字幕生成音频...")

    for i, sub in enumerate(subtitles):
        print(f"\n--- 处理字幕 {i+1}/{total} (序号: {sub['index']}) ---")

        # 1. 语言识别和'|'分割
        raw_text = sub['text']
        target_lang = GPT_SOVITS_PARAMS['text_lang']
        if raw_text.strip().startswith('j:'):
            target_lang = 'ja'
            text_for_filename = raw_text.strip()[2:].strip()
            print("   检测到 'j:' 前缀，语言切换为日语。")
        else:
            text_for_filename = raw_text.strip()
        text_for_filename = text_for_filename.split('|')[0].strip()

        if not text_for_filename:
            print("   ⚠️ 文本预处理后为空，跳过此字幕。")
            continue

        # 2. 生成文件名 (使用替换前的文本)
        safe_text = sanitize_filename(text_for_filename)
        output_filename = f"{sub['index'].zfill(4)}_{target_lang}_{safe_text}.wav"
        output_filepath = os.path.join(output_dir, output_filename)

        # 3. 英文替换 (仅用于语音合成)
        text_for_synthesis = replace_english_words(text_for_filename)
        if text_for_synthesis != text_for_filename:
            print(f"   英文词替换: \"{text_for_filename}\" -> \"{text_for_synthesis}\"")

        # 4. 生成音频
        if generate_audio_for_text(text_for_synthesis, target_lang, output_filepath):
            success_count += 1
        time.sleep(0.5)

    print(f"\n🎉 处理完成！成功生成 {success_count}/{total} 个文件。输出目录: {output_dir}")

if __name__ == "__main__":
    # 要运行完整的SRT处理流程，请取消下面一行的注释
    main()

    ####### 临时测试区 #######
    # if not switch_models(GPT_WEIGHTS_PATH, SOVITS_WEIGHTS_PATH): sys.exit(1)
    # output_dir = "E:\\抽吧唧"
    # os.makedirs(output_dir, exist_ok=True)
    # # 测试文本 (包含j:前缀, |忽略部分, 和需要替换的英文)
    # raw_text_to_test = "j:パクチソン 体操"
    # print(f"\n--- 运行单条文本测试 ---\n原始文本: \"{raw_text_to_test}\"")
    # # 1. 语言识别和'|'分割
    # target_lang = GPT_SOVITS_PARAMS['text_lang']
    # if raw_text_to_test.strip().startswith('j:'):
    #     target_lang = 'ja'
    #     text_for_filename = raw_text_to_test.strip()[2:].strip()
    #     print("   检测到 'j:' 前缀，语言切换为日语。")
    # else:
    #     text_for_filename = raw_text_to_test.strip()
    # text_for_filename = text_for_filename.split('|')[0].strip()
    # # 2. 生成文件名
    # if text_for_filename:
    #     safe_text = sanitize_filename(text_for_filename)
    #     output_filename = f"0000_{target_lang}_{safe_text}.wav"
    #     output_filepath = os.path.join(output_dir, output_filename)
    #     # 3. 英文替换
    #     text_for_synthesis = replace_english_words(text_for_filename)
    #     if text_for_synthesis != text_for_filename:
    #         print(f"   英文词替换: \"{text_for_filename}\" -> \"{text_for_synthesis}\"")
    #     # 4. 生成音频
    #     generate_audio_for_text(text_for_synthesis, target_lang, output_filepath)