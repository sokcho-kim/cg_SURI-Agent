import scrapy
from scrapy.http import FormRequest


class KoicdSpider(scrapy.Spider):
    name = 'koicd'
    allowed_domains = ['koicd.kr']
    start_urls = ['https://www.koicd.kr/ins/act.do']

    def start_requests(self):
        # 필요한 만큼 페이지 수 조절
        for page in range(1, 6):  # 예: 5페이지만 먼저 테스트
            yield FormRequest(
                url=self.start_urls[0],
                # formdata={'pageIndex': str(page)},
                formdata={
                    'menuCd': 'DOM_000000103001000000',
                    'pageIndex': str(page),
                    'searchWord': '',
                    'searchCondition': '',
                },
                callback=self.parse_list,
                meta={'page': page}
            )

    def parse_list(self, response):
        with open(f"debug_page_{response.meta['page']}.html", "wb") as f:
            f.write(response.body)

        rows = response.css("table.tableList tr")[1:]  # 헤더 제외
        for row in rows:
            tds = row.css("td")
            if len(tds) >= 3:
                수가코드 = tds[0].css("a::text").get(default='').strip()
                act_id = tds[0].css("a::attr(href)").re_first(r"'(ACT\d+)'")
                행위명_한글 = tds[1].css("::text").get(default='').strip()
                행위명_영문 = tds[2].css("::text").get(default='').strip()

                yield FormRequest(
                    url="https://www.koicd.kr/ins/actDtl.do",
                    formdata={"actId": act_id},
                    callback=self.parse_detail,
                    meta={
                        "수가코드": 수가코드,
                        "행위명_한글": 행위명_한글,
                        "행위명_영문": 행위명_영문
                    }
                )

    def parse_detail(self, response):
        def extract(label):
            return response.xpath(
                f"//th[contains(text(), '{label}')]/following-sibling::td[1]/text()"
            ).get(default='').strip()

        yield {
            "수가코드": response.meta["수가코드"],
            "행위명_한글": response.meta["행위명_한글"],
            "행위명_영문": response.meta["행위명_영문"],
            "분류코드": extract("분류코드"),
            "분류단계": extract("분류단계"),
            "산정명": extract("산정명"),
            "수술여부": extract("수술여부"),
            "의원단가": extract("의원단가"),
            "병원급이상단가": extract("병원급이상단가"),
            "치과병의원단가": extract("치과병의원단가"),
            "보건기관단가": extract("보건기관단가")
        }
