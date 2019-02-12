#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2018/12/05
del
客户端
"""
import binascii
import json
import sys
import threading
import datetime
import time

import config
import socket
import queue
from concurrent.futures import ThreadPoolExecutor as Pool
from tornado.httpclient import AsyncHTTPClient
from tornado import ioloop

send_que = queue.Queue()  # 发送队列
recv_que = queue.Queue()  # 接收队列
Message_buf = bytes()  # 消息buf
lock = threading.Lock()  # 线程锁
idle_tags = list()  # 空闲标签列表
job_tags = list()  # 工作的标签
online_tags = list()  # 在线的标签
pool = Pool()  # 线程池
loop = ioloop.IOLoop.current()  # 异步tornado机制
http_client = AsyncHTTPClient()  # 初始化AsyncHttpClient
# 计数器c
counter = {
    'send': 0,
    'recv': 0,
    'tghb': 0,
}
# 标记数据
mark = {
    'myalive': False
}


# socket客户端
# noinspection PyTypeChecker
class SocketClient(object):

    # 连接服务器初始化以及其他配置（初始化Socket连接）
    def __init__(self):
        self.message_buf = bytes()  # 初始化消息buf
        self.TCP_SOCKET = socket.socket()  # 初始化Tcp_Socket
        self.SocketConnection = False  # socket连接状态
        self.my_address = (socket.gethostbyname(socket.gethostname()), config.options.get("my_port"))  # 设置本地地址
        self.tcpserver_address = (config.options.get('socket_ip'), config.options.get('socket_port'))  # 设置tcpserver地址
        self.connection_()  # 初始化连接

    # 发送 线程池多线程发送
    def send(self):
        l = []
        try:
            msg = send_que.get()
            obj = pool.submit(self.TCP_SOCKET.send, bytes.fromhex(msg))
            l.append(obj)
            [obj.result() for obj in l]
        except Exception as ex:
            print("发送出错:" + ex.args)
        else:
            print("{}:发送了——{}".format(datetime.datetime.now(), msg))
        threading.Timer(0, self.send).start()

    # 接收分割  单线程
    def recv_(self):
        try:
            if len(self.message_buf) > 0:
                msg = self.message_buf[0:2]
                msg_len = int.from_bytes(msg[1:], byteorder='big', signed=False) + 2
                msg += self.message_buf[2:msg_len]
                self.message_buf = self.message_buf[msg_len:]
                msg = (str(binascii.b2a_hex(msg))[2:-1]).upper()
                # msg = re.sub(r'(?<=\w)(?=(?:\w\w)+$)', " ", msg).upper()
                # msg = msg.upper()
                print("{}接收到——{} :".format(datetime.datetime.now(), msg))
                recv_que.put(msg)
        except Exception as es:
            print('接收发生了异常:' + es.args)
            print(es.args)
        threading.Timer(0, self.recv_).start()

    # 接收
    def recv(self):
        try:
            msg = self.TCP_SOCKET.recv(2048)
            if msg != b'':
                self.message_buf += msg
        except Exception as es:
            print("接收出错:" + es.args)
            print(es.args)
        threading.Timer(0, self.recv).start()

    # 连接
    def connection_(self):
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tcp_socket.bind(self.my_address)
            tcp_socket.connect(self.tcpserver_address)
        except Exception as es:
            print("\033[1;31m%s\033[1m" % "<<<Socket Connection Failed>>")
            print(es.args)
        else:
            self.TCP_SOCKET = tcp_socket
            self.SocketConnection = True
            print("\033[1;32m%s\033[1m" % ">>Socket connection Succeeded<<")


# Http客户端
class HttpClinet(object):

    # 连接服务器初始化（往服务器发送请求）以及其他配置（上传基站，获取标签）
    def __init__(self):
        global idle_tags
        self.ServerConnection = False
        self.http_address = config.options.get("server_ip") + ':' + str(config.options.get('server_port'))
        self.posts_(directory='/PostMyPortNo', parameters={'MyPortNo': config.myinfo.get('MyPortNo')})  # 上传我的portno
        self.gets_(url='/GetTag?First=' + config.myinfo.get('MyFirstTag') + '&Num=' + str(config.myinfo.get(
            'MyTagNum')) + '&Type=' + config.myinfo.get('MyTagType'))
        if idle_tags:
            self.ServerConnection = True
            print("\033[1;32m%s\033[1m" % ">>Server Connection succeeded<<")
        else:
            input("\033[1;31m%s\033[1m" % "Server Connection Failed, press ENTER to exit...")
            sys.exit()

    # get请求
    async def get_(self, str_url):
        """
        get请求服务器，返回值为数据
        :param str_url: 请求地址
        :return:返回值为请求返回的的数据
        """
        global idle_tags
        try:
            url = self.http_address + str_url
            response = await http_client.fetch(url)
        except Exception as ex:
            # lock.release()  # 解锁
            print("Get请求发生异常:" + ex.args)
            return None
        else:
            if response.code == 200:
                resp_dict = json.loads(str(response.body, encoding="UTF-8"))
                msg = resp_dict.get("Msg")
                tags = resp_dict.get("Tags")
                msgtype = resp_dict.get("MsgType")
                if msg and msg != "End":
                    send_que.put(msg)
                    if msgtype == "BsHb":
                        mark.update({'myalive': msg})
                if tags:
                    idle_tags = tags

    # 多线 异步Get请求
    def gets_(self, url=None):
        lock.acquire()
        loop.run_sync(lambda: self.get_(url))
        lock.release()

    # post请求s
    async def post_(self, directory=None, parameters=None):
        """
        post请求，请求服务器，返回值为数据
        :param directory 请求目录
        :param parameters: 参数
        :return:返回值为请求返回的数据
        """
        try:
            url = self.http_address + directory
            response = await http_client.fetch(method='POST', request=url, body=json.dumps(parameters))

        except Exception as ex:
            print("Post请求发生异常:" + ex.args)
            return None
        else:
            if response.code == 200:
                resp_dict = json.loads(str(response.body, encoding="UTF-8"))
                msg = resp_dict.get("Msg")
                if msg and msg != "End":
                    send_que.put(msg)

    # 多线程异步Post方法
    def posts_(self, directory=None, parameters=None):
        lock.acquire()
        loop.run_sync(lambda: self.post_(directory, parameters))
        lock.release()

    # 基站心跳请求
    def Bs_alive(self):
        if mark.get('myalive') is False:
            req_dir = '/GetHb?myPortNo=' + config.myinfo.get('MyPortNo') + '&dataType=' + config.datatype.get(
                'BsHb')  # 请求目录
            self.gets_(url=req_dir)
        else:
            send_que.put(mark.get('myalive'))
        threading.Timer(config.polling_time.get('GetBsHb'), self.Bs_alive).start()  # 每隔15S进行获取一次

    # 标签心跳请求
    def Tg_alive(self):
        l = []
        if online_tags:
            for tag in online_tags:
                url = '/GetHb?myPortNo=' + config.myinfo.get(
                    'MyPortNo') + '&tagPortNo=' + tag + '&dataType=' + config.datatype.get('TgHb') + '&modes=00'
                obj = pool.submit(self.gets_, url)
                l.append(obj)
            [obj.result() for obj in l]
        if config.myinfo.get('MyTagType') is 'Temperature':  # 体温心跳是6S一次
            threading.Timer(6, self.Tg_alive).start()
        else:
            threading.Timer(config.polling_time.get('GetTgHb'), self.Tg_alive).start()

    # action请求
    def action(self):
        if idle_tags:
            for tag in idle_tags:
                url = '/GetEvent?myPortNo=' + config.myinfo.get(
                    'MyPortNo') + '&tagPortNo=' + tag + '&dataType=' + config.datatype.get('Action')
                self.gets_(url)
                time.sleep(1)
            threading.Timer(0, self.action).start()

    # 事件请求
    def event(self, tags):
        if tags:
            l = []
            for tag in tags:
                url = '/GetEvent?myPortNo=' + config.myinfo.get('MyPortNo') + '&dataType=' + config.datatype.get(
                    'TgEvt') + '&event= {}?tagPortNo=' + tag
                if tags is not job_tags:
                    url.format('02')
                else:
                    url.format('01')
                obj = pool.submit(self.gets_, url)
                l.append(obj)
            [obj.result() for obj in l]

    # 数据请求
    def datas_(self):
        if job_tags:
            l = []
            for tag in job_tags:
                url = '/GetData?myPortNo=' + config.myinfo.get(
                    'MyPortNo') + '&tagPortNo=' + tag + '&dataType=' + config.datatype.get('TgDt')
                obj = pool.submit(self.gets_, url)
                l.append(obj)
            [obj.result() for obj in l]
        threading.Timer(config.polling_time.get('GetTgDt'), self.datas_).start()

    # 接收数据处理
    def recv_data_studio(self):
        msg = recv_que.get()  # 接收的数据
        if msg is not None:
            msg = msg.replace(' ', '')  # 去除空格
            datatype = None
            get_on_off = False
            command_type = msg[4:6]  # 事件代码
            my_portno = msg[6:14]  # 基站portno
            tag_portno = msg[14:22]  # 标签portno
            if command_type == "A2":
                online_tags.append(tag_portno)
                try:
                    idle_tags.remove(tag_portno)
                except ValueError:
                    pass  # 当删除的数据不存在的时候忽略掉
                if config.myinfo.get('MyTagType') == 'ProbeTypeColdChain' or config.myinfo.get(
                        'MyTagType') == 'One-pieceColdChain':
                    job_tags.append(tag_portno)
            elif command_type == "A8":  # 获取参数返回，，，，，目前有问题
                datatype = 5
                get_on_off = True
            elif command_type == "A9":  # 设置参数返回，，，目前有问题
                datatype = 6
                get_on_off = True
            elif command_type == "AA":  # 下达用药数据返回
                datatype = 7
                get_on_off = True
            if get_on_off:
                parameter = {'myPortNo': my_portno, 'tagPortNo': tag_portno, 'dataType': datatype}  # 参数
                req_dir = '/PostData'  # 请求目录
                ret_msg = self.post_(req_dir, parameter)
                if ret_msg is not None:
                    send_que.put(ret_msg)  # 存入队列
        threading.Timer(0, self.recv_data_studio).start()

    # 控制器
    def controller(self):
        if config.myinfo.get('MyTagType') is 'Infusion':
            self.infusion_mode()  # 输液模式
        elif config.myinfo.get('MyTagType') is 'Temperature':
            self.temperature_mode()  # 体温模式
        elif config.myinfo.get('MyTagType') is 'One-pieceColdChain' or config.myinfo.get(
                'MyTagType') is 'ProbeTypeColdChain':
            self.cold_chain_mode()  # 冷链模式

    # 输液模式
    def infusion_mode(self):
        pass

    # 冷链模式
    def cold_chain_mode(self):
        self.datas_()  # 请求数据

    # 体温模式
    def temperature_mode(self):
        pass


# 客户端
class SuperClinet(SocketClient, HttpClinet):
    def __init__(self):
        print("\033[1;34m%s\033[1m" % "___System initialization____")
        super().__init__()  # init Httpclinet
        super(SocketClient, self).__init__()  # init Socketclient
        if self.SocketConnection is True and self.ServerConnection is True:
            print("\033[1;32m%s\033[1m" % "____Initialization succeeded_____")
        else:
            input("\033[1;31m%s\033[1m" % 'Initialization failed,Please restart.Press ENTER to exit......')
            sys.exit()

    def main(self):
        thread = []
        try:
            t1 = threading.Thread(target=self.send)
            t2 = threading.Thread(target=self.Bs_alive)
            t3 = threading.Thread(target=self.action)
            t4 = threading.Thread(target=self.controller)
            t5 = threading.Thread(target=self.recv)
            t6 = threading.Thread(target=self.recv_)
            t7 = threading.Thread(target=self.recv_data_studio)
            if config.myinfo.get('MyTagType') is 'Temperature':  # 体温模式心跳数据加体温数据
                tx = threading.Thread(target=self.Tg_alive)
                thread.append(tx)
            thread.append(t1)
            thread.append(t2)
            thread.append(t3)
            thread.append(t4)
            thread.append(t5)
            thread.append(t6)
            thread.append(t7)
            for t in thread:
                t.start()
        except Exception as e:
            print(e)


if __name__ == '__main__':
    client = SuperClinet()
    client.main()
