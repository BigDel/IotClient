from tornado.httpclient import AsyncHTTPClient
import tornado.ioloop
import json

loop = tornado.ioloop.IOLoop.current()
http_client = AsyncHTTPClient()


async def f():
    try:
        response = await http_client.fetch("http://127.0.0.1:8888/GetHb?myPortNo=75000001&dataType=0")
    except Exception as e:
        print("Error: %s" % e)
    else:
        print(response.code)
        sbody = (json.loads(str(response.body, encoding="UTF-8")).get('Msg'))


async def ff(url):
    try:
        response = await http_client.fetch(url)
    except Exception as e:
        print("Error: %s" % e)
    else:
        print(response.code)
        sbody = (json.loads(str(response.body, encoding="UTF-8")).get('Msg'))


def s(i):
    loop.run_sync(lambda: ff(i))


if __name__ == '__main__':
    loop.run_sync(f)
    l = ["http://127.0.0.1:8888/GetHb?myPortNo=75000001&dataType=0",
         "http://127.0.0.1:8888/GetHb?myPortNo=75000001&dataType=0",
         "http://127.0.0.1:8888/GetHb?myPortNo=75000001&dataType=0",
         "http://127.0.0.1:8888/GetHb?myPortNo=75000001&dataType=0"]

    for i in l:
        s(i)
