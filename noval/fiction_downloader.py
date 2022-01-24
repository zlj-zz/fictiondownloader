# /usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import re
import time
import json
import requests
import urllib3
from lxml import etree
from argparse import ArgumentParser


RUN_PATH = os.path.dirname(__file__)
DEFAULT_CONF_FILE = "noval_conf.json"
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0",
}

URL_RE = re.compile(
    r"(http|ftp|https):\/\/[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?"
)

# 飞山中文
class Downloader(object):
    def __init__(
        self,
        conf: dict = {},
        conf_path: str = "",
        auto_load_conf: bool = True,
        debug: bool = False,
    ) -> None:
        self.conf = conf
        self.conf_path = conf_path
        self.fiction_name = ""
        self.saved_name = ""
        self.save_path = ""

        self.search_res_url = ""
        self.desc_res_url = ""
        self.desc_url = ""

        self.auto_load_conf = auto_load_conf
        self.already_loaded_conf = False

        self.debug = debug

    def read_conf_from_file(self, conf_path: str) -> dict:
        conf = {}

        if conf_path:
            if not os.path.isfile(conf_path):
                print("INFO: Config path is not exist.")
            if not conf_path.endswith(".json"):
                print("INFO: Config must be a json file.")

            # read given config.
            conf = self.read_json(conf_path)
        elif os.path.isfile(DEFAULT_CONF_FILE):
            # read current path default config.
            conf = self.read_json(DEFAULT_CONF_FILE)
        else:
            # read default config.
            conf = self.read_json(os.path.join(RUN_PATH, "..", DEFAULT_CONF_FILE))

        return conf

    def read_json(self, json_path: str) -> dict:
        res = {}

        try:
            with open(json_path, "r") as f:
                res = json.load(f)
        except json.decoder.JSONDecodeError:
            print("ERROR: The json file is not right.")

        return res

    def load_conf(self):
        if not self.conf:
            self.conf = self.read_conf_from_file(self.conf_path)

        # print(self.conf)
        conf = self.conf
        if not conf:
            print("INFO: Don't have config can be loaded.")
            return

        # Parse config.
        if not self.fiction_name:
            self.fiction_name = conf.get("fiction_name", "")
        self.base_url = conf.get("base_url", "")

        search_conf = conf.get("search", {})
        self.search_url = search_conf.get("url", "")
        if not URL_RE.match(self.search_url):
            self.search_url = self.base_url + self.search_url
        self.search_base_xpath = search_conf.get("base_xpath", "")
        self.search_url_xpath = search_conf.get("url_xpath", "")
        self.search_name_xpath = search_conf.get("name_xpath", "")
        self.search_author_xpath = search_conf.get("author_xpath", "")

        desc_conf = conf.get("desc", {})
        self.catalogue_url_xpath = desc_conf.get("catalogue_url_xpath", "")
        self.chapter_xpath = desc_conf.get("chapter_xpath", "")

        chapter_conf = conf.get("chapter", {})
        self.chapter_title_xpath = chapter_conf.get("title_xpath", "")
        self.chapter_content_xpath = chapter_conf.get("content_xpath", "")

        self.download_sleep = conf.get("download_sleep", 0.3)
        self.request_verify = conf.get("request_verify", True)
        if not self.request_verify:
            # Don't output warn.
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Process config.
        warns = []
        if not self.fiction_name:
            warns.append("ERROR: Must Give a fiction name.")
        if not self.base_url:
            warns.append(
                "ERROR: Cannot miss base url, because has url is not completed."
            )

        if warns:
            for warn in warns:
                print(warn)
            return
        else:
            # Modify conf status.
            self.already_loaded_conf = True

    def get_html(self, url, encoding="utf-8", retry=5):
        # TODO:force request. It's not good.
        try:
            resp = requests.get(url, verify=self.request_verify)
        except requests.exceptions.ConnectTimeout:
            if retry > 0:
                return self.get_html(url, encoding, retry - 1)
            else:
                print("INFO: connect the url timeout.")
                return
        except requests.exceptions.SSLError:
            print("INFO: SSL certificate verify failed.")
            return ""
        except requests.exceptions.ConnectionError:
            # TODO: may header alive-keep
            if retry > 0:
                return self.get_html(url, encoding, retry - 1)
            else:
                print("INFO: connect the url timeout.")
                return

        html = resp.content.decode(encoding)
        url = resp.url
        print("true", url)

        return html, url

    def parse_search_html(self, html_code: str):
        # print(html_code)
        html_tree = etree.HTML(html_code)

        res = []

        if self.search_base_xpath:
            items = html_tree.xpath(self.search_base_xpath)

            for item_tree in items:
                url = item_tree.xpath(self.search_url_xpath)[0]
                name = item_tree.xpath(self.search_name_xpath)[0]
                author = item_tree.xpath(self.search_author_xpath)[0]
                # update_time = item_tree.xpath("./td[4]/text()")[0]
                res.append([url, name, author])
        else:
            urls = html_tree.xpath(self.search_url_xpath)
            names = html_tree.xpath(self.search_name_xpath)
            authors = html_tree.xpath(self.search_author_xpath)
            # print(urls, names, authors)

            for url, name, author in zip(urls, names, authors):
                res.append([url, name, author])

        return res

    def parse_desc_html(self, html_code: str):
        html_tree = etree.HTML(html_code)
        res = html_tree.xpath(self.catalogue_url_xpath)
        if not res:
            self.desc_res_url = ""
        else:
            self.desc_res_url = res[0]

    def parse_catalogue_html(self, html_code: str):
        html_tree = etree.HTML(html_code)

        items = html_tree.xpath(self.chapter_xpath)
        urls = sorted(items)

        total = len(items)

        return total, urls

    def parse_chapter_html(self, html_code: str):
        html_tree = etree.HTML(html_code)

        title = html_tree.xpath(self.chapter_title_xpath)[0]
        items = html_tree.xpath(self.chapter_content_xpath)

        chapter = "\n".join(items)

        # special process.
        chapter = (
            chapter.replace("&nbsp", "")
            .replace("<sript>()</sript>", "")
            .replace("<sript>();</sript>", "")
        )
        return title, chapter

    def process_search(self, search_html: str):
        search_res = self.parse_search_html(search_html)

        # show search result.
        if not search_res:
            print("INFO: No search results or xpath is not right.")
            return

        for search_no, search_res_item in enumerate(search_res, start=1):
            print(search_no, *search_res_item[1:])

        # download choice.
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

        # Set info
        self.saved_name = search_res[idx][1] + ".txt"
        self.save_path = os.path.join(self.save_path, self.saved_name)
        self.search_res_url = search_res[idx][0]

    def process_desc(self):
        pass

    def process_chapter(self):
        pass

    def downloader(self):
        if self.auto_load_conf:
            self.load_conf()
        if not self.already_loaded_conf:
            print("The configuration file was not loaded correctly.")
            return

        # search fiction.
        print(f"Search fiction {self.fiction_name}:")
        search_html, _ = self.get_html(self.search_url.format(self.fiction_name))
        if not search_html:
            print("INFO: Can't get search result page.")
            return
        self.process_search(search_html)

        if self.search_res_url:
            print(self.search_res_url)
            # has desc page.
            if self.catalogue_url_xpath:
                desc_html, _ = self.get_html(self.base_url + self.search_res_url)
                self.parse_desc_html(desc_html)
                print(self.desc_res_url)

                catalogue_html, _ = self.get_html(self.base_url + self.desc_res_url)
            else:
                catalogue_html, _ = self.get_html(self.base_url + self.search_res_url)
            print(_)

            if not catalogue_html:
                print("INFO: Can't get catalogue page.")
                return
        else:
            # may only one result, goto dest page.
            print("INFO: Try to replace search page to desc page.")
            catalogue_html = search_html
            self.saved_name = self.fiction_name + ".txt"
            self.save_path = os.path.join(self.save_path, self.saved_name)

        # Output info.
        print("\nOutput Info:")
        print(f"--> Save name is:'{self.saved_name}'")
        print(f"--> Save path is:'{self.save_path}'")

        # Process chapters.
        total, urls = self.parse_catalogue_html(catalogue_html)
        if not total or not urls:
            print("INFO: Not found any chapters.")
        print(f"--> Total {total} chapters.")

        # Clear exist file.
        if os.path.exists(self.saved_name):
            with open(self.saved_name, "w") as f:
                pass

        # Download chapter and save.
        start_t = time.time()
        print("\nStart Download:")
        # print("\033[s")  # Mark current position (-2, 1)
        for progress, sub_url in enumerate(urls, start=1):
            if not URL_RE.match(sub_url):
                chapter_url = os.path.join(self.base_url, sub_url.lstrip("/"))
            else:
                chapter_url = sub_url

            # Get one chapter.
            while True:
                chapter_html, _ = self.get_html(chapter_url)
                if not chapter_html:
                    try_ans = input(f"Are you want to try again (y/n):").lower()
                    if try_ans in ["y", "Y", "yes", "Yes"]:
                        print("\033[1A\rRe-trying...\033[K")
                        continue
                    else:
                        print("INFO: Can't get current chapter page.")
                        return
                else:
                    break
            chapter_title, chapter_content = self.parse_chapter_html(chapter_html)
            # print(chapter_title, chapter_content)

            # Write to file.
            with open(self.save_path, "a+") as f:
                f.write(chapter_title + "\n")
                f.write(chapter_content + "\n\n")

            print(
                "\r-->", progress, chapter_url, "\033[K"
            )  # Goto the mark position to print and clear subsequent.
            print(
                f"\r:: Percent of downloaded chapters: {progress / total * 100:.2f}%, "
                f"speed time: {time.time()-start_t:.1f}s",
                end="",
            )
            time.sleep(self.download_sleep)

        print("\n==END==")

    def run(self):
        try:
            self.downloader()
        except (KeyboardInterrupt):
            print("\nManual stop.")


