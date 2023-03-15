from urllib.parse import urlparse
import re
import scrapy

from manual_scraper_ext.items import Manual


class HyundaiCrawlerSpider(scrapy.Spider):
    name = "hyundai-crawler.de"

    start_urls = ["http://www.hyundai-electronics.de/", "https://www.hyundai-electronics.cz/",
                  "https://www.hyundai-electronics.sk/", "https://www.hyundai-electronics.pl/", "https://www.hyundai-electronics.hu/"]

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
        model_2 = ""
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
                    match_2 = re.search(
                        r"hyundai-(\w+)-(\w+)-(\w+)", product)
                    if match_2:
                        # Two words after "Hyundai"
                        the_product = ' '.join(
                            [match.group(1), match.group(2)]).upper()
                        model = match.group(2).upper()
                model, model_2 = self.clean_model(model, response)
            else:
                model = product.split("-")[1].capitalize() + " " + product.split("-")[2].capitalize(
                ) if len(product.split("-")) > 3 else product.split("-")[1].capitalize()
                the_product = product.split("-")[3].capitalize() if len(
                    product.split("-")) > 3 else product.split("-")[1].capitalize()
        except Exception as e:
            self.logger.error(f"Error occurred while matching regex: {e}")

        # a is the download link
        for a in response.xpath('//a[contains(@href, "katalog.hponline.cz")]'):
            product = Manual()
            href = a.xpath('./@href').get()
            text = a.xpath('./u/text()').get()
            the_type = self.clean_type(text.split("-")[0].strip())
            if "Gebrauchsanweisung" in the_type or "Návod k použití" in the_type or "Instrukcja obsługi" in the_type or "Használati utasítás" in the_type:
                product["model"] = model
                product["model_2"] = model_2
                product["brand"] = brand
                product["product"] = the_product.replace("-", " ")
                product["product_lang"] = response.meta["domain"].split(
                    ".")[-1]
                product["file_urls"] = [href]
                product["type"] = the_type
                product["url"] = response.urljoin(link)

                for img in response.css("img[src*='cdn.shopify.com'][src*='DocumentHandler']"):
                    full_link = response.urljoin(img.attrib['src'])
                    product["thumb"] = full_link

                product["source"] = response.meta["domain"].split(
                    ".")[1] + "." + response.meta["domain"].split(".")[2]

                yield product

    def clean_model(self, model, response):
        title = response.css('h1.pr_title.mb10:first-of-type')
        text_content = title.css('::text').get()
        regex = r"Hyundai\s+([A-Z0-9]+\s*[A-Z0-9]*\s*[A-Z0-9]*)"
        model_2 = ""

        match_title = re.search(regex, text_content)
        if match_title:
            model = match_title.group(1).strip()
            if len(model) < 5:
                if "SENZOR" in model:
                    match_again = re.search(
                        r"Hyundai\s+(\w+\s+\w+\s+\w+)", text_content)
                else:
                    match_again = re.search(r'\bHyundai\s+(\S+)', text_content)
                if match_again:
                    model = match_again.group(1).strip()
        if 'Retro' in text_content:
            model_2 = text_content.split(
            )[2] + " " + text_content.split()[3] + " " + text_content.split()[4]
        return model.replace("SENZOR", " ").strip(), model_2.replace("Hyundai", "").strip() if len(model_2) > 0 else model_2

    def clean_type(self, the_type):
        langs = ["ENG", "CZ", "SK", "PL", "HU", "DE", "(CE)"]
        string = the_type
        for lang in langs:
            string = string.replace(lang, "")
        return string.strip()
