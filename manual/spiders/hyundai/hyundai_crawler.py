from urllib.parse import urlparse
import re
import scrapy

from manual.items import Manual


class HyundaiCrawlerSpider(scrapy.Spider):
    name = "hyundai-crawler"
  
    start_urls = ["http://www.hyundai-electronics.de/", "https://www.hyundai-electronics.cz/", "https://www.hyundai-electronics.sk/", "https://www.hyundai-electronics.pl/", "https://www.hyundai-electronics.hu/"]

    def parse(self, response, **kwargs):
        domain = urlparse(response.url).netloc
        # all links
        for link in response.xpath('//a[@href]/@href').extract():
            if "/collections/" in link:
                yield response.follow(response.urljoin(link), callback=self.parse_collections, meta={"domain": domain})

    def parse_collections(self, response, **kwargs):
        # collection links
        for link in response.xpath('//a/@href').extract():
            if "/collections/" in link and "/products/" in link:
                domain = response.meta["domain"]
                yield response.follow(response.urljoin(link), callback=self.parse_item, meta={"domain": domain})

    def parse_item(self, response, **kwargs):
        link = response.url
        if "/" in link:
            product = link.split("/")[-1]
        else:
            product = link
        pattern = r"^(.*)-hyundai-(.*)$"
        match = re.match(pattern, product)
        if match:
            the_product = match.group(1).capitalize()
            brand = "Hyundai"
            if '-' in match.group(2):
                model = match.group(2).split("-")[:-1]
                model = ("-".join(model)).upper()
            else:
                model = ""
            title = response.css('h1.pr_title.mb10:first-of-type')
            text_content = title.css('::text').get()
            regex = r"Hyundai\s+([A-Z0-9]+\s*[A-Z0-9]*\s*[A-Z0-9]*)"
            match_title = re.search(regex, text_content)
            if match_title:
                model = match_title.group(1).strip()
                if len(model) == 1:
                    match_again = re.search(r'[A-Z]+\s\d+', text_content)
                    if match_again:
                        model = match_again.group(1).strip()
        # a is the download link
        for a in response.xpath('//a[contains(@href, "katalog.hponline.cz")]'):
            product = Manual()
            href = a.xpath('./@href').get()
            text = a.xpath('./u/text()').get()
            product["model"] = model
            product["brand"] = brand
            product["product"] = the_product
            product["product_lang"] = response.meta["domain"].split(".")[-1]
            product["file_urls"] = href
            product["type"] = text.split("-")[0].strip()
            product["url"] = response.urljoin(link)

            for img in response.css("img[src*='cdn.shopify.com'][src*='DocumentHandler']"):
                full_link = response.urljoin(img.attrib['src'])
                product["thumb"] = full_link

            product["source"] = response.meta["domain"].split(".")[1] + "." + response.meta["domain"].split(".")[2]

            yield product
        





        







                





