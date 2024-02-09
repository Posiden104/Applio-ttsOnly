import os, sys
import gradio as gr
import regex as re
import json
import shutil
import datetime
import random

from core import (
    run_tts_script,
)

from assets.i18n.i18n import I18nAuto

i18n = I18nAuto()

now_dir = os.getcwd()
sys.path.append(now_dir)

model_root = os.path.join(now_dir, "logs")
audio_root = os.path.join(now_dir, "assets", "audios")

model_root_relative = os.path.relpath(model_root, now_dir)
audio_root_relative = os.path.relpath(audio_root, now_dir)

max_parts = 10
parts = []
use_json = False

sup_audioext = {
    "wav",
    "mp3",
    "flac",
    "ogg",
    "opus",
    "m4a",
    "mp4",
    "aac",
    "alac",
    "wma",
    "aiff",
    "webm",
    "ac3",
}

names = [
    os.path.join(root, file)
    for root, _, files in os.walk(model_root_relative, topdown=False)
    for file in files
    if (
        file.endswith((".pth", ".onnx"))
        and not (file.startswith("G_") or file.startswith("D_"))
    )
]

indexes_list = [
    os.path.join(root, name)
    for root, _, files in os.walk(model_root_relative, topdown=False)
    for name in files
    if name.endswith(".index") and "trained" not in name
]

audio_paths = [
    os.path.join(root, name)
    for root, _, files in os.walk(audio_root_relative, topdown=False)
    for name in files
    if name.endswith(tuple(sup_audioext))
    and root == audio_root_relative
    and "_output" not in name
]


def change_choices():
    names = [
        os.path.join(root, file)
        for root, _, files in os.walk(model_root_relative, topdown=False)
        for file in files
        if (
            file.endswith((".pth", ".onnx"))
            and not (file.startswith("G_") or file.startswith("D_"))
        )
    ]

    indexes_list = [
        os.path.join(root, name)
        for root, _, files in os.walk(model_root_relative, topdown=False)
        for name in files
        if name.endswith(".index") and "trained" not in name
    ]

    audio_paths = [
        os.path.join(root, name)
        for root, _, files in os.walk(audio_root_relative, topdown=False)
        for name in files
        if name.endswith(tuple(sup_audioext))
        and root == audio_root_relative
        and "_output" not in name
    ]
    return (
        {"choices": sorted(names), "__type__": "update"},
        {"choices": sorted(indexes_list), "__type__": "update"},
        {"choices": sorted(audio_paths), "__type__": "update"},
    )


def get_indexes():
    indexes_list = [
        os.path.join(dirpath, filename)
        for dirpath, _, filenames in os.walk(model_root_relative)
        for filename in filenames
        if filename.endswith(".index") and "trained" not in filename
    ]

    return indexes_list if indexes_list else ""


def match_index(model_file: str) -> tuple:
    model_files_trip = re.sub(r"\.pth|\.onnx$", "", model_file)
    model_file_name = os.path.split(model_files_trip)[
        -1
    ]  # Extract only the name, not the directory

    # Check if the sid0strip has the specific ending format _eXXX_sXXX
    if re.match(r".+_e\d+_s\d+$", model_file_name):
        base_model_name = model_file_name.rsplit("_", 2)[0]
    else:
        base_model_name = model_file_name

    sid_directory = os.path.join(model_root_relative, base_model_name)
    directories_to_search = [sid_directory] if os.path.exists(sid_directory) else []
    directories_to_search.append(model_root_relative)

    matching_index_files = []

    for directory in directories_to_search:
        for filename in os.listdir(directory):
            if filename.endswith(".index") and "trained" not in filename:
                # Condition to match the name
                name_match = any(
                    name.lower() in filename.lower()
                    for name in [model_file_name, base_model_name]
                )

                # If in the specific directory, it's automatically a match
                folder_match = directory == sid_directory

                if name_match or folder_match:
                    index_path = os.path.join(directory, filename)
                    if index_path in indexes_list:
                        matching_index_files.append(
                            (
                                index_path,
                                os.path.getsize(index_path),
                                " " not in filename,
                            )
                        )

    if matching_index_files:
        # Sort by favoring files without spaces and by size (largest size first)
        matching_index_files.sort(key=lambda x: (-x[2], -x[1]))
        best_match_index_path = matching_index_files[0][0]
        return best_match_index_path

    return ""


