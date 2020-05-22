# -*- coding:utf-8 -*-
import codecs
import os
import MySQLdb
import time
import sys
import re
import threading
import math
import socket
import struct
import httplib
import json


reload(sys)
sys.setdefaultencoding('utf-8')


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, sdch",
    "Accept-Language": "zh-CN,zh;q=0.8",
    # "Cache - Control": "no-cache",
    "Connection": "keep-alive"}

def get_tlmb():
    db = MySQLdb.connect("localhost", "root", "123456", "tlmb", charset="utf8")
    cursor = db.cursor()
    sql = "select dwmc,lx,jd,wd,radius from tlmb where jd is not null and wd is not null"
    sql_jw = "select ipsStart,ipsEnd,ipyh from tlmb_jw"
    sql_jn = "select ipsStart,ipsEnd,ipyh FROM tlmb_jn"

    cursor.execute(sql)
    results = list(cursor.fetchall())
    for i in range(len(results)):
        results[i] = list(results[i])
        try:
            results[i][2] = float(results[i][2])
        except:
            pass
    sort_re = sorted(results, key=lambda x: x[2])
    cursor.execute(sql_jw)
    results_jw = list(cursor.fetchall())
    cursor.execute(sql_jn)
    results_jn = list(cursor.fetchall())
    return sort_re, results_jw,results_jn

tlmb, tlmb_jw, tlmb_jn = get_tlmb()
class ipLocationInfo:
    ip = ''
    lng = -1
    lat = -1
    radius = -1
    contry = '*'
    prov = '*'
    city = '*'

    district = '*'
    accu = '*'
    scene = '*'
    owner = '*'
    EARTH_RADIUS = 6378.137

    def toString(self):

        string = ''
        string += self.ip
        string += '\t' + unicode(self.lng)
        string += '\t' + unicode(self.lat)
        string += '\t' + unicode(self.radius)

        if u"中国" not in self.contry or u"香港" in self.prov or u"澳门" in self.prov or u"台湾" in self.prov:
            company = self.search_foreign_company(self.ip)
            if u"香港" in self.prov:
                self.contry = u"香港"
            if u"澳门" in self.prov:
                self.contry = u"澳门"
            if u"台湾" in self.prov:
                self.contry = u"台湾"
        else:
            company = self.search_company(self.ip,self.lng, self.lat,self.radius, tlmb)
        # print self.ip
        # print self.city
        #  print self.prov
        string += '\t' + self.contry

        string += '\t' + self.prov
        string += '\t' + self.city
        string += '\t' + self.district
        string += '\t' + company
        #string += '\t' + company
        string += '\t' + self.accu
        string += '\t' + self.scene
        string += '\t' + self.owner
        return string

    def search_foreign_company(self, ip):
        ips = socket.ntohl(struct.unpack("I", socket.inet_aton(str(ip)))[0])
        for i in tlmb_jw:

            if ips > i[0] and ips < i[1]:
                # print i[2]
                return i[2]
        return "*"

    def rad(self, d):
        return d * math.pi / 180.0

    def get_distance(self, lat1, lng1, lat2, lng2):
        radlat1 = self.rad(lat1)
        radlat2 = self.rad(lat2)
        a = radlat1 - radlat2
        b = self.rad(lng1) - self.rad(lng2)
        s = 2 * math.asin(math.sqrt(
            math.pow(math.sin(a / 2), 2) + math.cos(radlat1) * math.cos(radlat2) * math.pow(math.sin(b / 2), 2)))
        s = s * self.EARTH_RADIUS
        return s

    def binarySearch(self, num, array, len):
        if array[len - 1][2] - array[0][2] <= 0.02:
            return array
        else:
            mid = int(len / 2)
            if array[mid][2] > num and array[mid][2] - num >= 0.01:
                return self.binarySearch(num, array[:mid], mid)
            elif array[mid][2] < num and array[mid][2] - num <= -0.01:
                return self.binarySearch(num, array[mid:len], len - mid)
            else:
                return array

    def search_chinese_company(self, ip):
        ips = socket.ntohl(struct.unpack("I", socket.inet_aton(str(ip)))[0])
        for i in tlmb_jn:
            if ips > i[0] and ips < i[1]:
                # print i[2]
                return i[2]
        return "*"

    def search_company(self, ip, jd, wd, radius, data):

        jd = float(jd)
        wd = float(wd)
        radius = float(radius)
        work_space = self.search_chinese_company(ip)
        if work_space == '*' and radius < 0.5:
            result = self.binarySearch(jd, data, len(data))
            for d in result:
                jd1 = float(d[2])
                wd1 = float(d[3])
                radius1 = float(d[4])
                min_ds = 1000
                ds = self.get_distance(wd1, jd1, wd, jd)
                if ds < radius+radius1 and ds < min_ds:
                    min_ds = ds
                    work_space = d[0]
        return work_space


def analysisJson(js):
    ipLI = ipLocationInfo()
    if js[u'ip']:
        ipLI.ip = js[u'ip']
    if u"data" in js.keys():
        if js[u'data'][u'lng']:
            ipLI.lng = js[u'data'][u'lng']
        if js[u'data'][u'lat']:
            ipLI.lat = js[u'data'][u'lat']
        if js[u'data'][u'radius']:
            ipLI.radius = js[u'data'][u'radius']
        if js[u'data'][u'country']:
            ipLI.contry = js[u'data'][u'country']
        if js[u'data'][u'prov']:
            ipLI.prov = js[u'data'][u'prov']
        if js[u'data'][u'city']:
            ipLI.city = js[u'data'][u'city']
        if js[u'data'][u'district']:
            ipLI.district = js[u'data'][u'district']
        if js[u'data'][u'accuracy']:
            ipLI.accu = js[u'data'][u'accuracy']
        if js[u'data'][u'scene']:
            ipLI.scene = js[u'data'][u'scene']
        if js[u'data'][u'owner']:
            ipLI.owner = js[u'data'][u'owner']
    return ipLI


def isip(ip):
    p = re.compile('((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)')
    if p.match(ip.strip()):
        return  True
    else:
        return False


def getIp2Location(ip_Str, conn):
    conn.request("GET", "http://10.128.131.98:8880/locate?ip=" + ip_Str + "&coordsys=BD09", None, headers)
    res = conn.getresponse()
    json_Str = res.read()
    js = json.loads(json_Str)
    return js

def qcdata(iplist):
    conn = httplib.HTTPConnection('10.128.131.98:8880')
    global thlock
    dict_ip={}
    for ip in iplist:
        #print ip
        str2write = u''
        js = getIp2Location(ip, conn)
        ipli = analysisJson(js)
        str2write += unicode(ipli.toString()) + u'\r\n'
        li1 = str2write.split('\t')
        dict_ip[li1[0]] = li1[8]
    return dict_ip



# 仿照下面
# iplist = ['211.86.157.133','218.58.75.196']    #这是存放需要查询的ip
# dict_ip = qcdata(iplist)                       #这是调用的主函数返回是字典类型

# for ip in dict_ip.keys():
#     print ip + ':' +dict_ip[ip]+'\r\n'

#print dict_ip
