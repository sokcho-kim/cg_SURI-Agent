import scrapy
import re
from urllib.parse import urlencode, quote
from hira_project.items import HiraItem

class HiraSpider(scrapy.Spider):
    name = "hira"

    def start_requests(self):
        for page in range(1, 200):
            data = {
                "pageIndex": str(page),
                "tabGbn": "10",
                "decIteTpCd": "10",
                "searchYn": "Y",
                "recordCountPerPage": "10"
            }
            yield scrapy.FormRequest(
                url="https://www.hira.or.kr/rc/insu/insuadtcrtr/InsuAdtCrtrList.do",
                formdata=data,
                callback=self.parse_list,
                meta={"page": page}
            )

    def parse_list(self, response):
        rows = response.css("div[class*=tb-type01] table tbody tr")
        if not rows:
            self.logger.warning(f"페이지 {response.meta['page']} 비어있음 → 중단")
            return
        for row in rows:
            onclick = row.css("td.col-tit a::attr(onclick)").get()
            m = re.search(r"viewInsuAdtCrtr\([^,]+,\s*'(\d+)'\s*,\s*'(\d+)'\s*,\s*'(\d+)'", onclick or "")
            if not m:
                continue
            mtgHmeDd, sno, mtgMtrRegSno = m.groups()
            popup_url = f"https://www.hira.or.kr/rc/insu/insuadtcrtr/InsuAdtCrtrPopup.do?mtgHmeDd={mtgHmeDd}&sno={sno}&mtgMtrRegSno={mtgMtrRegSno}"

            yield scrapy.Request(
                url=popup_url,
                callback=self.parse_detail,
                meta={
                    "published_date": mtgHmeDd,
                    "title": row.css("td.col-tit a::text").get(default="").strip(),
                    "category": row.css("td.col-gubun::text").get(default="").strip()
                }
            )

    def parse_detail(self, response):
        item = HiraItem()
        item["published_date"] = response.meta["published_date"]
        item["title"] = response.meta["title"]
        item["category"] = response.meta["category"]

        content_el = response.css("div.popup_cont, div.detail_cont, div.cont-area, div#content")
        content = content_el.get().strip() if content_el else ""
        item["content"] = content

        relevant = ""
        for line in content.splitlines():
            if "근거" in line or "관련" in line:
                relevant = line.strip()
                break
        item["relevant"] = relevant

        attachments = []
        for i, a in enumerate(response.css("a.btn_file[onclick*='Header.goDown1']")):
            onclick = a.attrib.get("onclick", "")
            m = re.search(r"Header\.goDown1\('([^']+)'\s*,\s*'([^']+)'\)", onclick)
            if not m:
                continue
            rel_src, fnm = m.groups()
            fnm_enc = quote(fnm, safe='')
            download_url = "https://www.hira.or.kr/download.do?" + urlencode({"src": rel_src, "fnm": fnm_enc})

            ext = fnm.split(".")[-1]
            safe_title = re.sub(r'[\\/:*?"<>|]', '', item["title"]).replace(" ", "").strip()[:30]
            save_name = f"{item['published_date']}_{item['category']}_{safe_title}_{i+1}.{ext}"

            attachments.append({
                "original_name": fnm,
                "download_url": download_url,
                "saved_name": save_name
            })

        item["attachments"] = attachments
        yield item