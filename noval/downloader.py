from typing import List, Optional, Tuple
import os
import textwrap
import time
import requests
import urllib3

from .extractor import Extractor
from .utils import splicing_url, slice_list
from .const import DEFAULT_HTM, SEARCH_LIST

from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.progress import (
    track,
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)


class DownloaderError(Exception):
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
        console: Console = Console(),
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
        self._console = console

    #########
    # tools
    #########
    def _get_html(self, url: str, retry: int) -> Tuple[str, str]:
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

    def save(self, file: str, content: str, mode: str = "w") -> None:
        with open(file, mode=mode) as fp:
            fp.write(content)

    def clear(self, file: str) -> None:
        with open(file, mode="w") as _:
            pass

    ########
    # step
    ########
    def search_fiction(self, name: str) -> List[str]:
        search_res = []

        with self._console.status(
            f"Search: [bold green]'{name}'...", spinner="shark"
        ) as _:
            for search_url in self._search_list:
                html, _ = self.get_html(search_url.format(name))
                search_res.extend(
                    self._extractor.extract_search(
                        html or DEFAULT_HTM, name, search_url
                    )
                )

        return search_res

    def get_chapters(self, next_url: str):
        extractor = self._extractor

        html, u = self.get_html(next_url)
        res = extractor.extract_chapters(html or DEFAULT_HTM, u)
        # print(res)

        if not res:
            if next_url := extractor.extract_detail(html or DEFAULT_HTM, u):
                self._console.print(f"Get next url: {next_url}")
                html, u = self.get_html(next_url)
                res = extractor.extract_chapters(html or DEFAULT_HTM, u)

        return res

    ##########
    # display
    ##########
    def fiction_table(self, search_res: List[List[str]]) -> Table:
        tb = Table(title="Search Result", collapse_padding=True)
        tb.add_column("Idx", style="green")
        tb.add_column("Fiction Name", style="yellow")
        tb.add_column("Last Update", style="cyan")
        tb.add_column("Other Info")

        for search_no, search_res_item in enumerate(search_res, start=1):
            tb.add_row(
                f"[yellow]No.[/yellow]{search_no} ", *search_res_item[0].split("|")
            )

        return tb

    def get_choice(self, num: int) -> int:
        range_str = f"1-{num}" if num > 1 else "1"
        while True:
            idx = input(f"input choice({range_str}):")
            try:
                idx = int(idx) - 1
                if not (0 <= idx < num):
                    print("\033[1A\rerror: Index out of range.\033[K")
                    continue
            except Exception:
                print("\033[1A\rerror: Please input a number.\033[K")
            else:
                break

        return idx

    #######
    # main
    #######
    def _run(
        self,
        fiction_name: str,
        dir_path: Optional[str] = None,
        sep: float = 0.0,
        chapter_range: Optional[Tuple[int, int]] = None,
        split: Optional[int] = None,
        append_mode: bool = False,
    ):
        console = self._console
        extractor = self._extractor

        # Search
        search_res = self.search_fiction(fiction_name)
        if not search_res:
            console.print("[red]Can't get search result page.")
            return

        # Show search result.
        console.print(self.fiction_table(search_res))

        # Choice.
        idx = self.get_choice(len(search_res))

        # Get chapters.
        real_name = search_res[idx][0].split("|")[0]
        real_path = os.path.join(dir_path, real_name) if dir_path else real_name
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        next_url = search_res[idx][1]
        console.print(
            Panel(
                f"[yellow]{real_name}[/yellow], {next_url}",
                title="Selected",
                expand=False,
            )
        )

        chapters = self.get_chapters(next_url)
        if not chapters:
            console.print("[red]No chapter found!")
            return

        chapter_dispay_str = f"[Total chapters {len(chapters)}]"
        console.print(f"{chapter_dispay_str:=^100}")

        if chapter_range:
            chapters = chapters[chapter_range[0] - 1 : chapter_range[1] - 1]

        # Download
        def _download_chapters(
            down_chapters,
            path: str,
            desc: str = "download",
            over_desc: str = "downloaded",
        ):
            not append_mode and self.clear(path)

            current_show_progress = Progress(
                TimeElapsedColumn(),
                TextColumn("{task.description}"),
            )
            overall_progress = Progress(
                TextColumn("{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
            )
            progress_group = Group(current_show_progress, overall_progress)

            with Live(progress_group):
                current_show_id = current_show_progress.add_task("")
                overall_task_id = overall_progress.add_task(
                    desc, total=len(down_chapters)
                )
                # for chapter_name, url in track(res, desc, console=console):
                for idx, (chapter_name, url) in enumerate(down_chapters):
                    # console.print(chapter_name, url)
                    current_show_progress.update(
                        current_show_id, description=f"「{idx:^7}」 {chapter_name} {url}"
                    )

                    while True:
                        html, _ = self.get_html(url)

                        if html:
                            break

                        try_ans = input("Are you want to try again (y/n):").lower()
                        if try_ans in ["y", "Y", "yes", "Yes"]:
                            print("\033[1A\rRe-trying...\033[K")
                        else:
                            print("INFO: Can't get current chapter page.")
                            return

                    content = extractor.extract_content(html)

                    if not content:
                        continue

                    chapter_content = (
                        f"{chapter_name}\n{textwrap.indent(content,'  ')}\n\n"
                    )
                    self.save(path, chapter_content, mode="a+")

                    overall_progress.update(overall_task_id, advance=1)
                    time.sleep(sep)

                overall_progress.update(overall_task_id, description=over_desc)
                current_show_progress.stop_task(current_show_id)
                current_show_progress.update(current_show_id, visible=False)

        if split and split > 1:
            part_id = 1
            for part_res in slice_list(chapters, len(chapters) // split + 1):
                _download_chapters(
                    part_res,
                    f"{real_path}.txt".replace(".txt", f"_{part_id}.txt"),
                    f"[green bold]Download part {part_id}...",
                    f"[green bold]Part {part_id} downloaded",
                )
                part_id += 1
        else:
            _download_chapters(
                chapters,
                f"{real_path}.txt",
                "[green bold]Download...",
                "[green bold]Downloaded",
            )

    def run(self, conf: dict):
        self._console.print(conf)
        try:
            self._run(**conf)
            self._console.print("[green u]End ^.^")
        except (KeyboardInterrupt,):
            self._console.print("\n[yellow]Noval Manual Stop.")