def save_to_wav(record_button):
    if record_button is None:
        pass
    else:
        path_to_file = record_button
        new_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".wav"
        target_path = os.path.join(audio_root_relative, os.path.basename(new_name))

        shutil.move(path_to_file, target_path)
        return target_path


def save_to_wav2(upload_audio):
    file_path = upload_audio
    target_path = os.path.join(audio_root_relative, os.path.basename(file_path))

    if os.path.exists(target_path):
        os.remove(target_path)

    shutil.copy(file_path, target_path)
    return target_path


def delete_outputs():
    for root, _, files in os.walk(audio_root_relative, topdown=False):
        for name in files:
            if name.endswith(tuple(sup_audioext)) and name.__contains__("_output"):
                os.remove(os.path.join(root, name))
    gr.Info(f"Outputs cleared!")


def process_input(file_path):
    with open(file_path, "r") as file:
        file_contents = file.read()
    gr.Info(f"The text from the txt file has been loaded!")
    return file_contents, None

def process_json_input(json_text):
    global use_json, parts
    json_data = json.loads(json_text)
    parts = json_data["parts"]
    use_json = True
    return json_data["title"], len(parts)

def prepare_tts_script(
    tts_title,
    tts_part,
    tts_part_total,
    tts_text,
    tts_voice,
    f0up_key,
    filter_radius,
    index_rate,
    hop_length,
    f0method,
    output_tts_path,
    # output_rvc_path,
    # pth_file,
    # index_path,
):
    global use_json, parts
    print(use_json)
    print(parts)
    if not use_json:
        tts_input = f'{tts_title}. Part {tts_part} of {tts_part_total}. {tts_text}' if tts_part_total > 0 else f'{tts_title}. {tts_text}'
        return run_tts_script(
            tts_input,
            tts_voice,
            f0up_key,
            filter_radius,
            index_rate,
            hop_length,
            f0method,
            os.path.join(output_tts_path, f'{tts_title}_pt{tts_part}.wav' if tts_part_total > 0 else f'{tts_title}.wav'),
            # output_rvc_path,
            # pth_file,
            # index_path,
        )
    else:
        for i, tts_body in enumerate(parts):
            tts_input =f'{tts_title}. {tts_body}'
            result = run_tts_script(
                tts_input,
                tts_voice,
                f0up_key,
                filter_radius,
                index_rate,
                hop_length,
                f0method,
                os.path.join(output_tts_path, f'{tts_title}_pt{i + 1}.wav'),
                # output_rvc_path,
                # pth_file,
                # index_path,
            )
        return result

