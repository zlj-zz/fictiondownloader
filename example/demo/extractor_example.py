import os, sys, glob
from pprint import pprint

_PATH = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, _PATH)
print(_PATH)

from noval.extractor import Extractor


_EXAMPLE_DIR = f"{_PATH}/example/html"


def demo1():
    name = "大主宰"
    html_list = glob.glob(f"{_EXAMPLE_DIR}/search_*.html", recursive=True)
    for html in html_list:
        with open(html) as f:
            pprint(Extractor().extract_search(f.read(), name))


def demo2():
    html_list = glob.glob(f"{_EXAMPLE_DIR}/desc_*.html", recursive=True)
    for html in html_list:
        with open(html) as f:
            pprint(Extractor().extract_detail(f.read()))


def demo3():
    html_list = glob.glob(f"{_EXAMPLE_DIR}/chapters_*.html", recursive=True)
    for html in html_list:
        with open(html) as f:
            pprint(Extractor().extract_chapters(f.read()))


def demo4():
    html_list = glob.glob(f"{_EXAMPLE_DIR}/content_*.html", recursive=True)
    for html in html_list:
        with open(html) as f:
            pprint(Extractor().extract_content(f.read()))


if __name__ == "__main__":
    # demo1()
    # demo2()
    # demo3()
    demo4()