def parse_cmd():
    parser = ArgumentParser(prog="novel", description="", prefix_chars="-")

    # add command.
    parser.add_argument(
        "-n", "--name", type=str, metavar="fiction_name", help="custom fiction name."
    )
    parser.add_argument("--conf", type=str, metavar="path", help="custom config path.")
    parser.add_argument(
        "--save-to", type=str, metavar="path", help="custom fiction save path."
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        help="Show version and exit.",
        version="novel version 1.0.0",
    )
    # parse command.
    args, unknown = parser.parse_known_args()
    # print(args, unknown)

    # process command.
    return args, unknown


def main():
    args, unknown = parse_cmd()
    if unknown:
        print(f"Not support command: {unknown}")

    downloader = Downloader(auto_load_conf=False)

    if args.name:
        downloader.fiction_name = args.name
    if args.conf:
        downloader.conf_path = args.conf
    if args.save_to:
        downloader.save_path = args.save_to

    downloader.load_conf()
    downloader.run()


if __name__ == "__main__":
    conf = {
        "fiction_name": "问道红尘",
        "base_url": "https://www.feishanzw.com",
        "search": {
            "url": "/search.php?search={0}",
            "base_xpath": "/html/body/section[3]/div/div[1]/table/tbody/tr",
            "url_xpath": "./td[1]/a/@href",
            "name_xpath": "./td[1]/a/text()",
            "author_xpath": "./td[3]/text()",
        },
        "desc": {
            "chapter_xpath": "/html/body/section[4]/div/div[1]/ul/li/a/@href",
        },
        "chapter": {
            "title_xpath": "/html/body/section[3]/div/div[2]/h1/text()",
            "content_xpath": "/html/body/section[3]/div/div[2]/article/text()",
        },
        "download_sleep": 3,
        "request_verify": False,
    }
    main()
