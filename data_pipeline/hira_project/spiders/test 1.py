import os, re, mimetypes
import scrapy
from urllib.parse import urlencode
from scrapy.crawler import CrawlerProcess
from scrapy.pipelines.files import FilesPipeline

PGMID = "HIRAA030069000400"

class CustomFilesPipeline(FilesPipeline):
    def get_media_requests(self, item, info):
        for f in item.get("file_urls", []):
            # f 는 dict 로 온다고 가정
            url = f["url"]
            fnm = f["fnm"]
            ref = f["referer"]
            yield scrapy.Request(
                url,
                meta={"item": item, "fnm": fnm},
                headers={"Referer": ref},
            )

    def file_path(self, request, response=None, info=None, **kwargs):
        item = request.meta["item"]
        fnm  = request.meta.get("fnm", "")
        ext  = os.path.splitext(fnm)[1]

        if not ext:
            ctype = response.headers.get(b"Content-Type", b"").decode()
            ext = mimetypes.guess_extension(ctype.split(";")[0].strip()) or ".bin"

        def clean(s):
            return re.sub(r'[\\/:*?"<>|]', "_", s)

        pub   = clean(item.get("published_date", ""))
        cat   = clean(item.get("category", "") or "etc")
        title = clean(item.get("title", "")[:30])

        return f"{cat}/{pub}_{cat}_{title}{ext}"

    def item_completed(self, results, item, info):
        item.pop("files", None)
        return item


