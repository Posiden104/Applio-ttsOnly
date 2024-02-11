import gradio as gr
import sys
import os
import logging

now_dir = os.getcwd()
sys.path.append(now_dir)

# Tabs
from tabs.report.report import report_tab
from tabs.download.download import download_tab
from tabs.tts.tts import tts_tab
from tabs.settings.themes import theme_tab
from tabs.plugins.plugins import plugins_tab

# Assets
import assets.themes.loadThemes as loadThemes
from assets.i18n.i18n import I18nAuto
import assets.installation_checker as installation_checker

i18n = I18nAuto()
installation_checker.check_installation()
logging.getLogger("uvicorn").disabled = True
logging.getLogger("fairseq").disabled = True

my_applio = loadThemes.load_json()
if my_applio:
    pass
else:
    my_applio = "ParityError/Interstellar"

with gr.Blocks(theme=my_applio, title="Applio") as Applio:
    gr.Markdown("# Applio")
    gr.Markdown(
        i18n(
            "Ultimate voice cloning tool, meticulously optimized for unrivaled power, modularity, and user-friendly experience."
        )
    )
    gr.Markdown(
        i18n(
            "[Support](https://discord.gg/IAHispano) — [Discord Bot](https://discord.com/oauth2/authorize?client_id=1144714449563955302&permissions=1376674695271&scope=bot%20applications.commands) — [Find Voices](https://applio.org/models) — [GitHub](https://github.com/IAHispano/Applio)"
        )
    )
    # with gr.Tab(i18n("Inference")):
    #     inference_tab()

    # with gr.Tab(i18n("Train")):
    #     train_tab()

    with gr.Tab(i18n("TTS")):
        tts_tab()

    # with gr.Tab(i18n("Extra")):
    #     extra_tab()

    with gr.Tab(i18n("Plugins")):
        plugins_tab()

    with gr.Tab(i18n("Download")):
        download_tab()

    with gr.Tab(i18n("Report a Bug")):
        report_tab()

    with gr.Tab(i18n("Settings")):
        theme_tab()


if __name__ == "__main__":
    # download_background_video(get_background_config("video"))
    Applio.launch(
        favicon_path="assets/ICON.ico",
        share="--share" in sys.argv,
        inbrowser="--open" in sys.argv,
        server_port=6969,
    )
