from typing import Generator, List, Optional, Tuple
import os

from .utils import slice_list
from .downloader import Downloader

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


def fiction_table(search_res: List[List[str]]) -> Table:
    tb = Table(title="Search Result", collapse_padding=True)
    tb.add_column("Idx", style="green")
    tb.add_column("Fiction Name", style="yellow")
    tb.add_column("Last Update", style="cyan")
    tb.add_column("Other Info")

    for search_no, search_res_item in enumerate(search_res, start=1):
        tb.add_row(f"[yellow]No.[/yellow]{search_no} ", *search_res_item[0].split("|"))

    return tb


def get_choice(num: int) -> int:
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


def download_with_bar(
    gen: Generator,
    total: int,
    desc: str = "download",
    over_desc: str = "downloaded",
) -> None:
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
        overall_task_id = overall_progress.add_task(desc, total=total)

        for idx, (chapter_name, url) in enumerate(gen):
            if chapter_name is None:
                try_ans = input("Are you want to try again (y/n):").lower()
                if try_ans in ["y", "Y", "yes", "Yes"]:
                    print("\033[1A\rRe-trying...\033[K")
                    gen.send(True)
                else:
                    print("INFO: Can't get current chapter page.")
                    return
            else:
                current_show_progress.update(
                    current_show_id, description=f"「{idx:^7}」 {chapter_name} {url}"
                )
                overall_progress.update(overall_task_id, advance=1)

        overall_progress.update(overall_task_id, description=over_desc)
        current_show_progress.stop_task(current_show_id)
        current_show_progress.update(current_show_id, visible=False)


console = Console()


def _entry(
    fiction_name: str,
    dir_path: Optional[str] = None,
    sep: float = 0.0,
    chapter_range: Optional[Tuple[int, int]] = None,
    split: Optional[int] = None,
    append_mode: bool = False,
) -> None:
    download = Downloader(verify=False)

    # Search
    search_res = []
    with console.status(
        f"Search: [bold green]'{fiction_name}'...", spinner="shark"
    ) as _:
        for part_search_res in download.search_fiction(fiction_name):
            search_res.extend(part_search_res)

    if not search_res:
        console.print("[red]Can't get search result page.")
        return

    # Show search result.
    console.print(fiction_table(search_res))

    # Choice.
    idx = get_choice(len(search_res))

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

    chapters = download.get_chapters(next_url)
    if not chapters:
        console.print("[red]No chapter found!")
        return

    chapter_dispay_str = f"[Total chapters {len(chapters)}]"
    console.print(f"{chapter_dispay_str:=^100}")

    if chapter_range:
        chapters = chapters[chapter_range[0] - 1 : chapter_range[1] - 1]

    # Download
    if split and split > 1:
        for part_id, part_res in enumerate(
            slice_list(chapters, len(chapters) // split + 1), start=1
        ):
            download_with_bar(
                download.download_chapters(
                    part_res,
                    f"{real_path}.txt".replace(".txt", f"_{part_id}.txt"),
                    sep,
                    append_mode,
                ),
                len(part_res),
                f"[green bold]Download part {part_id}...",
                f"[green bold]Part {part_id} downloaded",
            )
    else:
        download_with_bar(
            download.download_chapters(
                chapters,
                f"{real_path}.txt",
                sep,
                append_mode,
            ),
            len(chapters),
            "[green bold]Download...",
            "[green bold]Downloaded",
        )


def entry(conf: dict):
    console.print(conf)
    try:
        _entry(**conf)
        console.print("[green u]End ^.^")
    except (KeyboardInterrupt, EOFError):
        console.print("\n[yellow]Noval Manual Stop.")
