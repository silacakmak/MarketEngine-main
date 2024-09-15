import scrapy

class CompanySpider(scrapy.Spider):
    name = "companies"
    start_urls = [
        'https://www.example-directory.com/companies'  # Replace with a company directory
    ]

    def parse(self, response):
        for company in response.css('div.company-listing'):
            yield {
                'name': company.css('h2::text').get(),
                'website': company.css('a::attr(href)').get(),
                'industry': company.css('p.industry::text').get(),
                'location': company.css('span.location::text').get(),
            }
        next_page = response.css('a.next-page::attr(href)').get()
        if next_page is not None:
            yield response.follow(next_page, self.parse)