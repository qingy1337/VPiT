import cv2
import numpy as np
from time import sleep
import time
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import argparse
import threading
import pygame
from moviepy.editor import VideoFileClip

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
    global fps
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    while cap.isOpened():
        if early_break and len(frames_list) == early_break:
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

        frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames_list.append(frame)
    cap.release()
    return frames_list

def print_rgb(text, r, g, b):
    return f"\033[1m\033[38;2;{r};{g};{b}m{text}\033[0m"

def play_audio(audio_path):
    pygame.mixer.init()
    pygame.mixer.music.load(audio_path)
    pygame.mixer.music.play()

def extract_audio(video_path, output_audio_path):
    video = VideoFileClip(video_path)
    last = video.duration
    video = video.subclip(0, last)

    audio = video.audio
    audio.to_audiofile(output_audio_path)

def neq(a1, a2):
    return sum(abs(a1[x] - a2[x]) for x in range(3)) > 40

def main():
    parser = argparse.ArgumentParser(description="Play a video in the terminal.")
    parser.add_argument("video_path", type=str, help="Path to the video file.")
    parser.add_argument("--custom", type=str, help="Character used to display pixels.")

    args = parser.parse_args()

    pixel_value = lambda x: "█"
    if args.custom:
        pixel_value = lambda x: args.custom
        if args.custom == "binary":
            pixel_value = lambda x: str(x % 2)
        elif args.custom == "alphabet":
            pixel_value = lambda x: ascii_lowercase[x % 26]

    term_width, term_height = get_terminal_size()

    frame_thread = threading.Thread(target=extract_frames, args=(args.video_path, term_width, term_height))
    frame_thread.start()

    audio_path = "temp_audio.mp3"
    extract_audio(args.video_path, audio_path)

    pygame.mixer.init()
    pygame.mixer.music.load(audio_path)
    pygame.mixer.music.play()

    t1 = time.perf_counter()
    while True:
        time2 = time.perf_counter() - t1
        if time2 > len(frames_list) / fps:
            break

        frame_num = int(time2 * fps)

        if frame_num < 10:
            pygame.mixer.music.set_pos(time2)

        try:
            final_str = ""
            for ir, row in enumerate(frames_list[frame_num]):
                row_str = "".join([print_rgb(pixel_value(i), pixel[0], pixel[1],pixel[2]) for i, pixel in enumerate(row)])
                final_str += row_str + "\n"
            sleep(1/fps)
            move_cursor_to_top()
            print(final_str)
        except KeyboardInterrupt:
            break

    pygame.mixer.music.stop()
    os.remove('temp_audio.mp3')

if __name__ == "__main__":
    main()
