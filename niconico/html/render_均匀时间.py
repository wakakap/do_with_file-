import asyncio
import subprocess
import argparse
import pathlib
import tempfile
import json
from playwright.async_api import async_playwright
from tqdm import tqdm

# --- CONFIGURATION ---
OUTPUT_RESOLUTION = (1920, 1080)
OUTPUT_FPS = 30
# Path to the HTML file created in Step 1
HTML_FILE_PATH = pathlib.Path(__file__).parent / "render_均匀时间.html"
# How long the D3.js transition animation is (in seconds).
# Must match `rankChangeAnimationDuration` in the JS code (450ms = 0.45s)
TRANSITION_DURATION = 0.45

async def render_video(ass_file: str, video_file: str, output_file: str, item_count: int, speed: float):
    """
    Renders the bar chart race animation to a video file.
    """
    ass_path = pathlib.Path(ass_file).resolve()
    video_path = pathlib.Path(video_file).resolve()
    html_uri = HTML_FILE_PATH.as_uri()
    video_uri = video_path.as_uri()

    if not ass_path.is_file():
        print(f"Error: ASS file not found at {ass_path}")
        return
    if not video_path.is_file():
        print(f"Error: Video file not found at {video_path}")
        return

    print("--- Starting Browser Automation ---")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': OUTPUT_RESOLUTION[0], 'height': OUTPUT_RESOLUTION[1]},
            device_scale_factor=1,
        )
        page = await context.new_page()

        # Go to the local HTML file
        await page.goto(html_uri)

        # Read ASS content and escape it for JS
        print(f"Reading ASS file: {ass_path.name}")
        ass_content = ass_path.read_text(encoding='utf-8')
        js_escaped_ass_content = json.dumps(ass_content)

        # 1. Initialize the chart with data and parameters
        print("Initializing animation... (This may take a moment)")
        await page.evaluate(f"window.automation.setParameters({item_count}, {speed})")
        
        init_result = await page.evaluate(f"window.automation.loadDataAndInitialize({js_escaped_ass_content}, '{video_uri}')")
        
        total_keyframes = init_result.get("frameCount", 0)
        if total_keyframes == 0:
            print("Error: No keyframes were generated. Check the ASS file.")
            await browser.close()
            return

        print(f"Initialization complete. Found {total_keyframes} keyframes.")

        with tempfile.TemporaryDirectory() as temp_dir:
            frame_dir = pathlib.Path(temp_dir)
            print(f"Temporary frame directory: {frame_dir}")
            
            # 2. Start the animation state in JS
            await page.evaluate("window.automation.start()")
            
            time_per_keyframe_step = TRANSITION_DURATION / speed
            frames_to_capture_per_step = int(time_per_keyframe_step * OUTPUT_FPS)
            wait_time_between_screenshots = (1 / OUTPUT_FPS) * 1000  # in ms
            
            frame_number = 0
            
            # 3. Loop through each keyframe and capture the transition
            print("--- Starting Frame Capture ---")
            with tqdm(total=total_keyframes, unit="keyframe") as pbar:
                for i in range(total_keyframes):
                    # Advance the bar chart to the next state, which starts the transition animation
                    keyframe_info = await page.evaluate("window.automation.renderNextStep()")
                    
                    if keyframe_info['done']:
                        break
                    
                    current_anim_time = keyframe_info['time']
                    
                    # Capture the animation between keyframes
                    for j in range(frames_to_capture_per_step):
                        # Calculate the precise time for this screenshot within the transition
                        seek_time = current_anim_time + (j * (1 / OUTPUT_FPS))
                        await page.evaluate(f"window.automation.seekTo({seek_time})")

                        # Give the browser a moment to render the seeked frame
                        await page.wait_for_timeout(5) 

                        screenshot_path = frame_dir / f"frame-{frame_number:06d}.png"
                        await page.screenshot(path=screenshot_path)
                        frame_number += 1
                        
                    pbar.update(1)

            await browser.close()
            print(f"\n--- Frame capture complete. Captured {frame_number} frames. ---")

            # 4. Use FFmpeg to compile frames into a video
            print("--- Starting Video Compilation with FFmpeg ---")
            
            ffmpeg_command = [
                'ffmpeg',
                '-framerate', str(OUTPUT_FPS),          # Input frame rate
                '-i', f'{frame_dir}/frame-%06d.png',      # Input image sequence
                '-i', str(video_path),                   # Input audio source
                '-c:v', 'libx264',                       # Video codec
                '-crf', '20',
                '-pix_fmt', 'yuv420p',                   # Pixel format for compatibility
                '-c:a', 'aac',                           # Audio codec
                '-b:a', '192k',                          # Audio bitrate
                '-shortest',                             # Finish when the shortest input (images) ends
                '-y',                                    # Overwrite output file if it exists
                str(output_file)
            ]

            process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                print(f"\n✅ Success! Video saved to: {output_file}")
            else:
                print("\n❌ FFmpeg compilation failed. Error:")
                print(stderr.decode())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render a bar chart race animation from an ASS file.")
    parser.add_argument("ass_file", help="Path to the input .ass file.")
    parser.add_argument("video_file", help="Path to the source video file (for audio and video clips).")
    parser.add_argument("-o", "--output", default="output.mp4", help="Path to the output video file (default: output.mp4).")
    
    # Add arguments for the specific request
    parser.add_argument("-n", "--items", type=int, default=40, help="Number of bars to display (条目数).")
    parser.add_argument("-s", "--speed", type=float, default=1.0, help="Animation speed multiplier (速度倍率).")

    args = parser.parse_args()

    # Run the main async function
    # Added your specific parameters as the default values
    asyncio.run(render_video(
        ass_file=args.ass_file,
        video_file=args.video_file,
        output_file=args.output,
        item_count=args.items,
        speed=args.speed
    ))