class HiraSpider(scrapy.Spider):
    name = "hira"

    BASE_LIST_URL   = "https://www.hira.or.kr/rc/insu/insuadtcrtr/InsuAdtCrtrList.do"
    BASE_DETAIL_URL = "https://www.hira.or.kr/rc/insu/insuadtcrtr/InsuAdtCrtrPopup.do"

    TAB_MAP = {
        # "01": "고시",
        "02": "행정해석",
        "09": "심사지침",
        "10": "심의사례공개",
        "17": "심사사례지침",
    }

    custom_settings = {
        "FEEDS": {
            "output/hira_datas.json": {"format": "json", "encoding": "utf8", "indent": 2},
        },
        "ITEM_PIPELINES": {"__main__.CustomFilesPipeline": 1},
        "FILES_STORE": "files",
        "CONCURRENT_REQUESTS": 8,
        "DOWNLOAD_DELAY": 0.1,
        "HTTPERROR_ALLOWED_CODES": [404, 410],
    }

    # def start_requests(self):
    #     for tab_code in self.TAB_MAP:
    #         params = {"pgmid": PGMID, "tabGbn": tab_code, "pageIndex": 1}
    #         url = f"{self.BASE_LIST_URL}?{urlencode(params)}"
    #         yield scrapy.Request(url, callback=self.parse_list,
    #                              meta={"page": 1, "tab": tab_code})
    
    # def start_requests(self):
    #     for tab in self.TAB_MAP:                   # 01,02,09,10,17 …
    #         yield scrapy.FormRequest(
    #             url=self.BASE_LIST_URL,
    #             formdata={
    #                 "pgmid": PGMID,
    #                 "tabGbn": tab,
    #                 "pageIndex": "1",
    #             },
    #             method="POST",
    #             callback=self.parse_list,
    #             meta={"tab": tab, "page": 1, "cookiejar": tab},  # 탭별 세션 분리
    #             dont_filter=True,
    #         )

    # 
    
    def start_requests(self):
        for tab in self.TAB_MAP:
            # 탭 초기화 1차 요청 (goTabMove 흉내)
            yield scrapy.FormRequest(
                url=self.BASE_LIST_URL,
                formdata={
                    "pgmid": PGMID,
                    "tabGbn": tab,
                    "pageIndex": "1",
                    "searchYn": "Y",
                    "seqListYn": "N",
                    "seqList": "",
                    "startDt": "",
                    "endDt": "",
                    "searchWord": "",
                    "selSearchCondition": "TT",  # 전체검색 조건
                },
                method="POST",
                callback=self.parse_list,  # ✅ 바로 parse_list로 연결
                meta={"tab": tab, "page": 1, "cookiejar": tab},
                dont_filter=True,
            )



    def init_tab(self, response):
        # 2) 페이지에 있는 <form name="fm"> 을 찾아
        #    formdata 로 goTabMove(tab) 과 동일하게 제출합니다.
        for tab_code in self.TAB_MAP:
            yield scrapy.FormRequest.from_response(
                response,
                formxpath="//form[@name='fm']",
                formdata={
                    "pgmid":     PGMID,
                    "tabGbn":    tab_code,
                    "pageIndex": "1",
                },
                callback=self.after_tab_set,
                meta={"tab": tab_code, "cookiejar": tab_code},
                dont_filter=True,
            )

    def after_tab_set(self, response):
        # 3) 폼 제출 후 돌아오는 페이지가 탭이 적용된 첫 페이지 목록입니다.
        tab_code = response.meta["tab"]
        page     = 1
        self.logger.info(f"[Tab {tab_code}] Initialized. Parsing page {page}")
        # 이 응답을 바로 parse_list 로 넘겨도 되고, URL GET 으로 다시 호출해도 됩니다:
        yield from self.parse_list(response)






    def parse_list(self, response):
        page     = response.meta["page"]
        tab_code = response.meta["tab"]

        self.logger.warning(f"[탭 {tab_code}] 제목 예시: " + response.css(".board_list tbody tr td a::text").get(default="없음"))

        # 1) 모든 onclick 링크 추출
        onclicks = response.xpath("//a[contains(@onclick,'InsuAdtCrtr')]/@onclick").getall()
        self.logger.info(f"[Tab {tab_code}] Page {page} → onclicks: {len(onclicks)}")

        # 2) 상세 페이지 URL 생성 및 요청
        for oc in onclicks:
            # 따옴표 안의 값들만 뽑아서 date, sno, reg 에 할당
            vals = re.findall(r"'([^']*)'", oc)
            if len(vals) < 3:
                self.logger.warning(f"[Tab {tab_code}] onclick parsing failed: {oc}")
                continue
            date, sno, reg = vals[0], vals[1], vals[2]
            params     = {"mtgHmeDd": date, "sno": sno, "mtgMtrRegSno": reg}
            detail_url = f"{self.BASE_DETAIL_URL}?{urlencode(params)}"
            self.logger.debug(f"[Tab {tab_code}] enqueue DETAIL → {detail_url}")

            yield scrapy.Request(
                detail_url,
                callback=self.parse_detail,
                meta={"published_date": date, "detail_url": detail_url},
                headers={"Referer": response.url},
                dont_filter=True,
                priority=10,   # 상세를 우선 처리
            )

        # 3) 페이징 (goPage)
        for oc in response.css('a[onclick^="goPage"]::attr(onclick)').getall():
            m = re.search(r"goPage\((\d+)\)", oc)
            if not m:
                continue
            nxt = int(m.group(1))
            if nxt == page:
                continue

            params   = {"pgmid": PGMID, "tabGbn": tab_code, "pageIndex": nxt}
            next_url = f"{self.BASE_LIST_URL}?{urlencode(params)}"
            self.logger.debug(f"[Tab {tab_code}] enqueue NEXT → {next_url}")

            yield scrapy.Request(
                next_url,
                callback=self.parse_list,
                meta={"page": nxt, "tab": tab_code},
                headers={"Referer": response.url},
                dont_filter=True,
                priority=0,    # 페이징은 나중에
            )


    def parse_detail(self, response):
        self.logger.debug(f"DETAIL HIT: {response.url}")

        pub_date   = response.meta["published_date"]
        detail_ref = response.meta["detail_url"]

        title = response.css("div.title::text").get(default="").strip()
        content = "\n".join(t.strip() for t in response.css("div.view ::text").getall() if t.strip())

        category = response.xpath(
            'normalize-space(//*[@id="c"]/div/div[2]/ul/li[1]/span/following-sibling::text()[1])'
        ).get(default="").strip()
        relevant = response.xpath(
            'normalize-space(//*[@id="c"]/div/div[2]/ul/li[2]/span/following-sibling::text()[1])'
        ).get(default="").strip()

        file_objs = []
        for oc in response.css('a.btn_file::attr(onclick)').getall():
            m = re.search(r"Header\.goDown1\('([^']+)'\s*,\s*'([^']+)'\)", oc)
            if not m:
                continue
            rel_src, fnm = m.groups()
            dl_url = "https://www.hira.or.kr/download.do?" + urlencode({"src": rel_src, "fnm": fnm})
            file_objs.append({"url": dl_url, "fnm": fnm, "referer": detail_ref})

        self.logger.debug(f"ATTACH URLS: {file_objs}")

        yield {
            "published_date": pub_date,
            "title":          title,
            "category":       category,
            "relevant":       relevant,
            "content":        content,
            "file_urls":      file_objs,
        }


if __name__ == "__main__":
    process = CrawlerProcess()
    process.crawl(HiraSpider)
    process.start()
