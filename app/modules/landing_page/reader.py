"""
落地页内容提取器
用 httpx 抓取 HTML，用内置 html.parser 提取标题、标题标签、正文，不引入额外依赖
"""
import re
import httpx
from html.parser import HTMLParser

_SKIP_TAGS = {"script", "style", "nav", "footer", "noscript", "iframe", "svg"}
_HEADING_TAGS = {"h1", "h2", "h3"}
_BODY_TAGS = {"p", "li", "td", "th", "span", "div", "section", "article"}


class _Extractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta_description = ""
        self.headings: list[str] = []
        self.body_chunks: list[str] = []
        self._tag_stack: list[str] = []
        self._skip_depth = 0

    def _current(self):
        return self._tag_stack[-1] if self._tag_stack else ""

    def handle_starttag(self, tag, attrs):
        self._tag_stack.append(tag)
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        if tag == "meta":
            d = dict(attrs)
            if d.get("name", "").lower() == "description":
                self.meta_description = d.get("content", "")[:300]

    def handle_endtag(self, tag):
        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()
        if tag in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth > 0:
            return
        text = data.strip()
        if not text:
            return
        tag = self._current()
        if tag == "title":
            self.title = text[:100]
        elif tag in _HEADING_TAGS:
            if text not in self.headings:
                self.headings.append(text)
        elif tag in _BODY_TAGS and len(text) > 25:
            self.body_chunks.append(text)


async def fetch_landing_page(url: str) -> dict:
    """抓取落地页，返回结构化文本内容，总正文不超过 2500 字符"""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; AIAdsBot/1.0)",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
    }
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        html = resp.text

    parser = _Extractor()
    parser.feed(html)

    # 去重并合并正文
    seen = set()
    unique_chunks = []
    for chunk in parser.body_chunks:
        key = re.sub(r"\s+", " ", chunk).lower()[:60]
        if key not in seen:
            seen.add(key)
            unique_chunks.append(chunk)

    body = " ".join(unique_chunks)
    body = re.sub(r"\s+", " ", body).strip()[:2500]

    return {
        "url": url,
        "title": parser.title,
        "meta_description": parser.meta_description,
        "headings": parser.headings[:12],
        "body_text": body,
    }
