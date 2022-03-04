import textwrap, time, os
from argparse import ArgumentParser

from .downloader import Downloader
from .extractor import Extractor
from .utils import splicing_url, slice_list
from .const import DEFAULT_HTM

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


def parse_cmd():
    parser = ArgumentParser(prog="noval", description="", prefix_chars="-")

    # add command.
    parser.add_argument("name", type=str, help="fiction name.")
    parser.add_argument("--sep", type=float, help="sleep time.")
    parser.add_argument("--save-to", metavar="path", help="custom fiction save path.")
    parser.add_argument(
        "--range",
        nargs=2,
        type=int,
        help="Download chapter range, like:`--range 10 20`",
    )
    exc_group = parser.add_mutually_exclusive_group()
    exc_group.add_argument("--split", type=int, help="Download segmented storage.")
    exc_group.add_argument(
        "--append",
        action="store_true",
        help="Whether it is in append mode. It is recreated by default.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        help="Show version and exit.",
        version="noval version: 2022.02.28",
    )

    # parse command.
    args, unknown = parser.parse_known_args()

    # process command.
    return args, unknown


search_list = [
    "https://www.feishanzw.com/search.php?search={0}",
    "https://www.kankezw.com/search.html?searchkey={0}",
]


def run(conf: dict):
    dr = Downloader(verify=False)
    er = Extractor()
    console = Console()

    # Init
    console.print(conf)
    fiction_name = conf["name"]
    sep = conf["sep"] or 0
    dir_path = os.path.abspath(conf["path"] or ".")
    chapter_range = conf["range"]
    split = conf.get("split")
    is_append = conf.get("append", False)

    # Search
    search_res = []

    with console.status(
        f"Search: [bold green]'{fiction_name}'...", spinner="shark"
    ) as st:
        for search_url in search_list:
            html, _ = dr.get_html(search_url.format(fiction_name))
            search_res.extend(
                er.extract_search(html or DEFAULT_HTM, fiction_name, search_url)
            )

    if not search_res:
        console.print("[red]Can't get search result page.")
        return

    # Show search result.
    res_t = Table(title="Search Result", collapse_padding=True)
    res_t.add_column("Idx", style="green")
    res_t.add_column("Fiction Name", style="yellow")
    res_t.add_column("Last Update", style="cyan")
    res_t.add_column("Other Info")

    for search_no, search_res_item in enumerate(search_res, start=1):
        res_t.add_row(str(search_no), *search_res_item[0].split("|"))

    console.print(res_t)

    # Choice.
    while True:
        idx = input(f"input choice(1-{len(search_res)}):")
        try:
            idx = int(idx) - 1
            if idx >= len(search_res) or idx < 0:
                print("\033[1A\rerror: Index out of range.\033[K")
                continue
        except Exception:
            print("\033[1A\rerror: Please input a number.\033[K")
        else:
            break

    # Get chapters.
    real_name = search_res[idx][0].split("|")[0]
    real_path = os.path.join(dir_path, real_name)
    next_url = splicing_url(search_url, search_res[idx][1])
    console.print(
        Panel(
            f"[yellow]{real_name}[/yellow], {next_url}", title="Selected", expand=False
        )
    )

    html, u = dr.get_html(next_url)
    res = er.extract_chapters(html or DEFAULT_HTM, u)

    if not res:
        next_url = er.extract_detail(html or DEFAULT_HTM, u)
        if next_url:
            console.print(f"Get next url: {next_url}")
            html, u = dr.get_html(next_url)
            res = er.extract_chapters(html or DEFAULT_HTM, u)

    if not res:
        console.print("[red]No chapter found!")
        return

    console.print(f"{len(res):=^100}")

    if chapter_range:
        res = res[chapter_range[0] - 1 : chapter_range[1] - 1]

    # Download
    def _download_chapters(
        res, path: str, desc: str = "download", over_desc: str = "downloaded"
    ):
        if not is_append:
            with open(path, "w") as f:
                pass

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
            overall_task_id = overall_progress.add_task(desc, total=len(res))
            # for chapter_name, url in track(res, desc, console=console):
            for idx, (chapter_name, url) in enumerate(res):
                # console.print(chapter_name, url)
                current_show_progress.update(
                    current_show_id, description=f"「{idx:^7}」 {chapter_name} {url}"
                )

                while True:
                    html, _ = dr.get_html(url)

                    if not html:
                        try_ans = input(f"Are you want to try again (y/n):").lower()
                        if try_ans in ["y", "Y", "yes", "Yes"]:
                            print("\033[1A\rRe-trying...\033[K")
                            continue
                        else:
                            print("INFO: Can't get current chapter page.")
                            return
                    else:
                        break

                content = er.extract_content(html)

                if not content:
                    continue

                chapter_content = f"{chapter_name}\n{textwrap.indent(content,'  ')}\n\n"
                dr.save(path, chapter_content, mode="a+")

                overall_progress.update(overall_task_id, advance=1)
                time.sleep(sep)

            overall_progress.update(overall_task_id, description=over_desc)
            current_show_progress.stop_task(current_show_id)
            current_show_progress.update(current_show_id, visible=False)

    if split and split > 1:
        part_id = 1
        for part_res in slice_list(res, len(res) // split + 1):
            _download_chapters(
                part_res,
                f"{real_path}.txt".replace(".txt", f"_{part_id}.txt"),
                f"[green bold]Download part {part_id}...",
                f"[green bold]Part {part_id} downloaded",
            )
            part_id += 1
    else:
        _download_chapters(
            res, f"{real_path}.txt", "[green bold]Download...", "[green bold]Downloaded"
        )


def main():
    args, unknown = parse_cmd()

    conf = {
        "name": args.name,
        "sep": args.sep,
        "path": args.save_to,
        "split": args.split,
        "range": args.range,
        "append": args.append,
    }

    try:
        run(conf)
        print("==end==")
    except (KeyboardInterrupt,):
        print("\nManual Stop.")
