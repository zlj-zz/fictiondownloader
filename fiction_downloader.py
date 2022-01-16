import os
import time
import json
import requests
from lxml import etree
import urllib3


headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:80.0) Gecko/20100101 Firefox/80.0",
}

# 飞山中文
class Downloader(object):
    def __init__(self, conf: dict = {}, auto_load_conf: bool = True) -> None:
        if conf:
            self.conf = conf
        else:
            with open("./conf.json", "r") as f:
                self.conf = json.load(f)
        # print(self.conf)

        self.auto_load_conf = auto_load_conf
        self.already_loaded_conf = False

    def load_conf(self):
        conf = self.conf

        self.fiction_name = conf.get("fiction_name", "")
        self.base_url = conf.get("base_url", "")

        search_conf = conf.get("search", {})
        search_url_is_completed = search_conf.get("url_is_completed", False)
        self.search_url = search_conf.get("url", "")
        if not search_url_is_completed:
            self.search_url = self.base_url + self.search_url
        self.search_base_xpath = search_conf.get("base_xpath", "")
        self.search_url_xpath = search_conf.get("url_xpath", "")
        self.search_name_xpath = search_conf.get("name_xpath", "")
        self.search_author_xpath = search_conf.get("author_xpath", "")

        desc_conf = conf.get("desc", {})
        self.chapter_xpath = desc_conf.get("chapter_xpath", "")

        chapter_conf = conf.get("chapter", {})
        self.chapter_url_is_completed = chapter_conf.get("url_is_completed", False)
        self.chapter_title_xpath = chapter_conf.get("title_xpath", "")
        self.chapter_content_xpath = chapter_conf.get("content_xpath", "")

        self.download_sleep = conf.get("download_sleep", 0.2)
        self.request_verify = conf.get("request_verify", True)
        if not self.request_verify:
            # Don't output warn.
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Modify conf status.
        self.already_loaded_conf = True

    def get_html(self, url, encoding="utf-8"):
        # TODO:force request. It's not good.
        try:
            resp = requests.get(url, verify=self.request_verify)
        except requests.exceptions.ConnectTimeout:
            return self.get_html(url, encoding)

        html = resp.content.decode(encoding)
        return html

    def parse_search_html(self, html_code):
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

            for url, name, author in zip(urls, names, authors):
                res.append([url, name, author])

        return res

    def parse_desc_html(self, html_code):
        html_tree = etree.HTML(html_code)

        items = html_tree.xpath(self.chapter_xpath)
        urls = sorted(items)

        total = len(items)

        return total, urls

    def parse_chapter_html(self, html_code):
        html_tree = etree.HTML(html_code)

        title = html_tree.xpath(self.chapter_title_xpath)[0]
        items = html_tree.xpath(self.chapter_content_xpath)

        chapter = "\n".join(items)
        chapter = (
            chapter.replace("&nbsp", "")
            .replace("<sript>()</sript>", "")
            .replace("<sript>();</sript>", "")
        )
        return title, chapter

    def downloader(self):
        if self.auto_load_conf:
            self.load_conf()
        if not self.already_loaded_conf:
            print("Please manual load conf.")
            return

        # search fiction.
        print(f"Search fiction {self.fiction_name}:")
        search_html = self.get_html(self.search_url.format(self.fiction_name))
        search_res = self.parse_search_html(search_html)

        # show search result.
        if not search_res:
            print("No search results or xpath is not right.")
            return

        for search_res_item in search_res:
            print(*search_res_item[1:])
        while True:
            idx = input(f"input choice(0-{len(search_res)-1}):")
            try:
                idx = int(idx)
                if idx >= len(search_res) or idx < 0:
                    continue
            except Exception:
                continue
            else:
                break

        # Get info.
        print("\nOutput Info:")

        saved_name = search_res[idx][1] + ".txt"
        print(f"--> Save name is:'{saved_name}'")

        desc_url = self.base_url + search_res[idx][0]
        print(f"--> Catalogue url: {desc_url}")

        desc_html = self.get_html(desc_url)
        total, urls = self.parse_desc_html(desc_html)
        print(f"--> Total {total} chapters.")

        #
        if os.path.exists(saved_name):
            with open(saved_name, "w") as f:
                pass

        # Download chapter and save.
        start_t = time.time()
        print("\nStart Download:")
        print("\033[s")  # Mark current position (-2, 1)
        for progress, sub_url in enumerate(urls, start=1):
            if not self.chapter_url_is_completed:
                chapter_url = self.base_url + sub_url
            else:
                chapter_url = sub_url

            # Get one chapter.
            chapter_html = self.get_html(chapter_url)
            chapter_title, chapter_content = self.parse_chapter_html(chapter_html)
            # print(chapter_title, chapter_content)

            # Write to file.
            with open(saved_name, "a+") as f:
                f.write(chapter_title + "\n")
                f.write(chapter_content + "\n\n")

            print(
                "\033[u-->", progress, chapter_url, "\033[K"
            )  # Goto the mark position to print and clear subsequent.
            print(
                f"\r:: Number of downloaded chapters: {progress / total * 100:.2f}%, "
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


if __name__ == "__main__":
    conf = {
        "fiction_name": "问道红尘",
        "base_url": "https://www.feishanzw.com",
        "search": {
            "url": "/search.php?search={0}",
            "url_is_completed": False,
            "base_xpath": "/html/body/section[3]/div/div[1]/table/tbody/tr",
            "url_xpath": "./td[1]/a/@href",
            "name_xpath": "./td[1]/a/text()",
            "author_xpath": "./td[3]/text()",
        },
        "desc": {
            "chapter_xpath": "/html/body/section[4]/div/div[1]/ul/li/a/@href",
        },
        "chapter": {
            "is_completed": False,
            "title_xpath": "/html/body/section[3]/div/div[2]/h1/text()",
            "content_xpath": "/html/body/section[3]/div/div[2]/article/text()",
        },
        "download_sleep": 3,
        "request_verify": False,
    }
    # with open("./conf.json", "w") as f:
    #     json.dump(conf, f, indent=2)

    # downloader = Downloader(conf)
    downloader = Downloader()
    downloader.run()
