import base64
import binascii
import json
import math
import random
import re
import time
from datetime import datetime
from urllib.parse import quote
from urllib.parse import urlencode

import pymysql
import requests
import rsa
from config import *
from lxml import etree


class Weibo(object):
    requests.packages.urllib3.disable_warnings()

    # 类初始化
    def __init__(self, username, password):
        super(Weibo, self).__init__()
        self.db = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, port=MYSQL_PORT,
                                  db=MYSQL_DATABASE)
        self.cursor = self.db.cursor()
        try:
            self.db.ping(reconnect=True)
            self.cursor.execute(CREATE_TABLE)
            self.db.commit()
        except:
            print('Table {table} already exists!'.format(table=CREATE_TABLE))

        self.s = requests.Session()
        self.username = username
        self.password = password
        self.servertime = None
        self.pcid = None
        self.nonce = None
        self.pubkey = None
        self.rsakv = None
        self.userid = None
        self.userid = None
        self.base_url = 'https://s.weibo.com/weibo/' + quote('苏宁') + '?'

    # 返回一个随机的请求头 headers
    def get_headers(self):
        user_agent_list = [
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163 Safari/535.1',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'
        ]
        UserAgent = random.choice(user_agent_list)
        headers = {'User-Agent': UserAgent}
        return headers

    # 用户名加密
    def user_encrypt(self):
        user = quote(self.username)
        user = base64.b64encode(user.encode())
        return str(user, encoding='utf-8')

    def prelogin(self):
        params = {
            'entry': 'weibo',
            'callback': 'sinaSSOController.preloginCallBack',
            'su': self.user_encrypt(),
            'rsakt': 'mod',
            'checkpin': 1,
            'client': 'ssologin.js(v1.4.19)',
            '_': str(int(time.time()) * 1000)
        }

        try:
            url = 'https://login.sina.com.cn/sso/prelogin.php?' + urlencode(params)
            response = self.s.get(url=url, headers=self.get_headers(), verify=False)
            if response.status_code == 200:
                resp = response.text
                begPos = resp.find('{')
                endPos = resp.find('}')
                resp = resp[begPos:endPos + 1]
                resp = json.loads(resp)
                self.pcid = resp['pcid']
                self.servertime = resp['servertime']
                self.nonce = resp['nonce']
                self.pubkey = resp['pubkey']
                self.rsakv = resp['rsakv']
        except requests.exceptions.ConnectionError as e:
            print(e.args)

    def get_qrcode(self):
        # 输入生成的验证码
        params = {
            'r': math.floor(random.random() * math.pow(10, 8)),
            's': 0,
            'p': self.pcid
        }
        url = 'https://login.sina.com.cn/cgi/pin.php?'
        print(url + urlencode(params))
        resp = self.s.get(url=url, headers=self.get_headers(), params=params, verify=False)
        with open('qrcode.png', 'wb') as fp:
            fp.write(resp.content)
        qrcode = input('>>>')
        return qrcode

    # 对密码加密
    def encry_password(self):
        rsaPublickey = int(self.pubkey, 16)
        key = rsa.PublicKey(rsaPublickey, 65537)  # 创建公钥
        message = str(self.servertime) + '\t' + str(self.nonce) + '\n' + str(self.password)  # 拼接明文js加密文件中得到
        message = bytes(message, encoding="utf-8")
        passwd = rsa.encrypt(message, key)  # 加密
        passwd = binascii.b2a_hex(passwd)  # 将加密信息转换为16进制。
        return passwd

    def get_replace_url(self, response):
        if response:
            pattern = re.compile('.*location.replace\(\"(.*?)\"\).*')
            result = re.search(pattern, response)
            return result.group(1)

    def get_ticket_url(self, response):
        if response:
            pattern = re.compile('.*location.replace\(\'(.*?)\'\).*')
            result = re.search(pattern, response)
            return result.group(1)

    def get_response(self, url):
        try:
            response = self.s.get(url=url, headers=self.get_headers(), verify=False)
            if response.status_code == 200 or response.status_code == 302:
                print(requests.utils.dict_from_cookiejar(response.cookies))
                return response.text
            return None
        except Exception as e:
            print(e.args)
            return None

    def get_redirect(self, response):
        if response:
            pattern = re.compile('\"uniqueid\":\"(\d+)\".*')
            result = re.search(pattern, response)
            url = r'https://weibo.com/u/' + result.group(1) + "/home"
            return url

    def get_userid(self, response):
        if response:
            beg_pos = response.find("$CONFIG['uid']")
            if beg_pos != -1:
                beg_pos += len("$CONFIG['uid']='")
            end_pos = response.find("$CONFIG['nick']")
            result = response[beg_pos:(end_pos - 2)]

    def login(self):
        url = 'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.19)'
        self.prelogin()
        door = self.get_qrcode()
        params = {
            'entry': 'weibo',
            'gateway': 1,
            'from': '',
            'savestate': 7,
            'qrcode_flag': False,
            'useticket': 1,
            'pagerefer': 'https://passport.weibo.com/visitor/visitor?entry=miniblog&a=enter&url=https%3A%2F%2Fweibo.com%2F&domain=.weibo.com&ua=php-sso_sdk_client-0.6.28&_rand=1566560955.9263',
            'pcid': self.pcid,
            'door': door,
            'vsnf': 1,
            'su': self.user_encrypt(),
            'service': 'miniblog',
            'servertime': self.servertime,
            'nonce': self.nonce,
            'pwencode': 'rsa2',
            'rsakv': self.rsakv,
            'sp': self.encry_password(),
            'encoding': 'UTF-8',
            'prelt': random.randint(100, 500),
            'url': 'https://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
            'returntype': 'META'
        }

        try:
            response = self.s.post(url=url, headers=self.get_headers(), params=urlencode(params), verify=False)
            if response.status_code == 200:
                replace_url = self.get_replace_url(response.text)
                ticke_response = self.get_response(replace_url)
                ticket_url = self.get_ticket_url(ticke_response)
                redirect_response = self.get_response(ticket_url)
                redirect_url = self.get_redirect(redirect_response)
                result_response = self.get_response(redirect_url)
                self.get_userid(result_response)
                return True
        except Exception as e:
            print(e.args)
        return False

    def get_page(self, offset):
        params = {
            'topnav': '1',
            'wvr': '6',
            'b': '1',
            'page': str(offset)
        }
        try:
            print('Crawling: ', self.base_url + urlencode(params))
            response = self.s.get(self.base_url, headers=self.get_headers(), params=urlencode(params), verify=False)
            if response.status_code == 200:
                return response.text
            return None
        except Exception as e:
            print(e.args)
            return None

    def parse_page(self, resposne):
        try:
            if resposne:
                html = etree.HTML(resposne)
                items = html.xpath(
                    '//div[@id="pl_feed_main"]/div[@class="m-wrap"]/div[@id="pl_feedlist_index"]/div[1]/div[@class="card-wrap"]')
                for item in items:
                    try:
                        part_url = item.xpath(
                            './div[@class="card"]/div[@class="card-feed"]/div[@class="content"]/p[@class="from"]/a[1]/@href')[
                            0]
                        result = {}
                        result['mid'] = item.xpath('./@mid')[0]
                        result['url'] = 'https:' + part_url
                        user_id = \
                        item.xpath('./div[@class="card"]/div[@class="card-feed"]/div[@class="avator"]/a/@href')[0]
                        user_id = user_id.split('/')[-1]
                        result['id'] = user_id.split('?')[0]
                        result['title'] = ''.join(item.xpath(
                            './div[@class="card"]/div[@class="card-feed"]/div[@class="content"]/p[last() -1]/text()'))
                        yield result
                    except:
                        yield {}
        except Exception as e:
            print(e.args)
            yield {}

    def get_params(self, result: dict):
        try:
            url = 'https://m.weibo.cn/api/comments/show?id={id}'.format(id=result['mid'])
            response = self.s.get(url=url, headers=self.get_headers(), verify=False)
            if response.status_code == 200:
                data = response.json()
                d = data.get('data', None)
                result['comment_url'] = None
                if d:
                    max = d.get('max', None)
                    for page in range(1, max + 1):
                        result['comment_url'] = 'https://m.weibo.cn/api/comments/show?id={id}&page={page}'.format(
                            id=result['mid'], page=page)
                        yield result
                else:
                    yield result
        except:
            yield {}

    def get_comments(self, result: dict):
        time.sleep(random.random() * 2)
        if result:
            data = {}
            data['url'] = result['url']
            data['keyword'] = KEYWORD
            data['id'] = result['id']
            data['title'] = result['title']
            data['crawl_date'] = datetime.now().strftime('%Y-%m-%d')
            try:
                data['comment'] = ''
                if result['comment_url'] is None:
                    yield data
                else:
                    response = self.s.get(url=result['comment_url'],
                                          headers=self.get_headers(), verify=False)
                    if response.status_code == 200:
                        try:
                            json_data = response.json()
                            json_data = json_data.get('data', None)
                            if json_data is None:
                                yield data
                            else:
                                json_data = json_data.get('data', None)
                                for item in json_data:
                                    data['id'] = item['user']['id']
                                    data['comment'] = item['text']
                                    yield data
                        except:
                            yield data
            except requests.RequestException as e:
                print(e.args)
                yield {}

    # 保存到mysql
    def save_to_mysql(self, item):
        data = dict(item)
        keys = ', '.join(data.keys())
        values = ', '.join(['%s'] * len(data))
        sql = 'INSERT INTO {table}({keys}) VALUES ({values}) ON DUPLICATE KEY UPDATE'.format(table=MYSQL_TABLE,
                                                                                             keys=keys,
                                                                                             values=values)
        update = ','.join([" {key} = %s".format(key=key) for key in data])
        sql += update
        try:
            if self.cursor.execute(sql, tuple(data.values()) * 2):
                self.db.commit()
                print(data)
        except pymysql.MySQLError as e:
            print(e.args)
            self.db.rollback()

    # 调度函数
    def main(self):
        for offset in range(BEGIN_OFFSET, END_OFFSET + 1):
            time.sleep(random.random() * 2)
            for item in self.parse_page(self.get_page(offset)):
                for item2 in self.get_params(dict(item)):
                    for item3 in self.get_comments(dict(item2)):
                        self.save_to_mysql(item3)


if __name__ == '__main__':
    wb = Weibo('andrew_wf@sina.cn', 'WF#zero034439')
    login_result = wb.login()
    # if login_result:
    #     wb.main()
