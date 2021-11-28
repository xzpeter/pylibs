#!/usr/bin/python3

import urllib, urllib.request
import json

from html.parser import HTMLParser

class HTMLBaseParser(HTMLParser):
    def feed_url(self, url):
        html = urllib.request.urlopen(url).read().decode('utf-8')
        self.feed(html)

class HTMLArticleParser(HTMLBaseParser):
    data = ""
    def handle_data(self, data):
        self.data += data

    def should_skip(self, line):
        skip = [
            "您可以在百度里搜索“我的老千江湖 小说酷笔记(www.kubiji.net)",
            "ydtj() 最新章节全文阅读txt下载",
        ]
        if not line:
            return True
        for item in skip:
            if line.find(item) >= 0:
                return True
        return False

    def parse_article(self, url):
        self.data = ""
        self.reset()
        self.feed_url(url)
        stage = None
        title = body = ""
        # there is one line AD in the body
        ad_skipped = False
        array = self.data.split("\n")
        start_delimiter = "紧急情况：kubiji.org 被强打不开了，请大家收藏新域名 m.kubiji.net"
        end_delimiter = "我的老千江湖全文阅读地址：https://www.kubiji.net/148918/"
        for data in array:
            if not stage:
                if data.find(start_delimiter) >= 0:
                    stage = "title"
            elif stage == "title":
                title = data.strip().replace("作者：黑色枷锁", "")
                stage = "body"
            elif stage == "body":
                data = data.replace("我的老千江湖最新章节地址：", "")
                data = data.replace("https://www.kubiji.net/148918.html", "")
                data = data.strip()

                if self.should_skip(data):
                    continue

                if data.find(end_delimiter) >= 0:
                    # All done
                    break
                else:
                    if not ad_skipped:
                        ad_skipped = True
                        continue
                    body += data + "\n"
        return {
            "title": title,
            "body": "".join(body),
        }

class HTMLDirParser(HTMLBaseParser):
    is_a = False
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.is_a = True
            for attr in attrs:
                if attr[0] == "href":
                    self.href = attr[1]
    def handle_data(self, data):
        if self.is_a:
            print("A_DATA: %s [%s]" % (data, self.href))
    def handle_endtag(self, tag):
        if tag == "a":
            self.is_a = False
    def parse_dir(self, url):
        self.reset()
        self.feed_url(url)

article_parser = HTMLArticleParser()
dir_parser = HTMLDirParser()

def do_parse_entry(url):
    parser = article_parser
    return parser.parse_article(url)

def do_parse_dir(url):
    parser = dir_parser
    return parser.parse_dir(url)

# I used something like this to parse laoqianjianghu.dir, with some editing
# dir_url = 'https://www.kubiji.net/148918_2/'
# print(do_parse_dir(dir_url))

dirfile = "laoqianjianghu.dir"
data = open(dirfile, "r").read().split("\n")
data = list(map(lambda x: x.split(","), data))
# filter out some empty entries
data = filter(lambda x: x and len(x) > 1, data)
outfd = open("laoqianjianghu.txt", "w")

for entry in data:
    title = entry[0]
    url = entry[1]
    out = do_parse_entry(url)
    if title != out["title"]:
        print("Title mismatch: %s vs %s" % (title, out["title"]))
        exit(0)
    outdata = "%s\n\n%s\n\n" % (title, out["body"])
    outfd.write(outdata)
    print("Chapter written: %s" % title)
    
