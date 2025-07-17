# 帮我根据这个html，做成一个用于渲染的html和对应的python文件。注意用于渲染的html会完全放弃掉触发视频的相关功能，并放弃音乐播放的功能，除了这两个其他的功能请忠实于元html。特别注意关于动画的播放问题，我的元html中有播放的参数playbackSpeed，这个值和速率等于1时的数量关系，是我期望的播放样子，所以如果你修改后，要保证python和html交互过程中按这个速度播放原动画，帧率参数只是会改变这个播放速度下的插帧数量。隐藏控制按钮等部分。还有其他能设置的参数，添加到python文件中，例如两个ass文件路径，条目数，速度（这里的速度等于原速度上的跳帧），渲染时长（渲染测试用），最后一帧延长时间（默认5秒），渲染帧率默认30，渲染大小默认19201080，临时文件夹路径等等. 渲染尽可能地使用gpu n卡加速，而且会把截图保存在临时文件夹，可供中断后，下次同样参数运行时能继续。给我完整render.html和render.py的代码。

import asyncio
import os
import subprocess
import json
from playwright.async_api import async_playwright
import time

# ==============================================================================
# CONFIGURATION
# ==============================================================================
# --- File Paths ---
# Path to the .ass file used for counting statistics and driving the bar chart
STATS_ASS_PATH = "E:/抽吧唧/章鱼p/1/doublesub.ass"
# Path to the .ass file used for displaying scrolling/static danmaku comments
DANMAKU_ASS_PATH = "E:/抽吧唧/章鱼p/1/20250709_so45124910_comments_CH_extend.ass"
# Path to the local render.html file you just saved
HTML_FILE_PATH = "E:/Github/do_with_file-/niconico/html/render.html"
# Directory to store temporary PNG frames. This will be created if it doesn't exist.
TEMP_DIR = "D:/章鱼p/render_temp"
# Final output video file name.
OUTPUT_FILENAME = "D:/章鱼p/output_smooth.mp4"

# --- Rendering Parameters ---
# The number of bars to display on the chart.
NUM_BARS = 30
# Speed multiplier. 1.0 is the original intended speed. 2.0 is double speed.
# This works by "skipping" time, not by dropping frames.
SPEED_MULTIPLIER = 1.0
# Optional: Set a specific duration to render in seconds.
# If set to None, the script will render the entire animation.
# Example: RENDER_DURATION_S = 60 # Renders the first 60 seconds of the animation.
RENDER_DURATION_S = 5 
# How many seconds to hold the very last frame of the animation.
END_FRAME_HOLD_S = 5
# Frames per second for the output video. Higher FPS means smoother animation.
FPS = 30
# Resolution of the output video.
RESOLUTION = (1920, 1080)

# --- Advanced Settings ---
# If True, the script will look for existing frames in TEMP_DIR and
# continue rendering where it left off.
CONTINUE_RENDER = True
# If True, tries to use hardware acceleration for both browser rendering and ffmpeg encoding.
# Requires a supported NVIDIA GPU and correctly configured drivers.
USE_GPU_ACCELERATION = True
# Fallback video encoder if NVIDIA ('h264_nvenc') is not available or fails.
# 'libx264' is a high-quality software encoder.
CPU_ENCODER = 'libx264'
# ==============================================================================