def tts_tab():
    default_weight = random.choice(names) if names else ""
    # RVC Voice Stuff
    # with gr.Row():
    #     with gr.Row():
    #         model_file = gr.Dropdown(
    #             label=i18n("Voice Model"),
    #             choices=sorted(names, key=lambda path: os.path.getsize(path)),
    #             interactive=True,
    #             value=default_weight,
    #             allow_custom_value=True,
    #         )
    #         best_default_index_path = match_index(model_file.value)
    #         index_file = gr.Dropdown(
    #             label=i18n("Index File"),
    #             choices=get_indexes(),
    #             value=best_default_index_path,
    #             interactive=True,
    #             allow_custom_value=True,
    #         )
    #     with gr.Column():
    #         refresh_button = gr.Button(i18n("Refresh"))
    #         unload_button = gr.Button(i18n("Unload Voice"))

    #         unload_button.click(
    #             fn=lambda: ({"value": "", "__type__": "update"}),
    #             inputs=[],
    #             outputs=[model_file],
    #         )

    #         model_file.select(
    #             fn=match_index,
    #             inputs=[model_file],
    #             outputs=[index_file],
    #         )

    json_path = os.path.join("rvc", "lib", "tools", "tts_voices.json")
    with open(json_path, "r") as file:
        tts_voices_data = json.load(file)

    short_names = [voice.get("ShortName", "") for voice in tts_voices_data]
    
    short_names = filter(lambda v: v.startswith("en-US") or v.startswith("en-GB"), short_names)

    tts_voice = gr.Dropdown(
        label=i18n("TTS Voices"),
        choices=short_names,
        interactive=True,
        value="en-US-AndrewNeural",
    )

    output_tts_path = gr.Textbox(
        label=i18n("Base Output Path for TTS Audio"),
        placeholder=i18n("Enter output path"),
        value=os.path.join("D:\_TikTok\Sounds"),
        interactive=True,
    )

    with gr.Row():
        with gr.Column():
            with gr.Row():
                tts_title = gr.Textbox(
                    label=i18n("Title"),
                    placeholder=i18n("Enter Title"),
                    lines=3,
                )
                with gr.Accordion(i18n("Part Details"), open=False):
                    with gr.Column():
                        tts_part = gr.Number(
                            label=i18n("Part"), 
                            value=0,
                            interactive=True,
                        )
                        tts_part_total = gr.Number(
                            label=i18n("Part total"),
                            value=0,
                            interactive=True,
                        )

                    tts_text = gr.Textbox(
                        label=i18n("Text to Synthesize"),
                        placeholder=i18n("Enter text"),
                        lines=3,
                        interactive=True,
                    )

            json_text = gr.Textbox(
                label=i18n("Json input"),
                placeholder=i18n("Enter text"),
                lines=3,
                interactive=True,
            )

    with gr.Accordion(i18n("File Upload"), open=False):
        txt_file = gr.File(
            label=i18n("Or you can upload a .txt file"),
            type="filepath",
        )

    with gr.Accordion(i18n("Advanced Settings"), open=False):
        with gr.Column():
            # output_rvc_path = gr.Textbox(
            #     label=i18n("Output Path for RVC Audio"),
            #     placeholder=i18n("Enter output path"),
            #     value=os.path.join(now_dir, "assets", "audios", "tts_rvc_output.wav"),
            #     interactive=True,
            # )

            pitch = gr.Slider(
                minimum=-24,
                maximum=24,
                step=1,
                label=i18n("Pitch"),
                value=0,
                interactive=True,
            )
            filter_radius = gr.Slider(
                minimum=0,
                maximum=7,
                label=i18n(
                    "If >=3: apply median filtering to the harvested pitch results. The value represents the filter radius and can reduce breathiness"
                ),
                value=3,
                step=1,
                interactive=True,
            )
            index_rate = gr.Slider(
                minimum=0,
                maximum=1,
                label=i18n("Search Feature Ratio"),
                value=0.75,
                interactive=True,
            )
            hop_length = gr.Slider(
                minimum=1,
                maximum=512,
                step=1,
                label=i18n("Hop Length"),
                value=128,
                interactive=True,
            )
        with gr.Column():
            f0method = gr.Radio(
                label=i18n("Pitch extraction algorithm"),
                choices=[
                    "pm",
                    "harvest",
                    "dio",
                    "crepe",
                    "crepe-tiny",
                    "rmvpe",
                ],
                value="rmvpe",
                interactive=True,
            )

    with gr.Row():
        load_json_button1 = gr.Button(i18n("Load Json"))
        convert_button1 = gr.Button(i18n("Convert"))
        

    load_json_button1.click(
        fn=process_json_input,
        inputs=[json_text],
        outputs=[tts_title, tts_part_total]
    )

    with gr.Row():  # Defines output info + output audio download after conversion
        vc_output1 = gr.Textbox(label=i18n("Output Information"))
        vc_output2 = gr.Audio(label=i18n("Export Audio"))

    # refresh_button.click(
    #     fn=change_choices,
    #     inputs=[],
    #     outputs=[model_file, index_file],
    # )
    txt_file.upload(
        fn=process_input,
        inputs=[txt_file],
        outputs=[tts_text, txt_file],
    )
        
    convert_button1.click(
        fn=prepare_tts_script,
        inputs=[
            tts_title,
            tts_part,
            tts_part_total,
            tts_text,
            tts_voice,
            pitch,
            filter_radius,
            index_rate,
            hop_length,
            f0method,
            output_tts_path,
            # output_rvc_path,
            # model_file,
            # index_file,
        ],
        outputs=[vc_output1, vc_output2],
    )
