#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: Hamdi
import requests

from config import PROXY_POOL_URL


def get_proxy():
    """
    从代理池获取代理
    :return:
    """
    try:
        response = requests.get(PROXY_POOL_URL)
        if response.status_code == 200:
            print('获取代理：', response.text)
            return response.text
        return None
    except requests.ConnectionError:
        return None


proxy = get_proxy()
proxies = {
    'http:': 'http://' + proxy,
    'https:': 'https://' + proxy
}

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


try:
    response = requests.get('https://weixin.sogou.com/weixin?query=王小波&type=2&page=11', proxies=proxies, headers=headers)
    print(response.text)
except requests.exceptions.ConnectionError as e:
    print('我是错误:', e.args)