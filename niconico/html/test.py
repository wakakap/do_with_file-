import asyncio
import os
import subprocess
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright, Page
import time # 引入时间模块

# --- 配置区 ---
CONFIG = {
    "STATS_ASS_PATH": "E:/抽吧唧/章鱼p/1/doublesub.ass",  # 统计用的ASS文件
    "DANMAKU_ASS_PATH": "E:/抽吧唧/章鱼p/1/20250709_so45124910_comments_CH_extend.ass",  # 弹幕用的ASS文件
    "OUTPUT_VIDEO_PATH": "D:/章鱼p/output_smooth.mp4",     # 输出视频路径
    "TEMP_FRAME_DIR": "D:/章鱼p/render_temp",         # 存放截图的临时文件夹
    "NUM_BARS": 30,                            # 条目数 (n)
    # --- 实验关键参数 ---
    "RENDER_DURATION_SECONDS": 3,             # 渲染时长 (秒)
    "RENDER_FPS": 60,                          # 渲染帧率
    
    "BROWSER_VIEWPORT_SIZE": {"width": 1920, "height": 1080},
}

async def capture_frames_diagnostic(page: Page, config: dict):
    """用于诊断的截图循环"""
    print("诊断开始：将以期望的60 FPS速度进行截图，持续5秒...")
    
    chart_container = page.locator("#chart-container")
    temp_dir = Path(config["TEMP_FRAME_DIR"])
    total_expected_frames = int(config["RENDER_DURATION_SECONDS"] * config["RENDER_FPS"])
    
    # 精确计时开始
    start_time = time.perf_counter()

    for i in range(total_expected_frames):
        frame_path = temp_dir / f"frame_{i:06d}.png"
        await chart_container.screenshot(path=str(frame_path))
        # 注意：这里不再使用asyncio.sleep()，因为我们想测试的是
        # 截图操作本身能达到的最快速度，而不是人为限制它。
        # 在一个理想的、性能无限的计算机上，这个循环会瞬间完成。
        # 在真实计算机上，它的速度受限于CPU、磁盘I/O等。
    
    # 精确计时结束
    end_time = time.perf_counter()
    
    elapsed_time = end_time - start_time
    
    # 统计实际生成的文件数量
    actual_frames_captured = len(os.listdir(temp_dir))
    
    # 计算实际平均FPS
    actual_fps = actual_frames_captured / elapsed_time if elapsed_time > 0 else 0
    
    # 打印诊断报告
    print("\n" + "="*50)
    print("--- 帧率诊断报告 ---")
    print(f"期望持续时间: {config['RENDER_DURATION_SECONDS']} 秒")
    print(f"期望截取帧数: {total_expected_frames} 帧 (5秒 * 60fps)")
    print("-" * 20)
    print(f"实际总耗时: {elapsed_time:.4f} 秒")
    print(f"实际截取帧数: {actual_frames_captured} 帧")
    print(f"实际平均FPS: {actual_fps:.2f} 帧/秒")
    print("="*50 + "\n")

async def main():
    """主执行函数"""
    render_html_path = Path("E:/Github/do_with_file-/niconico/html/render.html").resolve()
    if not render_html_path.exists():
        print(f"错误: 未找到 'render.html' 文件。")
        return

    temp_dir = Path(CONFIG["TEMP_FRAME_DIR"])
    if temp_dir.exists():
        # 确保从一个干净的状态开始
        import shutil
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=[
                "--use-gl=desktop", 
                "--enable-gpu", 
                "--allow-file-access-from-files"])
        page = await browser.new_page(viewport=CONFIG["BROWSER_VIEWPORT_SIZE"])
        
        stats_ass_url = Path(CONFIG["STATS_ASS_PATH"]).resolve().as_uri()
        danmaku_ass_url = Path(CONFIG["DANMAKU_ASS_PATH"]).resolve().as_uri()
        url = (
            f"{render_html_path.as_uri()}?"
            f"stats_ass={quote(stats_ass_url)}&"
            f"danmaku_ass={quote(danmaku_ass_url)}&"
            f"n={CONFIG['NUM_BARS']}"
        )
        
        print("正在加载HTML页面...")
        ready_signal = asyncio.get_running_loop().create_future()
        page.on("console", lambda msg: "---KEYFRAMES-GENERATED---" in msg.text and not ready_signal.done() and ready_signal.set_result(True))
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.wait_for(ready_signal, timeout=300)
            print("页面加载和动画准备就绪，开始诊断...")
            
            await capture_frames_diagnostic(page, CONFIG)

        except Exception as e:
            print(f"诊断过程中发生错误: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())