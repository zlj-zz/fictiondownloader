try:
    import uvicorn
except ModuleNotFoundError:
    print("Use 'pip install uvicorn[standard]' to install uvicorn first.")
    exit(1)


def api_run(host: str, port: int, reload: bool = False):
    uvicorn.run(app="noval.api.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    from argparse import ArgumentParser

    # default host and port.
    default_host: str = "127.0.0.1"
    default_port: int = 9111

    # argument parser.
    parser = ArgumentParser(description="", prefix_chars="-")

    # add command.
    parser.add_argument(
        "--host",
        type=str,
        default=default_host,
        help=f"Bind socket to this host. [default: {default_host}]",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help=f"Bind socket to this port. [default: {default_port}]",
    )
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload.")

    # parse command.
    args, unknown = parser.parse_known_args()

    if unknown:
        print(f"Warn: unknown argument {unknown}")

    # start api serve.
    api_run(args.host, args.port, args.reload)
