import os
import re
import requests
import sys
import time

# --- Configuration ---
# All parameters are set based on your provided 'main.py' file.

# GPT-SoVITS API endpoint
API_URL = "http://localhost:9880/tts"
GPT_WEIGHTS_PATH = "D:\GPT-SoVITS_\GPT-SoVITS-v4-20250422fix\GPT_weights_v4\\zundamon-e10.ckpt"
SOVITS_WEIGHTS_PATH = "D:\\GPT-SoVITS_\\GPT-SoVITS-v4-20250422fix\\SoVITS_weights_v4\\zundamon_e1_s99_l32.pth"
# Parameters for the API request
# Using reference audio is enabled by default as requested.
# Please ensure these paths are correct for your system.
GPT_SOVITS_PARAMS = {
    # Reference Audio Settings
    "ref_audio_path": "D:\\GPT-SoVITS_\\zundamon\\今日は最高の一日だった！課題とか全然やってないけど、まぁ、明日頑張ればいいよね.wav",
    "prompt_text": "今日は最高の一日だった！課題とか全然やってないけど、まぁ、明日頑張ればいいよね",
    "prompt_lang": "ja",

    # Text and Language Settings
    "text_lang": "zh", # ja, zh, en
    
    # Synthesis Parameters
    "top_k": 5,
    "top_p": 1,
    "temperature": 1,
    "text_split_method": "cut5",
    "batch_size": 1,
    "batch_threshold": 0.75,
    "split_bucket": True,
    "speed_factor": 1.15,
    "fragment_interval": 0.3,
    "seed": -1,
    "parallel_infer": True,
    "media_type": "wav",
    "streaming_mode": False,
    "parallel_infer": True,
    "repetition_penalty": 1.35,
    "sample_steps": 16, #32
    "super_sampling": False,
}

def switch_models(gpt_path, sovits_path):
    print("\n--- 🔄 Attempting to switch models ---")
    
    # Switch GPT Model
    if gpt_path:
        print(f"  Switching GPT model to: {gpt_path}")
        try:
            # This logic is based on the /set_gpt_weights endpoint in api_v2.py
            response_gpt = requests.get(f"http://127.0.0.1:9880//set_gpt_weights", params={"weights_path": gpt_path}, timeout=20)
            if response_gpt.status_code == 200 and response_gpt.json().get("message") == "success":
                print("  ✔️ GPT model switched successfully.")
            else:
                print(f"  ❌ Failed to switch GPT model. Status: {response_gpt.status_code}, Response: {response_gpt.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Network error while switching GPT model: {e}")
            return False
    else:
        print("  - Skipping GPT model switch (no path provided).")

    # Switch SoVITS Model
    if sovits_path:
        print(f"  Switching SoVITS model to: {sovits_path}")
        try:
            # This logic is based on the /set_sovits_weights endpoint in api_v2.py
            response_sovits = requests.get(f"http://127.0.0.1:9880//set_sovits_weights", params={"weights_path": sovits_path}, timeout=20)
            if response_sovits.status_code == 200 and response_sovits.json().get("message") == "success":
                print("  ✔️ SoVITS model switched successfully.")
            else:
                print(f"  ❌ Failed to switch SoVITS model. Status: {response_sovits.status_code}, Response: {response_sovits.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Network error while switching SoVITS model: {e}")
            return False
    else:
        print("  - Skipping SoVITS model switch (no path provided).")

    print("--- ✅ Model switching complete ---\n")
    return True


def parse_srt_file(file_path):
    print(f"🔍 Parsing SRT file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ ERROR: SRT file not found at {file_path}")
        return None
    except Exception as e:
        print(f"❌ ERROR: Could not read SRT file. Reason: {e}")
        return None

    # Regex to capture index, timestamp, and text.
    # It handles multiline text within a subtitle block.
    pattern = re.compile(r'(\d+)\s*\n(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s*\n([\s\S]*?)(?=\n\n|\Z)', re.MULTILINE)
    
    subtitles = []
    for match in pattern.finditer(content):
        index = match.group(1)
        # Clean up text: remove leading/trailing whitespace and replace newlines with a space.
        text = ' '.join(match.group(4).strip().splitlines())
        if text: # Only add subtitles that have text
            subtitles.append({'index': index, 'text': text})
            
    if not subtitles:
        print("⚠️ Warning: No valid subtitle entries found in the file.")
    else:
        print(f"✅ Found {len(subtitles)} subtitle entries.")
        
    return subtitles


def generate_audio_for_text(text, output_path):
    """
    Sends a request to the GPT-SoVITS API to generate audio for the given text.

    Args:
        text (str): The text to synthesize.
        output_path (str): The path to save the generated WAV file.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    payload = GPT_SOVITS_PARAMS.copy()
    payload['text'] = text
    
    print(f"   Synthesizing: \"{text[:50]}...\"")
    
    try:
        response = requests.post(API_URL, json=payload, timeout=90)
        
        if response.ok and 'audio/wav' in response.headers.get('Content-Type', ''):
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"   ✔️ Audio saved to: {os.path.basename(output_path)}")
            return True
        else:
            print(f"   ❌ API Error (Status: {response.status_code}): {response.text[:250]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Network Error: Failed to connect to GPT-SoVITS API at {API_URL}.")
        print(f"      Reason: {e}")
        return False
    except Exception as e:
        print(f"   ❌ An unexpected error occurred during API call: {e}")
        return False


def main():
    srt_file_path = "E:\\抽吧唧\\2\\original_zh.srt" #sys.argv[1]
    output_dir = "E:\\抽吧唧\\2\\sub"
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Switch models before starting the main process
    if not switch_models(GPT_WEIGHTS_PATH, SOVITS_WEIGHTS_PATH):
        print("\nAborting due to model switching failure. Please check the API server and model paths.")
        sys.exit(1)
    
    # Parse the SRT file
    subtitles = parse_srt_file(srt_file_path)
    if subtitles is None:
        sys.exit(1) # Exit if file parsing failed
    
    total_subtitles = len(subtitles)
    success_count = 0
    
    print(f"\n🚀 Starting audio generation for {total_subtitles} subtitles...")
    
    # Process each subtitle
    for i, sub in enumerate(subtitles):
        print(f"\n--- Processing subtitle {i+1}/{total_subtitles} (Index: {sub['index']}) ---")
        
        # Format the output filename with leading zeros (e.g., 001.wav, 002.wav)
        output_filename = f"{sub['index'].zfill(4)}.wav"
        output_filepath = os.path.join(output_dir, output_filename)
        
        if generate_audio_for_text(sub['text'], output_filepath):
            success_count += 1
        else:
            print(f"   Skipping to next subtitle due to error.")
        
        # Add a small delay to avoid overwhelming the API server
        time.sleep(0.5)

    print("\n-------------------------------------------")
    print(f"🎉 Processing complete!")
    print(f"   Successfully generated: {success_count}/{total_subtitles} audio files.")
    print(f"   Output directory: {output_dir}")
    print("-------------------------------------------")


if __name__ == "__main__":
    main()
    ####### 临时用
    # text = "今天是个好日子"
    # output_filepath = os.path.join("", f"{text}.wav")
    # generate_audio_for_text(text, output_filepath)