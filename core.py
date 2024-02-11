import os
import sys
import argparse
import subprocess

now_dir = os.getcwd()
sys.path.append(now_dir)

from rvc.configs.config import Config
from rvc.lib.tools.validators import (
    validate_sampling_rate,
    validate_f0up_key,
    validate_f0method,
    validate_true_false,
    validate_tts_voices,
)

config = Config()
current_script_directory = os.path.dirname(os.path.realpath(__file__))
logs_path = os.path.join(current_script_directory, "logs")
# subprocess.run(
#     ["python", os.path.join("rvc", "lib", "tools", "prerequisites_download.py")]
# )

# TTS
def run_tts_script(
    tts_text,
    tts_voice,
    f0up_key,
    filter_radius,
    index_rate,
    hop_length,
    f0method,
    output_tts_path,
):
    tts_script_path = os.path.join("rvc", "lib", "tools", "tts.py")

    if os.path.exists(output_tts_path):
        os.remove(output_tts_path)

    command_tts = [
        "python",
        tts_script_path,
        tts_text,
        tts_voice,
        output_tts_path,
    ]

    subprocess.run(command_tts)
    return f"Text {tts_text} synthesized successfully.", output_tts_path


# Download
def run_download_script(model_link):
    download_script_path = os.path.join("rvc", "lib", "tools", "model_download.py")
    command = [
        "python",
        download_script_path,
        model_link,
    ]
    subprocess.run(command)
    return f"Model downloaded successfully."


# Parse arguments
def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Run the main.py script with specific parameters."
    )
    subparsers = parser.add_subparsers(
        title="subcommands", dest="mode", help="Choose a mode"
    )

    # Parser for 'tts' mode
    tts_parser = subparsers.add_parser("tts", help="Run TTS")
    tts_parser.add_argument(
        "tts_text",
        type=str,
        help="Text to be synthesized (enclose in double quotes)",
    )
    tts_parser.add_argument(
        "tts_voice",
        type=validate_tts_voices,
        help="Voice to be used (enclose in double quotes)",
    )
    tts_parser.add_argument(
        "f0up_key",
        type=validate_f0up_key,
        help="Value for f0up_key (-24 to +24)",
    )
    tts_parser.add_argument(
        "filter_radius",
        type=str,
        help="Value for filter_radius (0 to 10)",
    )
    tts_parser.add_argument(
        "index_rate",
        type=str,
        help="Value for index_rate (0.0 to 1)",
    )
    tts_parser.add_argument(
        "hop_length",
        type=str,
        help="Value for hop_length (1 to 512)",
    )
    tts_parser.add_argument(
        "f0method",
        type=validate_f0method,
        help="Value for f0method (pm, dio, crepe, crepe-tiny, harvest, rmvpe)",
    )
    tts_parser.add_argument(
        "output_tts_path", type=str, help="Output tts path (enclose in double quotes)"
    )
    tts_parser.add_argument(
        "output_rvc_path", type=str, help="Output rvc path (enclose in double quotes)"
    )
    tts_parser.add_argument(
        "pth_file", type=str, help="Path to the .pth file (enclose in double quotes)"
    )
    tts_parser.add_argument(
        "index_path",
        type=str,
        help="Path to the .index file (enclose in double quotes)",
    )

    return parser.parse_args()


def main():
    if len(sys.argv) == 1:
        print("Please run the script with '-h' for more information.")
        sys.exit(1)

    args = parse_arguments()

    try:
        if args.mode == "tts":
            run_tts_script(
                args.tts_text,
                args.tts_voice,
                args.f0up_key,
                args.filter_radius,
                args.index_rate,
                args.hop_length,
                args.f0method,
                args.output_tts_path,
                args.output_rvc_path,
                args.pth_file,
                args.index_path,
            )
    except Exception as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
