import scrapy
import re
from urllib.parse import urlparse, urljoin
from pathlib import Path

class CompaniesSpider(scrapy.Spider):
    name = "companies"
    
    start_urls = [
        "https://www.wiki.com.tr/",
        "https://www.sailteknoloji.com/?srsltid=AfmBOorhUnjbf0QXzQvz5GsKzJyUPTGvSj1i2SEhgauQV8eIX_YWX8YM",
    ]

    def __init__(self, *args, **kwargs):
        super(CompaniesSpider, self).__init__(*args, **kwargs)
        self.found_emails = set()  # E-posta adreslerini takip etmek için bir set
        self.visited_urls = set()  # Ziyaret edilen URL'leri takip etmek için bir set
        self.contact_found = False  # İletişim formu veya e-posta bulunup bulunmadığını takip etmek için

    def parse(self, response):
        if response.url in self.visited_urls:
            return  # Daha önce ziyaret edilen URL'yi yeniden işleme
        
        self.visited_urls.add(response.url)  # URL'yi ziyaret edilmiş olarak işaretle

        # Sayfanın HTML içeriğini al
        html_content = response.text
        
        # E-posta adresi bulmak için regex kullan
        email_regex = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        emails = re.findall(email_regex, html_content)

        # Bulunan e-posta adreslerini yazdır
        if emails:
            for email in emails:
                if email not in self.found_emails:
                    self.found_emails.add(email)
                    self.log(f"Bulunan e-posta: {email}")
                    self.check_exit_conditions()  # Çıkış koşullarını kontrol et

        # Sayfanın URL'sine göre dosya adı belirle
        domain = urlparse(response.url).netloc
        filename = f"companies-{domain}.html"
        
        # Sayfanın içeriğini dosyaya yaz
        Path(filename).write_bytes(response.body)
        self.log(f"Saved file {filename}")

        # Sayfanın iletişim sayfası olup olmadığını kontrol et
        url_path = urlparse(response.url).path.lower()
        if 'contact' in url_path or 'iletisim' in url_path or 'contact us' in url_path:
            self.log(f"İletişim sayfası bulunuyor: {response.url}")
            self.parse_contact_page(response)
            self.check_exit_conditions()  # Çıkış koşullarını kontrol et

        # Diğer sayfalara erişmek için bağlantıları takip et, ama yalnızca geçerli sayfaları tarayın
        links = response.css('a::attr(href)').getall()
        for link in links:
            next_page_url = urljoin(response.url, link)
            # Yalnızca geçerli sayfalara git ve ziyaret edilmemiş sayfaları kontrol et
            if self.is_valid_page(next_page_url) and next_page_url not in self.visited_urls:
                yield scrapy.Request(next_page_url, callback=self.parse)

    def parse_contact_page(self, response):
        """
        İletişim sayfasını işleyerek iletişim bilgilerini toplar.
        """
        forms = response.css('form')
        if forms:
            for form in forms:
                action = form.css('::attr(action)').get()
                self.log(f"Form action: {action}")
                form_html = form.get()
                self.log(f"Form HTML: {form_html[:1000]}")  # Uzun HTML içeriğini sınırlı şekilde yazdırmak
                self.contact_found = True
                self.check_exit_conditions()  # Çıkış koşullarını kontrol et
        else:
            self.log("İletişim formu bulunamadı.")

    def check_exit_conditions(self):
        """
        Çıkış koşullarını kontrol eder ve gerekiyorsa tarayıcıyı kapatır.
        """
        if self.found_emails or self.contact_found:
            self.log("Gerekli iletişim bilgileri bulundu. Tarayıcı kapanıyor.")
            self.crawler.engine.close_spider(self, 'Completed')

    def is_valid_page(self, url):
        """
        Geçerli sayfa URL'sini kontrol eder.
        """
        parsed_url = urlparse(url)
        # Sadece başlangıç URL'leriyle aynı alan adlarına sahip sayfaların ziyaret edilmesini sağlar
        return parsed_url.netloc in [urlparse(start_url).netloc for start_url in self.start_urls]
