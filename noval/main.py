from argparse import ArgumentParser

from .terminal import entry


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
        version="noval version: 2022.03.22",
    )

    # parse command.
    args, unknown = parser.parse_known_args()

    # process command.
    return args, unknown


def main():
    args, unknown = parse_cmd()

    conf = {
        "fiction_name": args.name,
        "dir_path": args.save_to,
        "sep": args.sep or 0.0,
        "chapter_range": args.range,
        "split": args.split,
        "append_mode": args.append,
    }

    entry(conf)
