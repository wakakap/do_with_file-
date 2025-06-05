# 把srt_file_path中的日语字幕转换为音频文件，使用VOICEVOX引擎，保存到 OUTPUT_DIR 目录。以srt中为准，清除掉OUTPUT_DIR中不再使用的音频文件。
import os
import requests
import time
import pysrt # We'll need this library for SRT parsing
import hashlib # For creating unique filenames from text

# --- Configuration Parameters ---
# Default address for the local VOICEVOX service. Ensure the software is running.
VOICEVOX_URL = "http://localhost:50021"
# Default speaker ID. You can change this to match your desired VOICEVOX character.
# Common IDs: 0 (四国めたん), 1 (ずんだもん) etc. Check VOICEVOX Engine /speakers or /docs for all IDs.
DEFAULT_SPEAKER_ID = 1 
# Output directory for generated audio files.
OUTPUT_DIR = "E:\\抽吧唧\\1\\voice"
srt_file_path = "E:\\抽吧唧\\1\\jp.srt" # Make sure your SRT file is here or specify the correct path

# --- Core VOICEVOX Interaction Functions ---

def generate_audio(text, output_path, speaker_id=DEFAULT_SPEAKER_ID):
    """
    Generates audio from text using the VOICEVOX API and saves it to output_path.
    Includes custom audio parameters for better control.
    """
    try:
        # Step 1: Get audio_query from text
        query_url = f"{VOICEVOX_URL}/audio_query"
        params = {
            "text": text,
            "speaker": speaker_id
        }
        
        response = requests.post(query_url, params=params)
        response.raise_for_status() # Raises an HTTPError for bad responses (4xx or 5xx)
        audio_query = response.json()
        
        # Modify audio parameters for fine-tuning
        audio_query["prePhonemeLength"] = 0.0   # Silence before speech
        audio_query["postPhonemeLength"] = 0.0  # Silence after speech
        audio_query["speedScale"] = 1.5        # Speech speed (default 1.0)
        audio_query["pitchScale"] = 0.0         # Pitch (default 0.0)
        audio_query["intonationScale"] = 1.1    # Intonation strength (default 1.0)
        audio_query["volumeScale"] = 1.2        # Volume (default 1.0)
        
        # Step 2: Synthesize audio
        synthesis_url = f"{VOICEVOX_URL}/synthesis"
        headers = {"Content-Type": "application/json"}
        params = {"speaker": speaker_id}
        
        response = requests.post(
            synthesis_url,
            json=audio_query,
            headers=headers,
            params=params
        )
        response.raise_for_status()
        
        # Save the audio file
        with open(output_path, "wb") as f:
            f.write(response.content)
        return True # Indicate success
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to VOICEVOX Engine at {VOICEVOX_URL}. Is it running?")
        return False
    except requests.exceptions.RequestException as e:
        print(f"VOICEVOX API error for text '{text}': {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during audio generation for '{text}': {e}")
        return False

def clean_unused_audio(output_dir, valid_files_bases):
    """
    Removes WAV files from output_dir that are no longer referenced in valid_files_bases.
    """
    if not os.path.exists(output_dir):
        print(f"Output directory '{output_dir}' does not exist, skipping cleanup.")
        return

    # Add .wav extension to valid file bases for comparison
    valid_full_filenames = [f"{base}.wav" for base in valid_files_bases]
    
    # Get all existing WAV files in the directory
    existing_files = [f for f in os.listdir(output_dir) if f.endswith('.wav')]
    
    # Find files to delete
    files_to_delete = list(set(existing_files) - set(valid_full_filenames))
    
    if files_to_delete:
        print(f"\nCleaning up {len(files_to_delete)} unused audio files in '{output_dir}'...")
        for file in files_to_delete:
            file_path = os.path.join(output_dir, file)
            try:
                os.remove(file_path)
                print(f"   Deleted redundant file: {file}")
            except Exception as e:
                print(f"   Error deleting file {file_path}: {e}")
    else:
        print(f"No redundant audio files found in '{output_dir}'.")

# --- Main Logic for SRT Processing ---

def main():
    # Create the output folder if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # List to store the base names of all valid audio files to be generated/kept
    valid_audio_bases = []

    try:
        # Open and parse the SRT file
        # Using encoding='utf-8' is crucial for Japanese text
        subs = pysrt.open(srt_file_path, encoding='utf-8')
        print(f"Successfully opened SRT file: {srt_file_path}")
        
        # Process each subtitle entry
        for sub in subs:
            text_content = sub.text.strip()
            if not text_content:
                print(f"Skipping empty subtitle at index {sub.index}.")
                continue

            # Create a unique filename based on the text content (first 32 chars + hash)
            # This helps avoid issues with long/invalid characters in filenames
            # and ensures uniqueness for identical phrases.
            clean_text_for_filename = "".join(c for c in text_content if c.isalnum() or c in (' ', '_')).strip()
            if not clean_text_for_filename: # If text becomes empty after cleaning
                clean_text_for_filename = f"subtitle_{sub.index}"
            
            # Use SHA256 hash for robustness against long or non-unique short texts
            text_hash = hashlib.sha256(text_content.encode('utf-8')).hexdigest()[:8] # Take first 8 chars of hash
            
            # Combine a truncated clean text with the hash for readability and uniqueness
            # MODIFICATION START: Add SRT index to the filename
            # Format the index with leading zeros (e.g., 001, 010)
            formatted_index = f"{sub.index:04d}" 
            filename_base = f"{formatted_index}_{clean_text_for_filename[:64]}_{text_hash}" # Truncate to reasonable length
            # MODIFICATION END
            
            output_audio_path = os.path.join(OUTPUT_DIR, f"{filename_base}.wav")
            valid_audio_bases.append(filename_base) # Add to list of valid files for cleanup
            
            # Check if audio file already exists
            if os.path.exists(output_audio_path):
                print(f"Audio for '{text_content[:30]}...' already exists, skipping generation. ({os.path.basename(output_audio_path)})")
                continue
            
            # Generate audio
            print(f"Generating audio for: '{text_content[:50]}...' (Index: {sub.index})") # Print truncated text
            success = generate_audio(text_content, output_audio_path, speaker_id=DEFAULT_SPEAKER_ID)
            
            if success:
                print(f"   Generated: {os.path.basename(output_audio_path)}")
                # Add a brief delay to avoid overwhelming the API
                time.sleep(0.1)
            else:
                print(f"   Failed to generate audio for: '{text_content[:50]}...'")

    except FileNotFoundError:
        print(f"Error: SRT file not found at '{srt_file_path}'. Please check the path.")
    except pysrt.Error as e:
        print(f"Error parsing SRT file '{srt_file_path}': {e}. Please ensure it's a valid SRT format.")
    except Exception as e:
        print(f"An unexpected error occurred during SRT processing: {e}")
    
    # Clean up any unused audio files
    clean_unused_audio(OUTPUT_DIR, valid_audio_bases)

if __name__ == "__main__":
    print("Starting VOICEVOX SRT to Audio conversion script...")
    main()
    print("\nScript finished.")