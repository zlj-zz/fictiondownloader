import os
import re


URL_RE = re.compile(
    r"(http|ftp|https):\/\/[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?"
)
ROOT_URL_RE = re.compile(r"^(((http|ftp|https):\/\/)?[\w\-_]+(\.[\w\-_]+)+)")


def splicing_url(base: str, part: str):
    # `part` is a full url.
    # if `base` is not a valid url.
    if URL_RE.match(part) or not URL_RE.match(base):
        return part

    # get root url.
    if part.startswith("/"):
        # get root url.
        base = ROOT_URL_RE.findall(base)[0][0]

    return os.path.join(base, part.lstrip("/"))


def slice_list(temp_list: list, n: int):
    """
    Args:
        temp_list (list):
        n (int): number of each part.
    """
    for i in range(0, len(temp_list), n):
        yield temp_list[i : i + n]


def get_keyword_pattern(keywords: list):
    return re.compile("|".join(keywords), flags=re.I)
