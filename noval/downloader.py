import requests
import urllib3


class DownloaderError(Exception):
    pass


class Downloader(object):
    def __init__(
        self,
        timeout: int = 10,
        retry: int = 5,
        encoding: str = "utf-8",
        verify: bool = True,
    ) -> None:
        self.timeout = timeout
        self.retry = retry
        self.encoding = encoding
        self.verify = verify
        if not verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _get_html(self, url: str, retry: int) -> tuple[str, str]:
        html, true_url = "", ""

        try:
            resp = requests.get(url, timeout=self.timeout, verify=self.verify)
        except (
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ReadTimeout,
        ):
            # TODO: may header alive-keep
            if retry > 0:
                return self._get_html(url, retry - 1)
        except requests.exceptions.SSLError:
            raise DownloaderError("Get SSLError, should set `verify` to False.")
        else:
            html = resp.content.decode(self.encoding)
            true_url = resp.url

        return html, true_url

    def get_html(self, url: str):
        return self._get_html(url, self.retry)

    def save(self, name: str, content: str, mode: str = "w"):
        with open(name, mode=mode) as fp:
            fp.write(content)
