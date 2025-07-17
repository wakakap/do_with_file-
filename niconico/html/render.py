# 帮我根据这个html，做成一个用于渲染的html和对应的python文件。注意用于渲染的html会完全放弃掉触发视频的相关功能，并放弃音乐播放的功能，除了这两个其他的功能请忠实于元html。特别注意关于动画的播放问题，我的元html中有播放的参数playbackSpeed，这个值和速率等于1时的数量关系，是我期望的播放速度，所以希望你保留这样的速度，并保留3d.js的补间动画效果，不要破坏。python只扮演截图和渲染的功能。另外，隐藏控制按钮等部分。在python文件中，设置两个ass文件路径，条目数，渲染时长（渲染测试用），渲染帧率默认60（注意这里的帧率完全不影响原动画播放速度，只影响python截图的频率），临时文件夹路径等等. 渲染尽可能地使用gpu n卡加速，而且会把截图保存在临时文件夹，可供中断后，下次同样参数运行时能继续。给我完整render.html和render.py的代码。

import asyncio
import os
import subprocess
from pathlib import Path
from urllib.parse import quote
from playwright.async_api import async_playwright, Page
from tqdm import tqdm

# --- 配置区 ---
CONFIG = {
    # --- 文件路径 ---
    # 请使用绝对路径，或者确保相对路径相对于此脚本的位置是正确的
    "STATS_ASS_PATH": "E:/抽吧唧/章鱼p/1/doublesub.ass",  # 统计用的ASS文件
    "DANMAKU_ASS_PATH": "E:/抽吧唧/章鱼p/1/20250709_so45124910_comments_CH_extend.ass",  # 弹幕用的ASS文件
    "MUSIC_PATH": None,  # [可选] 背景音乐文件, 如果不需要则设为 None
    "OUTPUT_VIDEO_PATH": "D:/章鱼p/output_smooth.mp4",     # 输出视频路径
    
    # --- 渲染参数 ---
    "TEMP_FRAME_DIR": "D:/章鱼p/render_temp",         # 存放截图的临时文件夹
    "NUM_BARS": 30,                            # 条目数 (n)
    "RENDER_DURATION_SECONDS": 5,             # 渲染时长 (秒)
    "RENDER_FPS_SHOT": 2,                          # 渲染帧率 (受硬件限制了)
    "RENDER_FPS": 30,                          # 渲染帧率
    
    # --- 高级选项 ---
    "CLEANUP_TEMP_DIR": False,                 # 渲染完成后是否删除临时文件夹
    "BROWSER_VIEWPORT_SIZE": {"width": 1920, "height": 1080}, # 浏览器窗口大小
}

async def check_ffmpeg():
    """检查系统中是否存在 ffmpeg"""
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误：未找到 FFmpeg。请确保已安装 FFmpeg 并将其添加至系统环境变量中。")
        return False

