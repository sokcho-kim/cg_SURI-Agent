# 첨부파일 저장 처리

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
import json
from scrapy.exceptions import DropItem

class JsonWriterPipeline:
    def open_spider(self, spider):
        os.makedirs("results", exist_ok=True)
        self.file = open('results/hira_data.jsonl', 'w', encoding='utf-8')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False)
        self.file.write(line + "\n")
        return item
