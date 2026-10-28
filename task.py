import csv
import time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

# スキップしたいファイルの拡張子
IGNORE_EXTENSIONS = (
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".zip",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
)


def crawl_and_save_to_csv(
    start_url: str,
    output_csv: str = "sitemap.csv",
    delay: float = 0.5,
    max_pages: int = 150,
):
    base_domain = urlparse(start_url).netloc
    to_visit = [start_url]
    visited = set()
    sitemap_dict = {}

    session = requests.Session()
    session.headers.update(
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )

    print(f"--- 巡回開始: {start_url} ---")

    while to_visit and len(visited) < max_pages:
        current_url = to_visit.pop(0)

        if current_url in visited:
            continue

        parsed_url = urlparse(current_url)
        if parsed_url.path.lower().endswith(IGNORE_EXTENSIONS):
            continue

        visited.add(current_url)
        print(f"[{len(visited)}/{max_pages}] Accessing: {current_url}")

        try:
            response = session.get(current_url, timeout=5)

            # HTMLページ以外はスキップ
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                continue

            # --- 文字化け対策（ここを追加） ---
            response.encoding = response.apparent_encoding

            soup = BeautifulSoup(response.text, "html.parser")

            # <title>の取得
            title_tag = soup.find("title")
            title_text = (
                title_tag.get_text(strip=True)
                if title_tag
                else "(タイトルなし)"
            )

            # 辞書型変数に格納
            sitemap_dict[current_url] = title_text

            # リンク抽出
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                full_url = urljoin(current_url, href)

                clean_url = urlparse(full_url)._replace(fragment="").geturl()
                parsed = urlparse(clean_url)

                if (
                    parsed.netloc == base_domain
                    and clean_url not in visited
                    and clean_url not in to_visit
                ):
                    if parsed.scheme in ("http", "https"):
                        if not parsed.path.lower().endswith(IGNORE_EXTENSIONS):
                            to_visit.append(clean_url)

            time.sleep(delay)

        except Exception as e:
            print(f"Error ({current_url}): {e}")

    # CSVファイルへ保存 (utf-8-sig でBOM付き出力)
    print(
        f"\n--- CSVファイルに保存中 (合計 {len(sitemap_dict)} 件): {output_csv} ---"
    )
    with open(output_csv, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["URL", "Title"])
        for url, title in sitemap_dict.items():
            writer.writerow([url, title])

    print("完了しました！")


if __name__ == "__main__":
    TARGET_URL = "https://www.musashino-u.ac.jp/"
    crawl_and_save_to_csv(
        TARGET_URL, output_csv="sitemap.csv", delay=0.5, max_pages=150
    )