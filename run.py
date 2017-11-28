# -*- coding: utf-8 -*-
from utils.config import Config
from crawler import Crawler


if __name__ == '__main__':
    config = Config()
    crawler = Crawler(config)
    articles = crawler.get_articles()
    crawler.save_new_articles(articles)
