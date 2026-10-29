import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import requests

import sitemap


class SitemapTest(unittest.TestCase):
    def test_crawl_links_without_duplicates_or_external_requests(self):
        root = "https://www.musashino-u.ac.jp/"
        pages = {
            root: (200, "text/html", '<title>武蔵野大学</title><a href="/a#one">A</a><a href="/a#two">A</a><a href="https://other.example/">外部</a><a href="mailto:a@example.com">メール</a><a href="/old">旧</a><a href="/file.pdf">PDF</a>', {}),
            root + "a": (200, "text/html", '<title>紹介,大学</title><a href="/">戻る</a><a href="b?x=1">B</a>', {}),
            root + "old": (302, "text/html", "", {"Location": "https://other.example/"}),
            root + "file.pdf": (200, "application/pdf", "%PDF", {}),
            root + "b?x=1": (200, "text/html", '<a href="/new">次</a>', {}),
            root + "new": (301, "text/html", "", {"Location": "/last"}),
            root + "last": (200, "text/html", "<title>最終ページ</title>", {}),
        }
        visited = []
        events = []

        def get(url, **kwargs):
            events.append("get")
            self.assertNotIn(url, visited)
            visited.append(url)
            status, content_type, body, headers = pages[url]
            response = requests.Response()
            response.status_code = status
            response.url = url
            response.headers.update({"Content-Type": content_type, **headers})
            response._content = body.encode("utf-8")
            response._content_consumed = True
            return response

        with patch("requests.get", get), patch("sitemap.time.sleep", side_effect=lambda seconds: events.append(("sleep", seconds))):
            result = sitemap.crawl(root, interval=1)

        self.assertEqual(result, {
            root: "武蔵野大学", root + "a": "紹介,大学",
            root + "b?x=1": "", root + "last": "最終ページ",
        })
        self.assertEqual(events, [("sleep", 1), "get"] * len(pages))

    def test_save_csv_preserves_japanese_commas_and_newlines(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sitemap.csv"
            sitemap.save_csv({"https://example.com/": "大学,紹介\n案内"}, path)
            with path.open(encoding="utf-8-sig", newline="") as file:
                self.assertEqual(list(csv.reader(file)), [
                    ["URL", "title"], ["https://example.com/", "大学,紹介\n案内"],
                ])


if __name__ == "__main__":
    unittest.main()
