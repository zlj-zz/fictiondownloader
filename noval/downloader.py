from typing import Dict, List, Literal, Optional, Tuple, Generator
import time
import textwrap
import requests
import urllib3

from .extractor import Extractor
from .const import DEFAULT_HTM, SEARCH_LIST


class DownloaderError(Exception):
    """Error class of ~Downloader."""

    pass


class Downloader(object):
    def __init__(
        self,
        timeout: int = 10,
        retry: int = 5,
        encoding: str = "utf-8",
        verify: bool = True,
        urls: Optional[str] = None,
        extractor: Extractor = Extractor(),
    ) -> None:
        if urls is None:
            urls = []
        self.timeout = timeout
        self.retry = retry
        self.encoding = encoding
        self.verify = verify
        if not verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self._search_list = [*SEARCH_LIST, *urls]
        self._extractor = extractor

    #########
    # tools
    #########
    def _get_html(
        self,
        url: str,
        retry: int,
        mode: Literal["get", "post"] = "get",
        data: Optional[Dict] = None,
    ) -> Tuple[str, str]:
        html, true_url = "", ""

        try:
            if mode == "get":
                resp = requests.get(url, timeout=self.timeout, verify=self.verify)
            elif mode == "post":
                resp = requests.post(
                    url, data, timeout=self.timeout, verify=self.verify
                )
            else:
                raise DownloaderError(
                    "request method please give 'get' or 'post'."
                ) from None
        except (
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout,
        ):
            # TODO: may header alive-keep
            if retry > 0:
                return self._get_html(url, retry - 1)
        except requests.exceptions.SSLError:
            raise DownloaderError(
                "Get SSLError, should set `verify` to False."
            ) from None
        else:
            html = resp.content.decode(self.encoding)
            true_url = resp.url

        return html, true_url

    def get_html(self, url: str):
        return self._get_html(url, self.retry)

    def save(self, file: str, content: str, mode: str = "w") -> None:
        with open(file, mode=mode) as fp:
            fp.write(content)

    def clear(self, file: str) -> None:
        with open(file, mode="w") as _:
            pass

    ########
    # step
    ########
    def search_fiction(self, name: str) -> Generator:
        """"""

        for search_url in self._search_list:
            html, _ = self.get_html(search_url.format(name))
            yield self._extractor.extract_search(html or DEFAULT_HTM, name, search_url)

    def get_chapters(self, next_url: str) -> List:
        extractor = self._extractor

        html, u = self.get_html(next_url)
        res = extractor.extract_chapters(html or DEFAULT_HTM, u)
        # print(res)

        if not res:
            if next_url := extractor.extract_detail(html or DEFAULT_HTM, u):
                # print(f"Get next url: {next_url}")
                html, u = self.get_html(next_url)
                res = extractor.extract_chapters(html or DEFAULT_HTM, u)

        return res

    def download_chapters(
        self,
        down_chapters: List[Tuple[str, str]],
        path: str,
        sep: float = 0.0,
        append_mode: bool = False,
    ) -> Generator:
        extractor = self._extractor
        not append_mode and self.clear(path)

        for chapter_name, url in down_chapters:
            # console.print(chapter_name, url)

            while True:
                html, _ = self.get_html(url)

                if html:
                    break

                flag = yield (None, None)
                if flag:
                    continue
                else:
                    return

            content = extractor.extract_content(html)

            if not content:
                continue

            chapter_content = f"{chapter_name}\n{textwrap.indent(content,'  ')}\n\n"
            self.save(path, chapter_content, mode="a+")

            time.sleep(sep)
            yield chapter_name, url
