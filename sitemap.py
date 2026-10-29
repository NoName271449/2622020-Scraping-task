import csv
import time
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlsplit

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


START_URL = "https://www.musashino-u.ac.jp/"
OUTPUT_FILE = Path(__file__).with_name("sitemap.csv")


def crawl(start_url=START_URL, interval=1):
    urls = [start_url]
    visited = {start_url}
    page_titles = {}
    domain = urlsplit(start_url).netloc

    with tqdm(total=1, desc="発見済みURL", unit="URL") as progress:
        for url in urls:
            # アクセスする前に少し待つ
            time.sleep(interval)
            res = requests.get(url, allow_redirects=False)

            # 転送先もリンクと同じように調べる
            if res.is_redirect:
                links = [res.headers["Location"]]
            elif "text/html" in res.headers.get("Content-Type", ""):
                soup = BeautifulSoup(res.content, "html.parser")
                title = soup.find("title")
                page_titles[url] = title.get_text().strip() if title else ""
                links = [a["href"] for a in soup.find_all("a", href=True)]
            else:
                links = []

            # 同じドメインのリンクを追加する
            for link in links:
                link = urldefrag(urljoin(url, link))[0]
                parts = urlsplit(link)
                if parts.scheme in ("http", "https") and parts.netloc == domain:
                    if link not in visited:
                        urls.append(link)
                        visited.add(link)

            # 新しいリンクが見つかったら総数も増やす
            progress.total = len(urls)
            progress.set_postfix({"取得": len(page_titles), "待機": len(urls) - progress.n - 1}, refresh=False)
            progress.update(1)

    return page_titles


def save_csv(page_titles, output_file=OUTPUT_FILE):
    # 辞書のURLとタイトルをCSVに書き込む
    with open(output_file, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["URL", "title"])
        writer.writerows(page_titles.items())


if __name__ == "__main__":
    page_titles = crawl()
    save_csv(page_titles)
    print("sitemap.csvに保存しました")
