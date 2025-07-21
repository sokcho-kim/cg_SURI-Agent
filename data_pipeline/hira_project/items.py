# 메타 데이터 구조 정의 

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class HiraItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    published_date = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    category = scrapy.Field()
    relevant = scrapy.Field()
    attachments = scrapy.Field()  # list of dicts

