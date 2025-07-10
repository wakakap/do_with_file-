import sys
import re

def time_to_seconds(t):
    """Convert ASS timestamp to seconds."""
    h, m, s = t.split(':')
    s, cs = s.split('.')
    return int(h)*3600 + int(m)*60 + int(s) + int(cs)/100

def seconds_to_time(secs):
    """Convert seconds to ASS timestamp format."""
    if secs < 0:
        secs = 0
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    s = int(secs % 60)
    cs = int(round((secs - int(secs)) * 100))
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def process_line(line, max_duration, shift=4.0):
    if not line.startswith('Dialogue:'):
        return line

    parts = line.split(',', 3)
    if len(parts) < 4:
        return line  # something's wrong

    # Parse start and end times
    start_str = parts[1]
    end_str = parts[2]
    try:
        start = time_to_seconds(start_str)
        end = time_to_seconds(end_str)
    except ValueError:
        return line

    # Shift times
    new_start = max(0, start)
    new_end = min(max_duration, end + shift)

    # Rebuild line
    new_line = f"{parts[0]},{seconds_to_time(new_start)},{seconds_to_time(new_end)},{parts[3]}"
    return new_line

def main():
    input_file = "niconico/takop/20250709_so45124910_comments_CH.ass"
    output_file = "niconico/takop/20250709_so45124910_comments_CH_extend.ass"
    try:
        max_duration = 111295.0
    except ValueError:
        print("Invalid max_video_seconds value")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    with open(output_file, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(process_line(line, max_duration))

if __name__ == "__main__":
    main()
