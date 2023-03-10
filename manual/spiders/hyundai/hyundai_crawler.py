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
        model = ""
        brand = "Hyundai"
        the_product = ""
        link = response.url
        if "/" in link:
            product = link.split("/")[-1]
        else:
            product = link
        try:
            pattern = r"^(.*)-hyundai-(.*)$"
            match = re.match(pattern, product)
            if match:
                the_product = match.group(1).capitalize()
                if '-' in match.group(2):
                    model = match.group(2).split("-")[:-1]
                    model = ("-".join(model)).upper()
                else:
                    match_2 = re.search(r'Hyundai\s+(\S+\s+\S+)\s+(\S+)\s*', text)
                    if match_2:
                        the_product = match.group(1)  # Two words after "Hyundai"
                        model = match.group(2)
                model = self.clean_model(model, response)  
        except Exception as e:
            self.logger.error(f"Error occurred while matching regex: {e}")

        # a is the download link
        for a in response.xpath('//a[contains(@href, "katalog.hponline.cz")]'):
            product = Manual()
            href = a.xpath('./@href').get()
            text = a.xpath('./u/text()').get()
            
            product["model"] = model
            product["brand"] = brand
            product["product"] = the_product.replace("-", " ")
            product["product_lang"] = response.meta["domain"].split(".")[-1]
            product["file_urls"] = [href]
            product["type"] = self.clean_type(text.split("-")[0].strip())
            product["url"] = response.urljoin(link)

            for img in response.css("img[src*='cdn.shopify.com'][src*='DocumentHandler']"):
                full_link = response.urljoin(img.attrib['src'])
                product["thumb"] = full_link

            product["source"] = response.meta["domain"].split(".")[1] + "." + response.meta["domain"].split(".")[2]

            yield product

    def clean_model(self, model, response):
        title = response.css('h1.pr_title.mb10:first-of-type')
        text_content = title.css('::text').get()
        regex = r"Hyundai\s+([A-Z0-9]+\s*[A-Z0-9]*\s*[A-Z0-9]*)"
      
        match_title = re.search(regex, text_content)
        if match_title:
            model = match_title.group(1).strip()
            if len(model) < 5:
                if "SENZOR" in model:
                    match_again = re.search(r"Hyundai\s+(\w+\s+\w+\s+\w+)", text_content)
                else:
                    match_again = re.search(r'\bHyundai\s+(\S+)', text_content)
                if match_again:
                    model = match_again.group(1).strip()
        return model
     
    def clean_type(self, the_type):
        langs = ["ENG", "CZ", "SK", "PL", "HU", "DE", "(CE)" ]
        string = the_type
        for lang in langs:
            string = string.replace(lang, "")
        return string.strip()






        







                





