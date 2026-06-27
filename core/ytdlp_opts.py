import shutil

from core.config import settings


def build_base_ytdl_opts() -> dict:
    opts: dict = {
        "quiet": True,
        "noprogress": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web", "ios"],
            }
        },
        "remote_components": ["ejs:github"],
    }

    if shutil.which("node"):
        opts["js_runtimes"] = {"node": {}}

    if settings.cookies_browser:
        opts["cookiesfrombrowser"] = (settings.cookies_browser,)

    return opts
