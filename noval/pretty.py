from typing import List, Generator

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

console = Console()


def fiction_table(search_res: List[List[str]]) -> Table:
    tb = Table(title="Search Result", collapse_padding=True)
    tb.add_column("Idx", style="green")
    tb.add_column("Fiction Name", style="yellow")
    tb.add_column("Last Update", style="cyan")
    tb.add_column("Other Info")

    for search_no, search_res_item in enumerate(search_res, start=1):
        tb.add_row(f"[yellow]No.[/yellow]{search_no} ", *search_res_item[0].split("|"))

    return tb


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
