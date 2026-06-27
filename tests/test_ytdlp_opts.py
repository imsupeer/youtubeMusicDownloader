import shutil

from core.ytdlp_opts import build_base_ytdl_opts


def test_build_base_ytdl_opts_includes_youtube_clients():
    opts = build_base_ytdl_opts()

    assert opts["extractor_args"]["youtube"]["player_client"] == [
        "android",
        "web",
        "ios",
    ]
    assert "remote_components" in opts


def test_build_base_ytdl_opts_enables_node_when_available():
    opts = build_base_ytdl_opts()

    if shutil.which("node"):
        assert opts.get("js_runtimes") == {"node": {}}
    else:
        assert "js_runtimes" not in opts
