import re
import logging
from typing import List
import feedparser
import httpx


async def fetch_rss_posts() -> List[dict]:
    hub_targets = [
        {"name": "DevOps", "url": "https://habr.com/ru/rss/hub/devops/all/"},
        {"name": "Python", "url": "https://habr.com/ru/rss/hub/python/all/"},
        {"name": "Хабр_Научпоп", "url": "https://habr.com/ru/rss/flows/popsci/all/"},
        {"name": "Tproger_Юмор", "url": "https://tproger.ru/feed"},
        {"name": "VC_Технологии", "url": "https://vc.ru/rss"},
        # Оставляем только стабильный Dev.to!
        {"name": "DevTo_DevOps", "url": "https://dev.to/feed/tag/devops"},
        {"name": "DevTo_Python", "url": "https://dev.to/feed/tag/python"},
    ]

    parsed_posts = []
    seen_urls = set()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient() as client:
        for target in hub_targets:
            try:
                logging.info(f"Опрос RSS ленты [{target['name']}]: {target['url']}")
                response = await client.get(
                    target["url"], headers=headers, timeout=15.0, follow_redirects=True
                )

                if response.status_code != 200:
                    logging.error(
                        f"Сервер ответил статус-кодом {response.status_code} для {target['url']}"
                    )
                    continue

                feed = feedparser.parse(response.text)

                for entry in feed.entries:
                    link = entry.link

                    if link in seen_urls:
                        continue
                    seen_urls.add(link)

                    raw_summary = entry.get("summary", "")
                    clean_summary = re.sub(r"<[^>]+>", "", raw_summary)
                    clean_summary = re.sub(r"\s+", " ", clean_summary).strip()

                    if len(clean_summary) > 450:
                        clean_summary = clean_summary[:450] + "..."

                    parsed_posts.append(
                        {
                            "title": entry.title,
                            "source_url": link,
                            "summary": clean_summary,
                            "hub_name": target["name"],
                        }
                    )
            except Exception as e:
                logging.error(f"Ошибка при парсинге ленты {target['url']}: {e}")

    return parsed_posts
