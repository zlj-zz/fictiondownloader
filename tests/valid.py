import os, sys

# 设置 debug 环境
os.environ["NOVAL_DEBUG"] = "debug"

NOVAL_PATH = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, NOVAL_PATH)

from noval.utils import slice_list
from noval.downloader import Downloader


def valid_search(dl: Downloader):
    fiction_list = ["大主宰"]  # , "一剑独尊"]
    for fiction_name in fiction_list:
        for part_search_res in dl.search_fiction(fiction_name):
            print(part_search_res)


if __name__ == "__main__":
    dl = Downloader(verify=False)
    valid_search(dl)
