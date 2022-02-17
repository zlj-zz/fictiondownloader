import os, sys, re


def get_all_conf():
    conf_path_list = []
    dir_path = os.path.join(os.path.dirname(__file__), "../conf")

    if os.path.isdir(dir_path):
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file in ["demo.json", "noval_conf.json"] or not file.endswith(
                    "json"
                ):
                    continue

                conf_path = os.path.join(root, file)
                conf_path_list.append(conf_path)

    return conf_path_list


if __name__ == "__main__":
    # Set env
    sys.path.insert(0, os.path.dirname(__file__))
    print(sys.path)

    # Import downloader
    from fiction_downloader import Downloader, parse_cmd

    # Process command
    args, unknown = parse_cmd()
    print(args)

    if unknown:
        print(f"Not support command: {unknown}")

    d = Downloader(auto_load_conf=False)

    if args.name:
        d.fiction_name = args.name
    if args.conf:
        print("Not allowed `conf` arg.")
    if args.save_to:
        d.save_path = args.save_to
    if args.range:
        if re.match(r"^\s*\d+\s*,\s*\d+\s*$", args.range):
            range_ = args.range.replace(" ", "").split(",")
            d.start_chapter_index = int(range_[0]) - 1
            d.end_chapter_index = int(range_[1]) - 1
        else:
            print("--range is not right.")
    if args.split:
        d.split_part = args.split
    if args.append:
        d.append_mode = True

    # Run with each conf
    conf_list = get_all_conf()

    for conf in conf_list:
        d.already_loaded_conf = False
        d.conf_path = conf

        # Handle load config.
        d.load_conf()
        if d.run():
            break
