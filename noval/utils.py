from typing import List
from urllib import parse
import re


URL_RE = re.compile(
    r"(http|ftp|https):\/\/[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?"
)
ROOT_URL_RE = re.compile(r"^(((http|ftp|https):\/\/)?[\w\-_]+(\.[\w\-_]+)+)")


def splicing_url(base: str, part: str) -> str:
    # `part` is a full url or if `base` is not a valid url.
    if URL_RE.match(part) or not URL_RE.match(base):
        return part

    return parse.urljoin(base, part)


def slice_list(temp_list: List, n: int):
    """
    Args:
        temp_list (list):
        n (int): number of each part.
    """
    for i in range(0, len(temp_list), n):
        yield temp_list[i : i + n]


def get_keyword_pattern(keywords: List):
    return re.compile("|".join(keywords), flags=re.I)


if __name__ == "__main__":
    l = [
        ("https://www.shuquge.com/txt/72275/index.html", "11220127.html"),
        ("https://www.feishanzw.com/fs/50413.html", "/fs/50413/88177067.html"),
        ("https://www.kankezw.com/Shtml62331.html", "22648115.html"),
    ]
    for parent, child in l:
        print(splicing_url(parent, child))
