#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: Hamdi
from urllib.parse import urlencode

import requests
from requests import Session, ReadTimeout
from pyquery import PyQuery as pq

from config import *
from redis_db import RedisQueue
from request import WeixinRequest
from mysql import MySQL


class Spider(object):
    base_url = 'https://weixin.sogou.com/weixin'
    keyword = '王小波'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Cookie': 'SUV=1562839772371461; SMYUV=1562839772381631; UM_distinctid=16be0826d052a3-09d62a664e15a1-3f71045b-1fa400-16be0826d0a34d; CXID=D68E05F4CE88F967F09E4EFE634A3A76; SUID=9C64B37B3965860A5D2EC3D6000A56F5; usid=fxxmcwoj-HcrKv9N; IPLOC=CN1504; wuid=AAHSMbPTKAAAAAqKFD2zIgEAAAA=; front_screen_resolution=1920*1080; FREQUENCY=1563856028394_2; ABTEST=7|1570086472|v1; weixinIndexVisited=1; sct=1; JSESSIONID=aaaE9yntPs_s-8_Hifp1w; PHPSESSID=ttjcume0gtn4feqsribvr3f4r1; SNUID=1378AE661D188EE1C3A171D61EE50067; ppinf=5|1570158018|1571367618|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZTo1OkhhbWRpfGNydDoxMDoxNTcwMTU4MDE4fHJlZm5pY2s6NTpIYW1kaXx1c2VyaWQ6NDQ6bzl0Mmx1TGtRRlFmblFXNEF6ejBFbUdPVDB3WUB3ZWl4aW4uc29odS5jb218; pprdig=sPO3BwvoD1mY_cO1DIG8_4gSXt8BtnBdEJST-J7MjK--FFHy3-Yqak3U_EaeWWKzT5ZMLFI7Hcg7PmyiFlkmkF0-zrsdyFgtLjaWQO9PpQZF7UoRL7vzaZwHg91P1q4Rd8OhNrg7qQknZcqKiA8T8njxh2aqShqS8OUoB4pdFn4; sgid=08-33565741-AV2WtcJ6dJibiamq3sSpY5GJI; ppmdig=15701580180000002e9b06a7bcf715991a141deb49ce2abc',
        'Host': 'weixin.sogou.com',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
    }
    """
    https://weixin.sogou.com/weixin?query=%E7%8E%8B%E5%B0%8F%E6%B3%A2&s_from=input&type=2&page=3
    """
    session = Session()
    queue = RedisQueue()
    mysql = MySQL()

    def start(self):
        """
        初始化工作
        :return:
        """
        # 全局更新Headers
        self.session.headers.update(self.headers)
        start_url = self.base_url + '?' + urlencode({'query': self.keyword, 'type': 2})
        weixin_request = WeixinRequest(url=start_url, callback=self.parse_index, need_proxy=True)
        # 调度第一个请求
        self.queue.add(weixin_request)

    def parse_index(self, response):
        """
        解析索引页
        :param response:
        :return:
        """
        doc = pq(response.text)
        items = doc('.news-box .news-list li .txt-box h3 a').items()
        for item in items:
            url = item.attr('href')
            weixin_request = WeixinRequest(url=url, callback=self.parse_detail)
            yield weixin_request
        next = doc('#sogou_next').attr('href')
        if next:
            url = self.base_url + str(next)
            weixin_request = WeixinRequest(url=url, callback=self.parse_index, need_proxy=True)
            yield weixin_request

    def parse_detail(self, response):
        """
        解析详情页
        :param response:
        :return:
        """
        doc = pq(response.text)
        data = {
            'title': doc('.rich_media_title').text(),
            'content': doc('.rich_media_content').text(),
            'date': doc('#post-date').text(),
            'nickname': doc('#js_profile_qrcode > div > strong').text(),
            'wechat': doc('#js_profile_qrcode > div > p:nth-child(3) > span').text()
        }
        yield data

    def request(self, weixin_request):
        """
        执行请求
        :param weixin_request: 请求
        :return: 响应
        """
        try:
            if weixin_request.need_proxy:
                proxy = self.get_proxy()
                if proxy:
                    proxies = {
                        'http': 'http://' + proxy,
                        'https': 'https://' + proxy
                    }
                    return self.session.send(weixin_request.prepare(),
                                             timeout=weixin_request.timeout, allow_redirects=False, proxies=proxies)
            return self.session.send(weixin_request.prepare(), timeout=weixin_request.timeout, allow_redirects=False)
        except (ConnectionError, ReadTimeout) as e:
            print(e.args)
            return False

    def get_proxy(self):
        """
        从代理池获取代理
        :return:
        """
        try:
            response = requests.get(PROXY_POOL_URL)
            if response.status_code == 200:
                print('获取代理中:', response.text)
                return response.text
            return None
        except requests.ConnectionError:
            return None

    def error(self, weixin_request):
        """
        错误处理
        :param weixin_request:
        :return:
        """
        weixin_request.fail_time = weixin_request.fail_time + 1
        print('Request Failed', weixin_request.fail_time, '时间:', weixin_request.url)
        if weixin_request.fail_time < MAX_FAILED_TIME:
            self.queue.add(weixin_request)

    def schedule(self):
        """
        调度请求
        :return:
        """
        while not self.queue.empty():
            weixin_request = self.queue.pop()
            callback = weixin_request.callback
            print('正在调度中:', weixin_request.url)
            response = self.request(weixin_request)
            if response and response.status_code in VALID_STATUSES:
                results = list(callback(response))
                if results:
                    for result in results:
                        print('新的请求:', type(result))
                        if isinstance(result, WeixinRequest):
                            self.queue.add(result)
                        if isinstance(result, dict):
                            self.mysql.insert('articles', result)
                else:
                    self.error(weixin_request)
            else:
                self.error(weixin_request)

    def run(self):
        """
        入口
        :return:
        """
        self.start()
        self.schedule()

if __name__ == '__main__':
    spider = Spider()
    spider.run()
