import os
from dotenv import load_dotenv
from googleapiclient.discovery import build

# --- 新增部分 ---
# 在脚本开头调用 load_dotenv()
# 它会自动查找当前目录下的 .env 文件并加载
load_dotenv()

# 使用 os.getenv() 来安全地获取环境变量中的API密钥
api_key = os.getenv('YOUTUBE_API_KEY')
# -----------------

# 检查API密钥是否成功加载
if not api_key:
    # 如果 .env 文件或其中的变量不存在，api_key 会是 None，程序将在这里退出
    raise ValueError("未找到API密钥。请检查您的 .env 文件中是否正确设置了 'YOUTUBE_API_KEY'。")

# --- 其余代码保持不变 ---

# 1. 设置频道ID
channel_id = 'UCFv2z4iM5vHrS8bZPq4fHQQ'

# 2. 创建YouTube API服务对象
youtube = build('youtube', 'v3', developerKey=api_key)

# 3. 构建请求
request = youtube.channels().list(
    part='snippet,statistics',
    id=channel_id
)

# 4. 执行请求并获取响应
response = request.execute()

# 5. 解析并打印结果
if 'items' in response and len(response['items']) > 0:
    channel_info = response['items'][0]
    
    title = channel_info['snippet']['title']
    subscriber_count = channel_info['statistics']['subscriberCount']
    view_count = channel_info['statistics']['viewCount']
    video_count = channel_info['statistics']['videoCount']
    
    print(f"频道名称: {title}")
    print(f"订阅人数: {subscriber_count} 人")
    print(f"总观看量: {view_count} 次")
    print(f"视频总数: {video_count} 个")
else:
    print("未能找到该频道或API请求失败。")