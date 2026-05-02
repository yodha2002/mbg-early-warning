"""
scraper.py — Modul Scraping Berita Keracunan MBG
Sumber (10 media):
  Detik.com · Kompas.com · Tribunnews.com · Liputan6.com · CNN Indonesia
  Merdeka.com · Kumparan · IDN Times · Suara.com · Okezone.com

Catatan: Selector HTML bisa berubah sewaktu-waktu jika situs update tampilan.
         Periksa dan sesuaikan selector jika data tidak muncul.
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

SEARCH_QUERIES = [
    "keracunan MBG",
    "keracunan makan bergizi gratis",
    "keracunan makan siang sekolah",
    "siswa keracunan makanan",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

DELAY_SECONDS = 2
MAX_PER_QUERY = 5


def _fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, "lxml")
    except requests.RequestException as e:
        logging.error(f"  Request error [{url[:60]}]: {e}")
        return None


def _build_article(source, title_el, link_el, date_el=None, snippet_el=None):
    if not (title_el and link_el):
        return None
    title = title_el.get_text(strip=True)
    if not title:
        return None
    return {
        "source": source,
        "title": title,
        "url": link_el.get("href", ""),
        "published_date": date_el.get_text(strip=True) if date_el else "",
        "content": snippet_el.get_text(strip=True) if snippet_el else "",
    }


# 1. Detik.com
def scrape_detik(query):
    url = f"https://www.detik.com/search/searchall?query={query.replace(' ', '+')}&siteid=2"
    soup = _fetch(url)
    if not soup: return []
    articles = []
    items = soup.select("article.list-content__item") or soup.select(".list-content article")
    for item in items[:MAX_PER_QUERY]:
        a = _build_article("Detik",
            title_el=item.select_one("h3.media__title a, h2.media__title a"),
            link_el=item.select_one("a[href]"),
            date_el=item.select_one("div.media__date span, .media__date"),
            snippet_el=item.select_one(".media__desc"))
        if a: articles.append(a)
    logging.info(f"  [Detik]       '{query}' -> {len(articles)}")
    return articles


# 2. Kompas.com
def scrape_kompas(query):
    url = f"https://search.kompas.com/search/?q={query.replace(' ', '+')}&submit=Submit"
    soup = _fetch(url)
    if not soup: return []
    articles = []
    items = (soup.select(".article__list .article__item") or
             soup.select(".articleItem") or soup.select(".search-result-item"))
    for item in items[:MAX_PER_QUERY]:
        link_el = item.select_one("h3 a, h2 a, .article__title a")
        a = _build_article("Kompas", title_el=link_el, link_el=link_el,
            date_el=item.select_one(".article__date, .articleDate, time"),
            snippet_el=item.select_one(".article__lead, .articleLead, p"))
        if a: articles.append(a)
    logging.info(f"  [Kompas]      '{query}' -> {len(articles)}")
    return articles


# 3. Tribunnews.com
def scrape_tribun(query):
    url = f"https://www.tribunnews.com/search?q={query.replace(' ', '+')}"
    soup = _fetch(url)
    if not soup: return []
    articles = []
    items = (soup.select(".search-result-content li") or
             soup.select(".list-berita li") or soup.select("article.pos-relative"))
    for item in items[:MAX_PER_QUERY]:
        title_el = item.select_one("h3 a, h2 a, a.blog-title")
        a = _build_article("Tribun", title_el=title_el, link_el=title_el,
            date_el=item.select_one("time, .timeago, .date"),
            snippet_el=item.select_one("p, .desc"))
        if a: articles.append(a)
    logging.info(f"  [Tribun]      '{query}' -> {len(articles)}")
    return articles


# 4. Liputan6.com
def scrape_liputan6(query):
    url = f"https://www.liputan6.com/search?q={query.replace(' ', '+')}"
    soup = _fetch(url)
    if not soup: return []
    articles = []
    items = (soup.select("article.articles--iridescent-list--text-item") or
             soup.select(".articles--iridescent-list li") or soup.select("article"))
    for item in items[:MAX_PER_QUERY]:
        title_el = item.select_one("h4 a, h3 a, .articles--iridescent-list--text-item__title a")
        a = _build_article("Liputan6", title_el=title_el, link_el=title_el,
            date_el=item.select_one("time, .articles--iridescent-list--text-item__time"),
            snippet_el=item.select_one("p, .articles--iridescent-list--text-item__content"))
        if a: articles.append(a)
    logging.info(f"  [Liputan6]    '{query}' -> {len(articles)}")
    return articles


# 5. CNN Indonesia
def scrape_cnn_indonesia(query):
    url = f"https://www.cnnindonesia.com/search?q={query.replace(' ', '+')}"
    soup = _fetch(url)
    if not soup: return []
    articles = []
    items = (soup.select(".list.media_rows article") or
             soup.select("article.media_rows") or soup.select(".search-result article"))
    for item in items[:MAX_PER_QUERY]:
        title_el = item.select_one("h2 a, h3 a, .media__title a")
        a = _build_article("CNN Indonesia", title_el=title_el, link_el=title_el,
            date_el=item.select_one(".media__date, time"),
            snippet_el=item.select_one("p, .media__desc"))
        if a: articles.append(a)
    logging.info(f"  [CNN ID]      '{query}' -> {len(articles)}")
    return articles


# 6. Merdeka.com
def scrape_merdeka(query):
    url = f"https://www.merdeka.com/search/?q={query.replace(' ', '+')}"
    soup = _fetch(url)
    if not soup: return []
    articles = []
    items = (soup.select(".article-search-item") or
             soup.select("ul.search-list li") or soup.select(".list-item"))
    for item in items[:MAX_PER_QUERY]:
        title_el = item.select_one("h2 a, h3 a, .title a, a.article-title")
        a = _build_article("Merdeka", title_el=title_el, link_el=title_el,
            date_el=item.select_one("time, .date, .article-date"),
            snippet_el=item.select_one("p, .content, .description"))
        if a: articles.append(a)
    logging.info(f"  [Merdeka]     '{query}' -> {len(articles)}")
    return articles


# 7. Kumparan
def scrape_kumparan(query):
    url = f"https://kumparan.com/search?q={query.replace(' ', '+')}"
    soup = _fetch(url)
    if not soup: return []
    articles = []
    # Kumparan banyak pakai React — ambil dari elemen statis yang tersedia
    items = (soup.select("article") or
             soup.select(".story-card") or soup.select("[data-testid='story-card']"))
    for item in items[:MAX_PER_QUERY]:
        title_el = item.select_one("h2 a, h3 a, a[href*='/read/']")
        a = _build_article("Kumparan", title_el=title_el, link_el=title_el,
            date_el=item.select_one("time, .date"),
            snippet_el=item.select_one("p"))
        if a:
            if a["url"] and not a["url"].startswith("http"):
                a["url"] = "https://kumparan.com" + a["url"]
            articles.append(a)
    logging.info(f"  [Kumparan]    '{query}' -> {len(articles)}")
    return articles


# 8. IDN Times
def scrape_idntimes(query):
    url = f"https://www.idntimes.com/search?q={query.replace(' ', '+')}"
    soup = _fetch(url)
    if not soup: return []
    articles = []
    items = (soup.select("article.article-card") or
             soup.select(".search-result-item") or soup.select("li.article"))
    for item in items[:MAX_PER_QUERY]:
        title_el = item.select_one("h2 a, h3 a, .article-card__title a")
        a = _build_article("IDN Times", title_el=title_el, link_el=title_el,
            date_el=item.select_one("time, .article-card__date"),
            snippet_el=item.select_one("p, .article-card__desc"))
        if a: articles.append(a)
    logging.info(f"  [IDN Times]   '{query}' -> {len(articles)}")
    return articles


# 9. Suara.com
def scrape_suara(query):
    url = f"https://www.suara.com/search?q={query.replace(' ', '+')}"
    soup = _fetch(url)
    if not soup: return []
    articles = []
    items = (soup.select("article.articles--list") or
             soup.select(".search-result-item") or soup.select("ul.content-list li"))
    for item in items[:MAX_PER_QUERY]:
        title_el = item.select_one("h2 a, h3 a, .article__title a, a.title")
        a = _build_article("Suara", title_el=title_el, link_el=title_el,
            date_el=item.select_one("time, .article__time"),
            snippet_el=item.select_one("p, .article__desc"))
        if a: articles.append(a)
    logging.info(f"  [Suara]       '{query}' -> {len(articles)}")
    return articles


# 10. Okezone.com
def scrape_okezone(query):
    url = f"https://search.okezone.com/?q={query.replace(' ', '+')}"
    soup = _fetch(url)
    if not soup: return []
    articles = []
    items = (soup.select("li.search-result-news") or
             soup.select(".news-list li") or soup.select("article"))
    for item in items[:MAX_PER_QUERY]:
        title_el = item.select_one("h4 a, h3 a, h2 a, .search-title a")
        a = _build_article("Okezone", title_el=title_el, link_el=title_el,
            date_el=item.select_one("time, .date, .search-date"),
            snippet_el=item.select_one("p, .search-desc"))
        if a: articles.append(a)
    logging.info(f"  [Okezone]     '{query}' -> {len(articles)}")
    return articles


# Daftar lengkap — tambah scraper baru di sini
ALL_SCRAPERS = [
    scrape_detik,
    scrape_kompas,
    scrape_tribun,
    scrape_liputan6,
    scrape_cnn_indonesia,
    scrape_merdeka,
    scrape_kumparan,
    scrape_idntimes,
    scrape_suara,
    scrape_okezone,
]


def run_all_scrapers():
    """
    Jalankan semua 10 scraper untuk semua query.
    Return: list artikel unik (deduplikasi berdasarkan title).
    """
    all_articles = []
    seen_titles = set()

    for query in SEARCH_QUERIES:
        logging.info(f"=== Query: '{query}' ===")
        for scraper_fn in ALL_SCRAPERS:
            results = scraper_fn(query)
            for article in results:
                title = article.get("title", "").strip()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_articles.append(article)
            time.sleep(DELAY_SECONDS)

    logging.info(f"Total artikel unik dari semua sumber: {len(all_articles)}")
    return all_articles


if __name__ == "__main__":
    # Uji satu sumber: python scraper.py detik
    target = sys.argv[1].lower() if len(sys.argv) > 1 else None

    if target:
        fn_map = {fn.__name__.replace("scrape_", ""): fn for fn in ALL_SCRAPERS}
        matched = [(k, v) for k, v in fn_map.items() if target in k]
        if not matched:
            print(f"Tidak ditemukan. Pilihan: {list(fn_map.keys())}")
        else:
            for name, fn in matched:
                print(f"\n=== Test: {name} ===")
                results = fn(SEARCH_QUERIES[0])
                for i, a in enumerate(results, 1):
                    print(f"  [{i}] [{a['source']}] {a['title'][:65]}")
                    print(f"       URL: {a['url'][:65]}")
    else:
        articles = run_all_scrapers()
        print(f"\n{'='*70}")
        print(f"{'Sumber':<15} {'Judul':<50} {'Tgl'}")
        print(f"{'='*70}")
        for a in articles:
            print(f"{a['source']:<15} {a['title'][:50]:<50} {a.get('published_date','')[:10]}")
        print(f"{'='*70}")
        print(f"Total: {len(articles)} artikel unik dari {len(ALL_SCRAPERS)} sumber")
