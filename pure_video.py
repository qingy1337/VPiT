import cv2
import numpy as np
from time import sleep
import time
import os
import argparse
import threading
# Removed: os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
# Removed: import pygame
# Removed: from moviepy.editor import VideoFileClip

from string import ascii_lowercase

CHARACTER_ASPECT_RATIO = 0.5

def move_cursor_to_top():
    print("\033[H", end="")

def get_terminal_size():
    size = os.get_terminal_size()
    return size.columns - 5, size.lines - 1

fps = -1
frames_list = []
def extract_frames(video_path, max_width, max_height, early_break=None):
    global fps # Ensure fps is globally available
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        fps = 0 # Set a default to prevent division by zero if video fails
        return [] # Return empty list

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0: # Handle cases where fps might not be read correctly
        print("Warning: Could not determine video FPS. Defaulting to 24 FPS.")
        fps = 24


    extracted_frames = [] # Use a local list to append and then assign to global
    while cap.isOpened():
        if early_break and len(extracted_frames) == early_break:
            break
        ret, frame = cap.read()
        if not ret:
            break

        height, width = frame.shape[:2]

        scale_width = max_width / width
        scale_height = (max_height - 1) / (height * CHARACTER_ASPECT_RATIO)
        scale = min(scale_width, scale_height)

        new_width = int(width * scale)
        new_height = int(height * scale * CHARACTER_ASPECT_RATIO)

        # Ensure new_width and new_height are not zero
        if new_width <= 0 or new_height <= 0:
            # print(f"Warning: Calculated invalid dimensions ({new_width}x{new_height}). Skipping frame.")
            continue


        frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        extracted_frames.append(frame)

    cap.release()
    global frames_list # Assign to global frames_list after extraction
    frames_list = extracted_frames
    return extracted_frames # Though frames_list is global, returning can be good practice

def print_rgb(text, r, g, b):
    return f"\033[1m\033[38;2;{r};{g};{b}m{text}\033[0m"

# Removed: play_audio function
# Removed: extract_audio function

def neq(a1, a2): # This function is defined but not used in the provided script.
                 # Keeping it in case it was intended for future use or part of a larger system.
    return sum(abs(a1[x] - a2[x]) for x in range(3)) > 40

def main():
    parser = argparse.ArgumentParser(description="Play a video in the terminal (no audio).")
    parser.add_argument("video_path", type=str, help="Path to the video file.")
    parser.add_argument("--custom", type=str, help="Character used to display pixels. Options: 'binary', 'alphabet', or any single character.")

    args = parser.parse_args()

    pixel_value_char = "█" # Default
    if args.custom:
        if args.custom == "binary":
            pixel_value = lambda i, pixel: str(i % 2) # Use index for binary pattern
        elif args.custom == "alphabet":
            pixel_value = lambda i, pixel: ascii_lowercase[i % 26] # Use index for alphabet pattern
        else:
            pixel_value_char = args.custom
            pixel_value = lambda i, pixel: pixel_value_char # Use the custom character
    else:
        pixel_value = lambda i, pixel: pixel_value_char # Default '█'

    term_width, term_height = get_terminal_size()

    print("Extracting frames...")
    frame_thread = threading.Thread(target=extract_frames, args=(args.video_path, term_width, term_height))
    frame_thread.start()
    frame_thread.join() # Wait for frame extraction to complete

    if not frames_list:
        print("No frames were extracted. Exiting.")
        return
    if fps <= 0:
        print("Invalid FPS. Exiting.")
        return

    print(f"Frames extracted. FPS: {fps:.2f}. Playing video...")
    sleep(1) # Give a moment for the user to see the message

    t1 = time.perf_counter()
    total_duration = len(frames_list) / fps
    frame_index = 0

    try:
        while True:
            current_time = time.perf_counter() - t1

            if current_time >= total_duration:
                break # Video finished

            # Determine which frame to display based on elapsed time
            expected_frame_num = int(current_time * fps)

            # Skip frames if rendering is too slow, or wait if rendering is too fast
            if expected_frame_num > frame_index:
                frame_index = expected_frame_num
            elif expected_frame_num < frame_index and frame_index < len(frames_list) -1 :
                # This case should ideally not happen often if sleep is accurate
                # but if it does, we might be rendering too fast, so we wait a bit.
                # The sleep(delay_per_frame) below handles this more directly.
                pass


            if frame_index >= len(frames_list):
                frame_index = len(frames_list) - 1 # Ensure we don't go out of bounds

            if frame_index < 0: # Should not happen
                frame_index = 0

            # --- Frame Rendering ---
            final_str = ""
            current_frame_data = frames_list[frame_index]
            for ir, row in enumerate(current_frame_data):
                # Pass both index and pixel to pixel_value lambda
                row_str = "".join([print_rgb(pixel_value(i, pixel), pixel[0], pixel[1], pixel[2]) for i, pixel in enumerate(row)])
                final_str += row_str + "\n"

            move_cursor_to_top()
            print(final_str, end="") # Use end="" to prevent extra newline from print

            # --- Timing & Sleep ---
            # Calculate time spent rendering this frame
            render_end_time = time.perf_counter()
            time_spent_rendering = render_end_time - (t1 + current_time) # Approx. time for this frame's logic + print

            # Calculate how long we should sleep until the next frame
            # target_next_frame_time = (frame_index + 1) / fps
            # time_until_next_frame = target_next_frame_time - current_time
            delay_per_frame = 1.0 / fps
            sleep_duration = delay_per_frame - time_spent_rendering
            
            if sleep_duration > 0:
                sleep(sleep_duration)
            
            # Prepare for next iteration
            frame_index += 1
            if frame_index >= len(frames_list):
                break


    except KeyboardInterrupt:
        print("\nPlayback interrupted.")
    finally:
        # Clean up cursor visibility and reset colors if needed (though print_rgb resets color per char)
        print("\033[?25h") # Show cursor
        print("\033[0m")   # Reset colors
        print("Video finished or interrupted.")

if __name__ == "__main__":
    main()