async def main():
    """Main function to control the rendering process."""
    
    # --- 1. Initial Setup and Validation ---
    print("--- Initializing Render ---")
    
    if not os.path.exists(STATS_ASS_PATH) or not os.path.exists(DANMAKU_ASS_PATH):
        print(f"Error: Cannot find ASS files.")
        print(f"Checked for STATS_ASS_PATH: '{STATS_ASS_PATH}'")
        print(f"Checked for DANMAKU_ASS_PATH: '{DANMAKU_ASS_PATH}'")
        return

    html_file_url = f'file://{os.path.abspath(HTML_FILE_PATH)}'
    os.makedirs(TEMP_DIR, exist_ok=True)

    start_frame = 0
    if CONTINUE_RENDER:
        existing_frames = [f for f in os.listdir(TEMP_DIR) if f.endswith('.png')]
        if existing_frames:
            start_frame = len(existing_frames)
            print(f"Found {start_frame} existing frames. Resuming render.")

    # --- 2. Launch Browser and Load Page ---
    async with async_playwright() as p:
        print("Launching browser...")
        browser_args = []
        if USE_GPU_ACCELERATION:
             browser_args.extend(['--enable-gpu', '--use-gl=desktop'])

        browser = await p.chromium.launch(headless=True, args=browser_args)
        page = await browser.new_page()
        await page.set_viewport_size({"width": RESOLUTION[0], "height": RESOLUTION[1]})
        
        print(f"Loading HTML file: {html_file_url}")
        await page.goto(html_file_url)

        # --- 3. Initialize Chart with Data ---
        print("Reading ASS files and initializing chart...")
        with open(STATS_ASS_PATH, 'r', encoding='utf-8') as f:
            stats_ass_text = f.read()
        with open(DANMAKU_ASS_PATH, 'r', encoding='utf-8') as f:
            danmaku_ass_text = f.read()

        js_config = {
            "numBars": NUM_BARS,
            "width": RESOLUTION[0],
            "height": RESOLUTION[1]
        }
        
        try:
            init_result = await page.evaluate(
                '([stats, danmaku, config]) => window.initialize(stats, danmaku, config)',
                [stats_ass_text, danmaku_ass_text, js_config]
            )
            animation_duration = init_result['duration']
            print(f"Initialization complete. Total animation duration: {animation_duration:.2f} seconds.")
        except Exception as e:
            print(f"\nError during page initialization in JavaScript:\n{e}")
            await browser.close()
            return

        # --- 4. Render Frames ---
        render_duration = RENDER_DURATION_S if RENDER_DURATION_S is not None else animation_duration
        total_anim_frames = int(render_duration * FPS)
        total_hold_frames = int(END_FRAME_HOLD_S * FPS)
        total_frames_to_render = total_anim_frames + total_hold_frames
        
        print(f"--- Starting Frame Capture ---")
        print(f"Resolution: {RESOLUTION[0]}x{RESOLUTION[1]} @ {FPS}fps")
        print(f"Will render {total_frames_to_render} total frames.")
        
        chart_container = page.locator('#chart-container')

        start_time = time.time()
        for frame_num in range(start_frame, total_frames_to_render):
            # Calculate the effective time in the animation
            # This accounts for the speed multiplier
            anim_time_s = (frame_num / FPS) * SPEED_MULTIPLIER
            
            # If we are past the animation part, hold the last frame
            if frame_num >= total_anim_frames:
                anim_time_s = (total_anim_frames / FPS) * SPEED_MULTIPLIER

            # Cap the time at the actual end of the animation
            effective_time = min(anim_time_s, animation_duration)

            # Call the JS function to render this specific time
            await page.evaluate('time => window.renderFrame(time)', effective_time)
            
            # Take screenshot
            frame_path = os.path.join(TEMP_DIR, f'frame_{frame_num:06d}.png')
            await chart_container.screenshot(path=frame_path)
            
            # Progress reporting
            elapsed = time.time() - start_time
            if frame_num > start_frame and (frame_num - start_frame) % 10 == 0:
                frames_done = frame_num - start_frame
                fps_render = frames_done / elapsed if elapsed > 0 else 0
                print(f"Rendered frame {frame_num}/{total_frames_to_render-1} | "
                      f"Video time: {effective_time:.2f}s | "
                      f"Render speed: {fps_render:.2f} fps", end='\r')

        print(f"\n--- Frame Capture Complete in {time.time() - start_time:.2f}s ---")
        await browser.close()

    # --- 5. Encode Video with FFmpeg ---
    print("--- Starting Video Encoding ---")
    frame_pattern = os.path.join(TEMP_DIR, 'frame_%06d.png')
    
    ffmpeg_cmd = [
        'ffmpeg',
        '-y',  # Overwrite output file if it exists
        '-r', str(FPS),  # Set frame rate
        '-i', frame_pattern,  # Input files
        '-c:v', 'h264_nvenc' if USE_GPU_ACCELERATION else CPU_ENCODER, # Video codec
        '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
        '-b:v', '15M', # Set a good bitrate for 1080p
        OUTPUT_FILENAME
    ]
    
    print(f"Executing FFmpeg command: {' '.join(ffmpeg_cmd)}")
    
    try:
        subprocess.run(ffmpeg_cmd, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"\nFFmpeg encoding with '{ffmpeg_cmd[6]}' failed: {e}")
        if USE_GPU_ACCELERATION:
            print(f"Falling back to CPU encoder '{CPU_ENCODER}'...")
            ffmpeg_cmd[6] = CPU_ENCODER
            try:
                subprocess.run(ffmpeg_cmd, check=True)
                print("Video encoded successfully with CPU.")
            except Exception as cpu_e:
                print(f"CPU encoding also failed: {cpu_e}")
                return
        else:
             print("Aborting video encoding.")
             return

    print(f"--- Video Encoding Complete ---")
    print(f"Output saved to: {OUTPUT_FILENAME}")
    
if __name__ == '__main__':
    asyncio.run(main())