async def get_gpu_encoder():
    """检查可用的NVIDIA NVENC编码器"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-h", "encoder=h264_nvenc"],
            check=True,
            capture_output=True,
            text=True
        )
        if "NVIDIA NVENC H.264 encoder" in result.stdout:
            print("检测到 NVIDIA NVENC (h264_nvenc)，将使用GPU加速。")
            return "h264_nvenc"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass # ffmpeg可能不存在或执行失败
    print("警告：未检测到 NVENC。将回退到CPU编码 (libx264)，速度会慢很多。")
    return "libx264"


async def capture_frames(page: Page, config: dict, start_frame: int, total_frames: int):
    """循环截图"""
    print("开始截图...")
    progress_bar = tqdm(initial=start_frame, total=total_frames, unit="frame")
    
    chart_container = page.locator("#chart-container")
    
    for i in range(start_frame, total_frames):
        frame_path = Path(config["TEMP_FRAME_DIR"]) / f"frame_{i:06d}.png"
        
        # 优化截图过程
        await chart_container.screenshot(path=str(frame_path))
        
        await asyncio.sleep(1 / config["RENDER_FPS_SHOT"])
        progress_bar.update(1)
        
    progress_bar.close()
    print("截图完成。")


def compile_video(config: dict, encoder: str):
    """使用 FFmpeg 将帧合成为视频"""
    print("开始使用 FFmpeg 合成视频...")
    temp_dir = Path(config["TEMP_FRAME_DIR"])
    output_path = Path(config["OUTPUT_VIDEO_PATH"])
    music_path = config.get("MUSIC_PATH")

    ffmpeg_cmd = [
        "ffmpeg",
        "-framerate", str(config["RENDER_FPS"]),
        "-i", str(temp_dir / "frame_%06d.png"),
    ]

    if music_path and Path(music_path).exists():
        ffmpeg_cmd.extend(["-i", str(music_path)])
        ffmpeg_cmd.extend(["-c:a", "aac", "-b:a", "192k", "-shortest"]) # 添加音频编码参数
    else:
        if music_path:
            print(f"警告：找不到指定的音乐文件 '{music_path}'，视频将不包含音频。")
        ffmpeg_cmd.extend(["-an"]) # 无音频

    ffmpeg_cmd.extend([
        "-c:v", encoder,
        "-pix_fmt", "yuv420p", # 保证兼容性
        "-y", # 覆盖已存在的文件
        str(output_path)
    ])
    
    # 针对 NVENC 添加优化参数
    if encoder == "h264_nvenc":
        ffmpeg_cmd.extend([
        "-preset", "p7",        # 保持最高质量 preset
        "-tune", "hq",          # 维持高质量优化
        "-rc", "vbr",           # 可变码率（质量优先）
        "-cq", "15",            # **将 cq 从 20 ↓ 到 15**，质量提升明显，文件会更大
        "-b:v", "0"             # 禁用码率限制，完全由 cq 控制输出质量
    ])
    else:
        ffmpeg_cmd.extend([
        "-crf", "17",
        "-preset", "medium",
    ])


    print(f"执行 FFmpeg 命令: {' '.join(ffmpeg_cmd)}")
    
    try:
        subprocess.run(ffmpeg_cmd, check=True)
        print(f"\n视频渲染成功！文件已保存至: {output_path.resolve()}")
    except subprocess.CalledProcessError as e:
        print(f"\n错误：FFmpeg 执行失败。返回码: {e.returncode}")
        print("请检查 FFmpeg 日志输出以获取详细信息。")
    except FileNotFoundError:
        print("\n错误：找不到 FFmpeg。请确保它已安装并位于系统的 PATH 中。")


async def main():
    """主执行函数"""
    if not await check_ffmpeg():
        return

    # 准备工作
    render_html_path = Path("E:/Github/do_with_file-/niconico/html/render.html").resolve()
    if not render_html_path.exists():
        print(f"错误: 未找到 'render.html' 文件，请确保它与此脚本在同一目录下。")
        return

    temp_dir = Path(CONFIG["TEMP_FRAME_DIR"])
    temp_dir.mkdir(exist_ok=True)

    # 计算帧数和断点续传
    total_frames = int(CONFIG["RENDER_DURATION_SECONDS"] * CONFIG["RENDER_FPS"])
    existing_frames = sorted(temp_dir.glob("frame_*.png"))
    start_frame = len(existing_frames)

    if start_frame > 0:
        if start_frame >= total_frames:
            print("检测到所有帧都已存在。将直接进入视频合成阶段。")
        else:
            print(f"检测到 {start_frame} 个已存在的帧。将从第 {start_frame + 1} 帧开始继续渲染。")
    else:
        print("未检测到临时文件，将从头开始渲染。")

    if start_frame < total_frames:
        # 启动浏览器并截图
        async with async_playwright() as p:
            # 尝试启用GPU加速
            browser = await p.chromium.launch(
                headless=False, 
                args=["--use-gl=desktop", 
                      "--enable-gpu", 
                      "--allow-file-access-from-files"]
            )
            page = await browser.new_page(viewport=CONFIG["BROWSER_VIEWPORT_SIZE"])
            
            # 构建URL
            stats_ass_url = Path(CONFIG["STATS_ASS_PATH"]).resolve().as_uri()
            danmaku_ass_url = Path(CONFIG["DANMAKU_ASS_PATH"]).resolve().as_uri()

            url = (
                f"{render_html_path.as_uri()}?"
                f"stats_ass={quote(stats_ass_url)}&"
                f"danmaku_ass={quote(danmaku_ass_url)}&"
                f"n={CONFIG['NUM_BARS']}"
            )
            
            print("正在浏览器中加载HTML并生成关键帧，请稍候...")
            
            # 设置一个 Future 来等待来自页面的信号
            ready_signal = asyncio.get_running_loop().create_future()
            
            def handle_console_message(msg):
                if "---KEYFRAMES-GENERATED---" in msg.text and not ready_signal.done():
                    print("接收到关键帧生成完毕信号！")
                    ready_signal.set_result(True)

            page.on("console", handle_console_message)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.wait_for(ready_signal, timeout=300) # 等待最多5分钟生成关键帧
                
                await capture_frames(page, CONFIG, start_frame, total_frames)

            except asyncio.TimeoutError:
                print("错误：等待关键帧生成信号超时。请检查.ass文件是否过大或格式有误。")
            except Exception as e:
                print(f"渲染过程中发生错误: {e}")
            finally:
                await browser.close()
    
    # 合成视频
    encoder = await get_gpu_encoder()
    compile_video(CONFIG, encoder)

    # 清理临时文件
    if CONFIG["CLEANUP_TEMP_DIR"] and temp_dir.exists():
        print("正在清理临时文件...")
        for file in temp_dir.glob("*"):
            file.unlink()
        temp_dir.rmdir()
        print("清理完成。")


if __name__ == "__main__":
    asyncio.run(main())