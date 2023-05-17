import scrapy
from scrapy.exceptions import CloseSpider


class ProductsSpider(scrapy.Spider):
    name = "products"
    allowed_domains = ["www.tinydeals.co"]
    start_urls = ["https://www.tinydeals.co/recommended/"]

    # optional
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://www.tinydeals.co',
        'Connection': 'keep-alive',
        'Referer': 'https://www.tinydeals.co/recommended/',
        # 'Cookie': 'tk_or=%22https%3A%2F%2Fwww.google.com%2F%22; tk_r3d=%22https%3A%2F%2Fwww.google.com%2F%22; tk_lr=%22https%3A%2F%2Fwww.google.com%2F%22; PHPSESSID=fnj26lvvu6egj4f9kgma6rk5hr; _ga_KSNDB8SNFZ=GS1.1.1684335201.2.1.1684335208.0.0.0; _ga=GA1.2.374695317.1684263582; _gid=GA1.2.1689830523.1684263582; gist_identified_xzgks4hj=0; gist_id_xzgks4hj=3b130238-8f6c-99f3-104e-e4f41fbb04c2; _fbp=fb.1.1684263584935.42552601; woocommerce_recently_viewed=240428%7C240228; sc_is_visitor_unique=rx12829943.1684335205.7732F19FC3AC4F01C148703460FB09C1.2.2.2.2.2.2.1.1.1; _gat_gtag_UA_186231599_1=1',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    }

    data = {
        'action': 're_filterpost',
        'filterargs[post_type]': 'product',
        'filterargs[posts_per_page]': '50',
        'filterargs[orderby]': '',
        'filterargs[order]': '',
        'filterargs[tax_query][0][0][taxonomy]': 'product_visibility',
        'filterargs[tax_query][0][0][field]': 'name',
        'filterargs[tax_query][0][0][terms]': 'exclude-from-catalog',
        'filterargs[tax_query][0][0][operator]': 'NOT IN',
        'filterargs[tax_query][0][relation]': 'AND',
        'template': 'woogridcompact',
        # 'containerid': 'rh_woogrid_236485417',
        'offset': '0',
        'innerargs[columns]': '6_col',
        'innerargs[woolinktype]': '',
        'innerargs[disable_thumbs]': '',
        'innerargs[gridtype]': 'compact',
        'innerargs[soldout]': '',
        'innerargs[attrelpanel]': '',
        # 'security': '9c1ade18eb',
        'security': 'lul',
    }

    # use this to control the number of items to scrape per request
    product_per_request_count = 50

    paginator = 0

    def parse(self, response):
        # Update the security key used for template calls (the security key is updated each 24 I guess)
        self.data['security'] = response.xpath("//script[@id='rehub-js-extra']/text()").re_first(
            r'"filternonce":"(\w+)"')
        self.data['posts_per_page'] = str(self.product_per_request_count)
        # start from 0
        self.data['offset'] = '0'

        data = self.data

        yield scrapy.FormRequest("https://www.tinydeals.co/wp-admin/admin-ajax.php",
                                 formdata=data,
                                 callback=self.parse_products)

    def parse_products(self, response):

        no_more_products = response.xpath("//span[@class='no_more_posts']")
        if no_more_products:
            raise CloseSpider("no more products to scrape!")

        products = response.xpath("//div[@class='grid_desc_and_btn']")

        for product in products:
            # get the price as a string
            price = "-".join(product.xpath(".//bdi/text()").getall())
            # check if the price is empty and return "Out of stock" if so
            price = price if price else "Out of stock"
            yield {
                "Name": product.xpath(".//h3/a[@href]/text()").get(),
                "Price": price
            }

        if self.paginator < 300:

            self.paginator = int(self.data['offset']) + self.product_per_request_count

            self.data['offset'] = str(self.paginator)

            yield scrapy.FormRequest("https://www.tinydeals.co/wp-admin/admin-ajax.php",
                                     formdata=self.data,
                                     callback=self.parse_products)
