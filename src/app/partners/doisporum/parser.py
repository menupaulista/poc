from typing import List

from poc.src.app.partners.doisporum.detail_parser import DoisPorUmDetailParser
from poc.src.app.partners.doisporum.list_parser import DoisPorUmListPageParser
from poc.src.models.offer import OfferItem
from poc.src.parsers.base_parser import PageScrapper, ListPageParser, DetailParser
from poc.src.protocols.base import HttpClient
from poc.src.services.detail_scraper import DetailScraper
from poc.src.services.link_collector import LinkCollector


class DoisPorUmScraper(PageScrapper):

    def __init__(self, async_http_client: HttpClient,
                 list_parser: ListPageParser,
                 detail_parser: DetailParser):
        self.async_http_client = async_http_client
        self.list_parser = list_parser
        self.detail_parser = detail_parser

    @staticmethod
    def default(async_http_client: HttpClient) -> 'DoisPorUmScraper':
        return DoisPorUmScraper(
            async_http_client=async_http_client,
            list_parser=DoisPorUmListPageParser(),
            detail_parser=DoisPorUmDetailParser()
        )

    async def collect_detail_urls(self, seed_url: str, max_items: int) -> List[str]:
        link_collector = LinkCollector(http_client=self.async_http_client, list_parser=self.list_parser)
        return await link_collector.collect_links(seed_url=seed_url, max_items=max_items)

    async def fetch_offers(self, detail_urls: List[str], max_concurrency: int = 3) -> List[OfferItem]:
        detail_scraper = DetailScraper(http_client=self.async_http_client,
                                       detail_parser=self.detail_parser,
                                       max_concurrency=max_concurrency
                                       )

        return await detail_scraper.scrape_details(urls=detail_urls)

    # def extract_detail_links(self, html: str) -> List[str]:
    #     return self.list_parser.extract_detail_links(html=html)
    #
    # def extract_pagination_links(self, html: str) -> List[str]:
    #     return self.list_parser.extract_pagination_links(html=html)
    #
    # def parse(self, html: str, url: str) -> Optional[OfferItem]:
    #     return self.detail_parser.parse(html=html, url=url)
