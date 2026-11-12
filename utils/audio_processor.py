ydl_opts = {
    "format": "bestaudio/best",
    "outtmpl": output_path,
    "noplaylist": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
        }
    ],
    "retries": 5,
    "fragment_retries": 5,
    "socket_timeout": 30,
    "extractor_args": {
        "youtube": {
            "player_client": ["android", "web"],
        }
    },
    # Use Node.js instead of Deno
    "js_runtimes": {"node": {}},
    "remote_components": ["ejs:github"],
    "quiet": False,
    "no_warnings": False,
}
