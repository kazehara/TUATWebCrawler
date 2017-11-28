# -*- coding: utf-8 -*-
import requests
import re
import sqlite3
from utils.config import Config
from bs4 import BeautifulSoup


class Crawler:

    def __init__(self, config: Config):
        self.articles_request_url = config.get('ARTICLES_REQUEST_URL')
        self.details_request_url = config.get('DETAILS_REQUEST_URL')
        self.conn = sqlite3.connect(config.get('DB_NAME'))
        self.cursor = self.conn.cursor()
        self.existed_article_nums = [num[0] for num in self.cursor.execute('SELECT num FROM articles').fetchall()]
        print(self.existed_article_nums)
        self.soup = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        self.conn.close()

    def init_soup(self, url, params):
        response = requests.get(url, params=params)
        self.soup = BeautifulSoup(response.text, "html5lib")

    def dump_json(self):
        pass

    def save_new_articles(self, new_articles):
        print(len(new_articles['articles']))
        for article in new_articles['articles']:
            sql = """ \
            INSERT INTO articles VALUES(
            {}, {}, \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\'
            )""".format(
                article['important'],
                article['num'],
                article['public_range'],
                article['category'],
                article['title'],
                article['administrator'],
                article['body'],
                article['attach_name'],
                article['attach_url'],
                article['target'],
                article['publisher']
            )
            self.conn.execute(sql)

        self.conn.commit()

    def check_new_article(self, article_num):
        if article_num in self.existed_article_nums:
            return False
        return True

    def delete_old_articles(self, article_nums):
        article_nums_set = set(article_nums)
        existed_nums_set = set(self.existed_article_nums)

        removed_article_nums = existed_nums_set.difference(article_nums_set)

        print('Articles will be removed are {}'.format(removed_article_nums))

        for num in removed_article_nums:
            sql = "DELETE FROM articles WHERE num = {}".format(num)
            self.conn.execute(sql)

        self.conn.commit()

    @staticmethod
    def init_article_dict():
        return {
            'important': None,
            'num': None,
            'public_range': None,
            'category': None,
            'title': None,
            'administrator': None,
            'body': None,
            'attach_name': None,
            'attach_url': None,
            'target': None,
            'publisher': None
        }

    def get_articles(self):
        skip = 0
        articles = {'articles': []}
        article_nums = []

        while True:
            self.init_soup(self.articles_request_url, {'skip': skip})
            raw_articles = self.soup.find_all('tr', class_='row')

            if len(raw_articles) == 0:
                self.delete_old_articles(article_nums)
                return articles

            for article in raw_articles:
                article_dict = self.init_article_dict()

                is_important = False
                if article.find('img', alt='重要'):
                    is_important = True
                article_num = int(article.get('alt'))

                article_nums.append(article_num)

                if not self.check_new_article(article_num):
                    continue

                self.init_soup(self.details_request_url, {'i': str(article_num)})

                article_dict['important'] = 1 if is_important else 0
                article_dict['num'] = article_num

                information = self.soup.find_all('tr')
                for inf in information:
                    try:
                        inf.find('div').decompose()
                    except Exception:
                        pass

                    try:
                        label = inf.find('td', class_='defLabel').text
                    except AttributeError:
                        continue
                    label = re.sub(r'.*\(.*\).*', '', label).strip()

                    if label == '公開期間':
                        article_dict['public_range'] = inf.find_all('td')[1].text.strip()
                    elif label == 'カテゴリー':
                        article_dict['category'] = inf.find_all('td')[1].text.strip()
                    elif label == 'タイトル':
                        article_dict['title'] = inf.find('td', class_='emphasis1').text.strip()
                    elif label == '担当者':
                        article_dict['administrator'] = inf.find_all('td')[1].text.strip()
                    elif label == '本文':
                        article_dict['body'] = inf.find('td', class_='emphasis2').text
                    elif label == '添付ファイル':
                        article_dict['attach_name'] = inf.find_all('td')[1].text.strip()
                        article_dict['attach_url'] = inf.find_all('td')[1].find('a').get('href')
                    elif label[0:2] == '対象':
                        article_dict['target'] = inf.find_all('td')[1].find('span').text
                    elif label == '発信元':
                        article_dict['publisher'] = inf.find_all('td')[1].text.strip()
                    else:
                        pass

                articles['articles'].append(article_dict)

            skip += 20
