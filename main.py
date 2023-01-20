import csv
import json
import os
import random
import time
from datetime import datetime
import openpyxl
# import parsel
import requests
from fake_useragent import UserAgent
from retrying import retry
from bs4 import BeautifulSoup
import threading
from collections import deque
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re
from tqdm import tqdm
import os.path
import pandas as pd

class WebDriver:
    def __init__(self):
        self.headers = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36 Edg/95.0.1020.30'
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument(f'user-agent={self.headers}')
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


class WebSpider:
    def __init__(self):
        self.headers = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36 Edg/95.0.1020.30'
        # self.headers = {'User-Agent': UserAgent().random}
        self.search_url_page = 'https://www.worshiptogether.com/search-results/#?cludoquery=Songs&cludoCategory=Songs&cludoinputtype=standard&cludopage='
        self.song_urls = deque()
        self.song_url_file_path = 'song_urls_list.json'
        self.lyrics = []
        self.themes = []
        self.titles = []
        self.references = []
        self.urls = []

    def get_song_from_page(self, page_url):
        response = self.get_response(page_url)
        # time.sleep(3 + random.random())
        # response = self.get_response(page_url)
        soup = self.getSoup(response)
        # print(soup.prettify())
        items = soup.find_all("li", class_="search-results-item")
        for item in items:
            self.song_urls.append(item.find_all('a')[0].attrs['href'])

    def get_song_lists(self, start, end):
        # 297 pages on Dec. 13th, 2022
        song_pages_urls = [self.search_url_page + str(i) for i in range(start, end + 1)]
        # counter = 0
        threads = []
        for url in tqdm(song_pages_urls):
            # counter += 1
            # print(counter)
            self.get_song_from_page(url)
            # threads.append(
            #     threading.Thread(target=self.get_song_from_page, args=(url,))
            # )

        # for thread in threads:
        #     thread.start()

        # for thread in threads:
        #     thread.join()

    @retry(stop_max_attempt_number=3)
    def get_response(self, url):
        """
        :param url:
        :return:
        """
        driver = WebDriver()
        driver.driver.get(url)
        driver.driver.implicitly_wait(3)
        # driver.driver.refresh()
        response = driver.driver.page_source
        driver.driver.close()
        # response = requests.get(url, headers=self.headers1)
        # response.encoding = response.apparent_encoding
        return response

    def getSoup(self, resp):
        soup = BeautifulSoup(resp, 'html.parser')
        return soup

    def get_lyric_quote(self, song_url):
        """
        :param song_url:
        :return:
        """
        response = self.get_response(song_url)
        # time.sleep(3 + random.random())
        soup = self.getSoup(response)
        # print(soup.prettify())
        try:
            items = soup.find_all("div", class_="chord-pro-lyric")
            lyric = ' '.join(item.text for item in items)
            lyric = re.sub(r'\s+', ' ', lyric)
        except:
            lyric = None
        try:
            title = soup.find_all("h2", class_="t-song-details__marquee__headline")[0].text
        except:
            title = None
        try:
            references = soup.find_all("a", class_="rtBibleRef")
            reference = [r.attrs['data-reference'] for r in references]
        except:
            reference = []
        try:
            themes = soup.find_all("div", class_="song_taxonomy")[0].find_all("div")[1].find_all("a")
            theme = [t.text for t in themes]
        except:
            theme = []
        return lyric, reference, title, theme, song_url

    def get_songs_info(self, num):
        """
        :param url:
        :return:
        """
        if os.path.exists(self.song_url_file_path):
            with open("song_urls_list.json", "r") as outfile:
                json_object = outfile.read()
            self.song_urls = json.loads(json_object)['song_url']
        else:
            self.get_song_lists(1, 297)
            song_urls_list = {
                "song_url": list(self.song_urls)
            }
            # Serializing json
            json_object = json.dumps(song_urls_list, indent=4)
            # Writing to sample.json
            with open("song_urls_list.json", "w") as outfile:
                outfile.write(json_object)

        for i in tqdm(range(num)):
            lyric, reference, title, theme, url = self.get_lyric_quote(self.song_urls[i])
            self.lyrics.append(lyric)
            self.themes.append(theme)
            self.references.append(reference)
            self.titles.append(title)
            self.urls.append(url)
        d = {'title': self.titles, 'lyric': self.lyrics, 'themes': self.themes, 'reference': self.references, 'url': self.urls}
        self.songs = pd.DataFrame(data=d)
        self.songs.to_csv('song1.csv', index=False)


if __name__ == '__main__':
    ws = WebSpider()
    # chrome_options = Options()
    # chrome_options.add_argument("--headless")
    # browser_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36 Edg/95.0.1020.30'
    #
    # chrome_options.add_argument(f'user-agent={browser_agent}')
    # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    # driver.get('https://www.worshiptogether.com/songs/10-000-reasons-bless-the-lord#SongLyrics')
    # print(driver.page_source)
    # print(ws.get_lyric_quote('https://www.worshiptogether.com/songs/10-000-reasons-bless-the-lord#SongLyrics'))
    # driver.get(
    #     'https://www.worshiptogether.com/search-results/#?cludoquery=Songs&cludoCategory=Songs&cludoinputtype=standard&cludopage=5')
    # # driver.implicitly_wait(3)
    # # driver = webdriver.Chrome('chromedriver.exe', options=options)
    # # # print(driver.get('https://www.worshiptogether.com/search-results/#?cludoquery=Songs&cludoCategory=Songs&cludoinputtype=standard&cludopage=5'))
    # print(ws.song_urls)
    # print(len(ws.song_urls))
    ws.get_songs_info(2949)
    print(ws.songs)



