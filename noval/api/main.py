from typing import Dict
import os, threading
from urllib.parse import urlencode

from noval.downloader import Downloader
from .utils import encode64, decode64

try:
    from fastapi import FastAPI
    from fastapi.responses import StreamingResponse, HTMLResponse
    from fastapi.middleware.cors import CORSMiddleware
except ModuleNotFoundError:
    print("Use 'pip install fastapi' to install fastapi first.")
    exit(1)


dr = Downloader(verify=False)
app = FastAPI()

# CORS allow any host.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

curr_crawl_status: Dict[str, int] = {}
dir_path = os.path.dirname(os.path.abspath("."))
print(dir_path)
# dir_path = f"{dir_path}/.."

encodekey = lambda fname, url: encode64(f"{fname}@@@{url}")
decodekey = lambda key: decode64(key).split("@@@")


@app.get("/")
def index():
    indexfile = os.path.join(dir_path, "index.html")
    with open(indexfile) as f:
        html_string = f.read()
        return HTMLResponse(html_string)


@app.get("/fiction")
def get_fictions(name: str):
    """Get fiction list follow name."""
    data = {}

    if name is not None:
        idx = 0
        for each in dr.search_fiction(name):
            for msg_string, url in each:
                fname, dt, info = msg_string.split("|")
                key = encodekey(fname, url)

                data[idx] = {"name": fname, "date": dt, "info": info, "key": key}
                idx += 1

    return {"data": data}


@app.get("/chapters")
def get_chapters(key: str):
    """Get fiction chapters list."""
    return {"data": dr.get_chapters(decodekey(key)[1])}


@app.get("/crawl")
def crawl(key: str):
    """Try to crawl a fiction."""
    global curr_chapter_idx

    # process fiction name
    fname, target_url = decodekey(key)
    filename = f"{key}.txt"
    print(target_url, filename)

    # get fiction chapters
    chapters = dr.get_chapters(target_url)
    print(chapters)

    if chapters:
        curr_crawl_status[key] = 0

        def _c():

            for idx, msg in enumerate(
                dr.download_chapters(chapters, os.path.join(dir_path, f"{key}.txt"))
            ):
                print(msg)
                curr_crawl_status[key] = idx
            curr_crawl_status[key] = -200

        threading.Thread(target=_c, daemon=True).start()

        data = {"total": len(chapters), "key": key}
    else:
        data = {"total": 0, "key": ""}

    return {"data": data}


@app.get("/crawl_status")
def get_crawl_status(key: str):
    """Get current crawl progress of key."""
    global curr_crawl_status
    data = {"current": curr_crawl_status.get(key, 0)}
    return {"data": data}


@app.get("/download")
def download(key: str):
    """Download fiction follow key."""
    fname, url = decodekey(key)
    filename = f"{fname}.txt"
    filepath = os.path.join(dir_path, f"{key}.txt")

    def _iter_file():
        with open(filepath) as file_like:
            yield from file_like

    headers = {"Content-Disposition": f"attachment;{urlencode({'filename':filename})}"}
    return StreamingResponse(
        _iter_file(), headers=headers, media_type="text/plain; charset=utf-8"
    )


# uvicorn api:app --reload
