# collect_data.py (升级版)
import os
import pandas as pd
from datetime import datetime
from googleapiclient.discovery import build
from dotenv import load_dotenv

# --- 配置 ---
CHANNEL_ID = 'UCFv2z4iM5vHrS8bZPq4fHQQ'
HISTORY_FILE = 'himehina_history.csv'

def get_channel_data(api_key, channel_id):
    """使用YouTube API获取频道的多种统计数据。"""
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        # part参数中增加了snippet，用于获取频道标题等基本信息 # <--- 修改
        request = youtube.channels().list(
            part='snippet,statistics',
            id=channel_id
        )
        response = request.execute()

        if 'items' in response and len(response['items']) > 0:
            item = response['items'][0]
            # 一次性获取所有需要的统计数据 # <--- 修改
            stats = {
                "title": item['snippet']['title'],
                "subscribers": int(item['statistics']['subscriberCount']),
                "views": int(item['statistics']['viewCount']),
                "videos": int(item['statistics']['videoCount'])
            }
            return stats
        else:
            print("错误：未能从API获取数据，请检查频道ID是否正确。")
            return None
    except Exception as e:
        print(f"调用API时发生错误: {e}")
        return None

def main():
    """主函数，执行数据获取和保存。"""
    print("开始执行数据收集任务 (升级版)...")
    
    load_dotenv()
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("错误：未能加载API密钥。请检查 .env 文件。")
        return

    # 获取包含多个指标的频道数据
    channel_data = get_channel_data(api_key, CHANNEL_ID)
    if channel_data is None:
        print("因无法获取频道数据，任务终止。")
        return

    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # 打印所有获取到的数据 # <--- 修改
    print("-" * 30)
    print(f"频道名称: {channel_data['title']}")
    print(f"日期: {current_date}")
    print(f"订阅人数: {channel_data['subscribers']:,}")
    print(f"总观看量: {channel_data['views']:,}")
    print(f"视频总数: {channel_data['videos']:,}")
    print("-" * 30)

    # 准备要写入文件的多列新数据 # <--- 修改
    new_data = pd.DataFrame({
        'date': [current_date],
        'subscribers': [channel_data['subscribers']],
        'views': [channel_data['views']],
        'videos': [channel_data['videos']]
    })

    try:
        if not os.path.exists(HISTORY_FILE):
            print(f"'{HISTORY_FILE}' 不存在，将创建新文件。")
            new_data.to_csv(HISTORY_FILE, index=False)
        else:
            new_data.to_csv(HISTORY_FILE, mode='a', header=False, index=False)
        
        print(f"数据已成功记录到 '{HISTORY_FILE}'。")

    except Exception as e:
        print(f"写入文件时发生错误: {e}")

if __name__ == '__main__':
    main()