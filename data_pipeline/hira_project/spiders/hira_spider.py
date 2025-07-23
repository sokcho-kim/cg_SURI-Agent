import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.pipelines.files import FilesPipeline
from urllib.parse import urlencode, quote, urlparse
import re
import os
import mimetypes

class CustomFilesPipeline(FilesPipeline):
    def get_media_requests(self, item, info):
        for f in item.get("file_urls", []):
            if isinstance(f, dict):
                url = f["url"]
                fnm = f.get("fnm", "")
                referer = f.get("referer", "")
            else:
                url = f
                fnm = ""
                referer = ""
            yield scrapy.Request(
                url,
                meta={"item": item, "fnm": fnm},
                headers={"Referer": referer},
            )

    def file_path(self, request, response=None, info=None, **kwargs):
        item = request.meta['item']
        fnm = request.meta.get("fnm", "")
        ext = os.path.splitext(fnm)[1]
        
        if not ext:
            ctype = response.headers.get(b"Content-Type", b"").decode()
            ext = mimetypes.guess_extension(ctype.split(";")[0].strip()) or ".bin"
            
        pub   = item.get('published_date', '')
        cat   = item.get('category', '').strip().replace(' ', '_')
        title = item.get('title', '')[:30].strip().replace(' ', '_')
        filename = f"{cat}/{pub}_{cat}_{title}{ext}"
        return filename

    def item_completed(self, results, item, info):
        item.pop('files', None)
        return item


class HiraSpider(scrapy.Spider):
    name = "hira"
    BASE_LIST_URL = "https://www.hira.or.kr/rc/insu/insuadtcrtr/InsuAdtCrtrList.do?pgmid=HIRAA030069000400"
    BASE_DETAIL_URL = "https://www.hira.or.kr/rc/insu/insuadtcrtr/InsuAdtCrtrPopup.do"
    TAB_MAP = {
        # "01": "고시",
        "02": "행정해석",
        "09": "심사지침",
        "10": "심의사례공개",
        "17": "심사사례지침"
    }
    custom_settings = {
        "FEEDS": {
            "output/hira_datas.json": {
                "format": "json",
                "encoding": "utf8",
                "indent": 2,
            },
        },
        "ITEM_PIPELINES": {
            "__main__.CustomFilesPipeline": 1,
        },
        "FILES_STORE": "files",
        "CONCURRENT_REQUESTS": 8,
        "DOWNLOAD_DELAY": 0.1,
    }
    
    def start_requests(self):
        for tab_code, cat_name in self.TAB_MAP.items():
            params = {
                "tabGbn": tab_code,
                "pageIndex": "1",
            }
            yield scrapy.FormRequest(
                url=self.BASE_LIST_URL + "?pgmid=HIRAA030069000400",
                formdata=params,
                callback=self.parse_list,
                meta={"page": 1, "tab": tab_code},
                headers={
                    "Referer": self.BASE_LIST_URL + "?pgmid=HIRAA030069000400",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            )
        
    
    def parse_list(self, response):
        page = response.meta["page"]
        tab_code = response.meta["tab"]
        
        links = response.css("a[onclick*='viewInsuAdtCrtr']")
        self.logger.info(f"[Tab {tab_code}] Page {page} → {len(links)} items")
        
        for a in links:
            onclick = a.attrib["onclick"]
            m = re.search(r"viewInsuAdtCrtr\(([^)]*)\)", onclick)
            if not m:
                continue
            args = [a.strip().strip("'") for a in m.group(1).split(",")]
            params = {
                "mtgHmeDd":     args[1],
                "sno":          args[2],
                "mtgMtrRegSno": args[3],
            }
            detail_url = f"{self.BASE_DETAIL_URL}?{urlencode(params)}"
            
            yield scrapy.Request(
                detail_url,
                callback=self.parse_detail,
                meta={"published_date": args[1]}
            )
            
        for onclick in response.css('a[onclick^="goPage"]::attr(onclick)').getall():
            m = re.search(r"goPage\((\d+)\)", onclick)
            if not m:
                continue
            nxt = int(m.group(1))
            if nxt == page:
                continue
            params = {
                "tabGbn": tab_code,
                "pageIndex": str(nxt),
            }
            yield scrapy.FormRequest(
                url=self.BASE_LIST_URL + "?pgmid=HIRAA030069000400",
                formdata=params,
                callback=self.parse_list,
                meta={"page": nxt, "tab": tab_code},
                headers={
                    "Referer": self.BASE_LIST_URL + "?pgmid=HIRAA030069000400",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            )
            
    def parse_detail(self, response):
        self.logger.info(f"DETAIL HIT: {response.url}")
        published_date = response.meta["published_date"]
        # published_date = response.url.split("mtgHmeDd=")[1].split("&")[0]
        title = response.css("div.title::text").get(default="").strip()
        content = "\n".join(
            [t.strip() for t in response.css("div.view ::text").getall() if t.strip()]
        )
        category = response.xpath(
            'normalize-space(//*[@id="c"]/div/div[2]/ul/li[1]/span/following-sibling::text()[1])'
        ).get(default="")
        relevant = response.xpath(
            'normalize-space(//*[@id="c"]/div/div[2]/ul/li[2]/span/following-sibling::text()[1])'
        ).get(default="")
        
        file_urls = []
        for a in response.css('a.btn_file[onclick*="Header.goDown1"]'):
            m = re.search(r"Header\.goDown1\('([^']+)'\s*,\s*'([^']+)'\)", a.attrib["onclick"])
            if not m:
                continue
            rel_src, fnm = m.groups()
            dl_url = "https://www.hira.or.kr/download.do?" + urlencode({"src": rel_src, "fnm": fnm})
            download_url = (
                "https://www.hira.or.kr/download.do?"
                + urlencode({"src": dl_url, "fnm": fnm})
            )
            file_urls.append({
                "url": download_url,
                "fnm": fnm,
                "referer": response.url,
            })
            
        self.logger.info(f"ATTACH URLS: {file_urls}")    
        yield {
            "published_date" :  published_date,
            "title":            title,
            "category":         category,
            "relevant":         relevant,
            "content":          content,
            "file_urls":        file_urls,
        }
        
if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(HiraSpider)
    process.start()