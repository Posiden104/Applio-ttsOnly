import multiprocessing
import os
import re
from os.path import exists  # Needs to be imported specifically
from typing import Final
from typing import Tuple, Any, Dict

import ffmpeg
from PIL import Image
from rich.console import Console
from rich.progress import track

from utils.console import print_step, print_substep
# from utils.thumbnail import create_thumbnail
# from utils.videos import save_data
from utils.cleanup import cleanup

import tempfile
import threading
import time

console = Console()


class ProgressFfmpeg(threading.Thread):
    def __init__(self, vid_duration_seconds, progress_update_callback):
        threading.Thread.__init__(self, name="ProgressFfmpeg")
        self.stop_event = threading.Event()
        self.output_file = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        self.vid_duration_seconds = vid_duration_seconds
        self.progress_update_callback = progress_update_callback

    def run(self):
        while not self.stop_event.is_set():
            latest_progress = self.get_latest_ms_progress()
            if latest_progress is not None:
                completed_percent = latest_progress / self.vid_duration_seconds
                self.progress_update_callback(completed_percent)
            time.sleep(1)

    def get_latest_ms_progress(self):
        lines = self.output_file.readlines()

        if lines:
            for line in lines:
                if "out_time_ms" in line:
                    out_time_ms_str = line.split("=")[1].strip()
                    if out_time_ms_str.isnumeric():
                        return float(out_time_ms_str) / 1000000.0
                    else:
                        # Handle the case when "N/A" is encountered
                        return None
        return None

    def stop(self):
        self.stop_event.set()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args, **kwargs):
        self.stop()


def prepare_background(title: str, W: int, H: int) -> str:
    output_path = f"assets/temp/{title}/background_noaudio.mp4"
    output = (
        ffmpeg.input(f"assets/temp/{title}/background.mp4")
        .filter("crop", f"ih*({W}/{H})", "ih")
        .output(
            output_path,
            an=None,
            **{
                "c:v": "h264_nvenc",
                "b:v": "20M",
                "b:a": "192k",
                "threads": multiprocessing.cpu_count(),
            },
        )
        .overwrite_output()
    )
    try:
        output.run(quiet=True)
    except ffmpeg.Error as e:
        print(e.stderr.decode("utf8"))
        exit(1)
    return output_path


def merge_background_audio(audio: ffmpeg, reddit_id: str):
    """Gather an audio and merge with assets/backgrounds/background.mp3
    Args:
        audio (ffmpeg): The TTS final audio but without background.
        reddit_id (str): The ID of subreddit
    """
    # background_audio_volume = settings.config["settings"]["background"]["background_audio_volume"]
    # if background_audio_volume == 0:
    return audio  # Return the original audio
    # else:
    #     # sets volume to config
    #     bg_audio = ffmpeg.input(f"assets/temp/{reddit_id}/background.mp3").filter(
    #         "volume",
    #         background_audio_volume,
    #     )
    #     # Merges audio and background_audio
    #     merged_audio = ffmpeg.filter([audio, bg_audio], "amix", duration="longest")
    #     return merged_audio  # Return merged audio


def make_final_video(
    length: int,
    title: str,
    tts_path: str,
    video_output_path: str
):
    """Gathers audio clips, gathers all screenshots, stitches them together and saves the final video to assets/temp
    Args:
        length (int): Length of the video
        title (str): The title of the video
        background_config (Tuple[str, str, str, Any]): The background config to use.
        tts_path (str): Path to TTS voice file
        video_output_path (str): Path to output final video
    """
    # settings values
    H: Final[int] = 1920
    W: Final[int] = 1080

    print_step("Creating the final video 🎥")

    background_clip = ffmpeg.input(prepare_background(title, W=W, H=H))

    # # Gather all audio clips
    # audio_clips = [ffmpeg.input(tts_path)]

    # audio_concat = ffmpeg.concat(*audio_clips, a=1, v=0)
    # ffmpeg.output(
    #     audio_concat, f"assets/temp/{title}/audio.mp3", **{"b:a": "192k"}
    # ).overwrite_output().run(quiet=True)

    console.log(f"[bold green] Video Will Be: {length} Seconds Long")

    # audio = ffmpeg.input(f"assets/temp/{title}/audio.mp3")
    final_audio = ffmpeg.input(tts_path)

    # screenshot_width = int((W * 45) // 100)
    # image_clips = list()

    # image_clips.insert(
    #     0,
    #     ffmpeg.input(f"assets/temp/{title}/png/title.png")["v"].filter(
    #         "scale", screenshot_width, -1
    #     ),
    # )

    # current_time = 0
    # audio_clips_durations = [
    #     float(
    #         ffmpeg.probe(f"assets/temp/{title}/mp3/postaudio-{i}.mp3")["format"]["duration"]
    #     )
    #     for i in range(number_of_clips)
    # ]
    # audio_clips_durations.insert(
    #     0,
    #     float(ffmpeg.probe(f"assets/temp/{title}/mp3/title.mp3")["format"]["duration"]),
    # )

    # image_clips.insert(
    #     1,
    #     ffmpeg.input(f"assets/temp/{title}/png/story_content.png").filter(
    #         "scale", screenshot_width, -1
    #     ),
    # )
    # background_clip = background_clip.overlay(
    #     image_clips[0],
    #     enable=f"between(t,{current_time},{current_time + audio_clips_durations[0]})",
    #     x="(main_w-overlay_w)/2",
    #     y="(main_h-overlay_h)/2",
    # )
    # current_time += audio_clips_durations[0]

    filename = title

    if not exists(video_output_path):
        print_substep(f"The output folder '{video_output_path}' could not be found so it was automatically created.")
        os.makedirs(video_output_path)

    # text = f"Background by {background_config['video'][2]}"
    # background_clip = ffmpeg.drawtext(
    #     background_clip,
    #     text=text,
    #     x=f"(w-text_w)",
    #     y=f"(h-text_h)",
    #     fontsize=5,
    #     fontcolor="White",
    #     fontfile=os.path.join("fonts", "Roboto-Regular.ttf"),
    # )
        
    background_clip = background_clip.filter("scale", W, H)
    print_step("Rendering the video 🎥")
    from tqdm import tqdm

    pbar = tqdm(total=100, desc="Progress: ", bar_format="{l_bar}{bar}", unit=" %")

    def on_update_example(progress) -> None:
        status = round(progress * 100, 2)
        old_percentage = pbar.n
        pbar.update(status - old_percentage)

    with ProgressFfmpeg(length, on_update_example) as progress:
        path = video_output_path + f"/{filename}"
        path = (
            path[:251] + ".mp4"
        )  # Prevent a error by limiting the path length, do not change this.
        try:
            ffmpeg.output(
                background_clip,
                final_audio,
                path,
                f="mp4",
                **{
                    "c:v": "h264_nvenc",
                    "b:v": "20M",
                    "b:a": "192k",
                    "threads": multiprocessing.cpu_count(),
                },
            ).overwrite_output().global_args("-progress", progress.output_file.name).run(
                quiet=True,
                overwrite_output=True,
                capture_stdout=False,
                capture_stderr=False,
            )
        except ffmpeg.Error as e:
            print(e.stderr.decode("utf8"))
            exit(1)
    old_percentage = pbar.n
    pbar.update(100 - old_percentage)
    
    pbar.close()
    # save_data(subreddit, filename + ".mp4", title, idx, background_config["video"][2])
    cleanups = cleanup(title)
    print_substep(f"Removed {cleanups} temporary files 🗑")
    print_step("Done! 🎉 The video is in the results folder 📁")
