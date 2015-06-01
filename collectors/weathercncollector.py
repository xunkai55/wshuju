__author__ = 'badpoet'

import codecs
import json
import requests
from time import sleep
from exception import WrongPage

class WeatherCnCollector(object):

    MAX_TRY = 3

    def __init__(self):
        self.headers = {
            "Host": "d1.weather.com.cn",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "Accept": "*/*",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36",
            "Referer": "http://www.weather.com.cn/weather1d/101010100.shtml",
            "Accept-Encoding": "gzip, deflate, sdch",
            "Accept-Language": "zh-CN,zh;q=0.8,ru;q=0.6,zh-TW;q=0.4,en;q=0.2"
        }
        self.base_url = "http://d1.weather.com.cn/sk_2d/%s.html"
        self.city_tuples = []
        f = codecs.open("resources/city_gib.txt", "r", "utf8")
        for each in f.readlines():
            cid, p, d, s, lat, long = each.strip().split(" ")
            self.city_tuples.append((cid, p, d, s, lat, long))
        f.close()

    def make_url(self, cid):
        return self.base_url % str(cid)

    def make_headers(self, cid):
        return self.headers

    def analyse_html(self, html):
        try:
            return json.loads(html[13:])
        except Exception, e:
            raise WrongPage()

    def fetch_once(self, url, headers, timeout=5):
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            raise WrongPage()
        return self.analyse_html(resp.text)

    def fetch_raw(self, cid):
        return self.fetch_once(self.make_url(cid), self.make_headers(cid))

    def fetch_page(self, cid):
        cnt = 0
        silence = 30
        last_exception = None
        timeout = 2
        while cnt < MAX_TRY:
            try:
                return self.fetch_once(self.make_url(cid), self.make_headers(cid), timeout)
            except requests.Timeout, e:
                cnt += 1
                timeout += 5
                last_exception = e
            except Exception, e:
                print "Are we banned?"
                cnt += 1
                silence += 30
                sleep(silence)
                last_exception = e
        print last_exception

    def fetch_all(self, wrapper = None):
        city_tuples = self.city_tuples
        tot = len(city_tuples)
        cnt = 0
        for cid, p, d, s, lat, long in city_tuples:
            cnt += 1
            sleep(0.5)
            obj = self.fetch_page(cid)
            pr = str(cnt) + "/" + str(tot) + " "
            if obj:
                try:
                    print pr, obj["cityname"].encode("utf8"), obj["time"].encode("utf8")
                    obj["lat"] = lat
                    obj["long"] = long
                    if wrapper:
                        obj["geo_key"] = wrapper.make_gk(lat, long)
                        wrapper.accept(obj)
                        wrapper.log(pr + json.dumps(obj, ensure_ascii=False), type="log")
                except Exception, e:
                    print e
                    print obj
            else:
                print pr, "failed on", cid
                if wrapper:
                    wrapper.log(pr + "failed on " + cid, type="err")


