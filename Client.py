#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2018/12/05
del
客户端
"""
import binascii
import json
import re
import sys
import threading
import time
import requests
import config
import socket
import queue
from concurrent.futures import ThreadPoolExecutor as Pool

send_que = queue.Queue()  # 发送队列
recv_que = queue.Queue()  # 接收队列
Message_buf = bytes()  # 消息buf
lock = threading.Lock()  # 线程锁
idle_tags = list()  # 空闲标签列表
job_tags = list()  # 工作的标签
online_tags = list()  # 在线的标签
pool = Pool()  # 线程池
# 计数器c
counter = {
    'send': 0,
    'recv': 0,
    'tghb': 0,
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

    # 发送
    def send_(self):
        l = []
        try:
            msg = send_que.get()
            obj = Pool.submit(self.send, msg)
            l.append(obj)
            [obj.result() for obj in l]
        except Exception as es:
            print('发送出现异常:' + es.args)
            # mainlog_.logger.info(es.args)
        else:
            threading.Timer(0, self.send_).start()

    # 发送
    def send(self, msg):
        try:
            self.TCP_SOCKET.send(bytes.fromhex(msg))
        except Exception as ex:
            print("发送出错:" + ex.args)
        else:
            print("{}:发送了——{}".format(time.strftime("%F %H:%M:%S", time.localtime()), msg))

    # 接收
    def recv_(self):
        true = True
        while true:
            try:
                if len(self.message_buf) > 0:
                    msg = self.message_buf[0:2]
                    msg_len = int.from_bytes(msg[1:], byteorder='big', signed=False) + 2
                    msg += self.message_buf[2:msg_len]
                    self.message_buf = self.message_buf[msg_len:]
                    msg = str(binascii.b2a_hex(msg))[2:-1]
                    msg = re.sub(r'(?<=\w)(?=(?:\w\w)+$)', " ", msg).upper()
                    print("{}接收到——{} ".format(time.strftime("%F %H:%M:%S", time.localtime()), msg))
                    recv_que.put(msg)
            except Exception as es:
                print('接收发生了异常:' + es.args)
                true = False

    # 接收
    def recv(self):
        true = True
        while true:
            try:
                msg = self.TCP_SOCKET.recv(2048)
                if msg != b'':
                    self.message_buf += msg
            except Exception as es:
                print("接收出错:" + es.args)
                true = False

    # 连接
    def connection_(self):
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tcp_socket.bind(self.my_address)
            tcp_socket.connect(self.tcpserver_address)
        except Exception:
            print("\033[1;31m%s\033[1m" % "<<<Socket Connection Failed>>")
        else:
            self.TCP_SOCKET = tcp_socket
            self.SocketConnection = True
            print("\033[1;32m%s\033[1m" % ">>Socket connection Succeeded<<")

    # 接收数据处理
    def recv_data_studio(self):
        msg = recv_que.get()
        if msg is not None:
            pass
        threading.Timer(0, self.recv_data_studio).start()


# Http客户端
class HttpClinet(object):

    # 连接服务器初始化（往服务器发送请求）以及其他配置（上传基站，获取标签）
    def __init__(self):
        global idle_tags
        self.ServerConnection = False
        self.http_address = config.options.get("server_ip") + ':' + str(config.options.get('server_port'))
        if self.post_(directory='/PostMyPortNo',
                      parameters={'MyPortNo': config.myinfo.get('MyPortNo')}) is not None:  # 上传我的portno
            parameter = {'First': config.myinfo.get('MyFirstTag'), 'Num': config.myinfo.get('MyTagNum'),
                         'Type': config.myinfo.get('MyTagType')}  # 参数
            req_data = self.get_(directory='/GetTag', parameters=parameter)
            if req_data is not None:
                idle_tags = req_data.get('Msg')
                self.ServerConnection = True
                print("\033[1;32m%s\033[1m" % ">>Server Connection succeeded<<")
            else:
                input("\033[1;31m%s\033[1m" % "Server Connection Failed, press ENTER to exit...")
                sys.exit()
        else:
            input("\033[1;31m%s\033[1m" % "Server Connection Failed, press ENTER to exit......")
            sys.exit()

    # get请求
    def get_(self, directory=None, parameters=None):
        """
        get请求服务器，返回值为数据
        :param directory: 请求目录
        :param parameters: 请求参数
        :return:返回值为请求返回的的数据
        """
        try:
            url = self.http_address + directory
            lock.acquire()  # 加锁
            req = requests.get(url, params=parameters)
            lock.release()  # 解锁
        except Exception as ex:
            lock.release()  # 解锁
            print("Get请求发生异常:" + ex.args)
            return None
        else:
            if req.status_code == 200:
                text = req.json()
                return text

    # 多线程Get请求
    def gets_(self, directory=None, parameters=None):
        value = self.get_(directory, parameters)
        if value is not None:
            send_que.put(value.get('Msg'))

    # post请求
    def post_(self, directory=None, parameters=None):
        """
        post请求，请求服务器，返回值为数据
        :param directory 请求目录
        :param parameters: 参数
        :return:返回值为请求返回的数据
        """
        try:
            url = self.http_address + directory
            lock.acquire()  # 加锁
            req = requests.post(url=url, data=json.dumps(parameters), headers={'Content-Type': 'application/json'})
            lock.release()  # 解锁
        except Exception as ex:
            lock.release()  # 解锁
            print("Post请求发生异常:" + ex.args)
            return None
        else:
            if req.status_code == 200:
                text = req.json()
                return text

    # 基站心跳请求
    def Bs_alive(self):
        req_dir = '/GetHb'  # 请求目录
        para = {'myPortNo': config.myinfo.get('MyPortNo'), 'dataType': config.datatype.get('BsHb')}  # 请求参数
        value = self.get_(directory=req_dir, parameters=para)
        if value is not None:
            send_que.put(value['Msg'])  # 将数据存入发送队列
        threading.Timer(config.polling_time.get('GetBsHb'), self.Bs_alive).start()  # 每隔15S进行获取一次

    # 标签心跳请求
    def Tg_alive(self):
        l = []
        req_dir = '/GetHb'
        for tag in online_tags:
            para = {'myPortNo': config.myinfo.get('MyPortNo'), 'tagPortNo': tag,
                    'dataType': config.datatype.get('TgHb'), 'modes': '00'}
            obj = pool.submit(self.gets_, req_dir, para)
            l.append(obj)
        [obj.result() for obj in l]
        threading.Timer(config.polling_time.get('GetTgHb'), self.Tg_alive).start()

    # action请求
    def action(self):
        req_dir = '/GetEvent'
        for tag in idle_tags:
            para = {'myPortNo': config.myinfo.get('MyPortNo'), 'tagPortNo': tag,
                    'dataType': config.datatype.get('Action')}
            value = self.get_(directory=req_dir, parameters=para)
            if value is not None:
                send_que.put(value['Msg'])
                time.sleep(1)  # 同一个基站1S发送一个Action请求

    # 事件请求
    def event(self, tags):
        if tags:
            l = []
            req_dir = '/GetEvent'
            para = {'myPortNo': config.myinfo.get('MyPortNo'), 'dataType': config.datatype.get('TgEvt'),
                    'event': '01'}
            if tags is not job_tags:
                para.update({'event': '02'})
            for tag in tags:
                para.update({'tagPortNo': tag})
                obj = pool.submit(self.gets_, req_dir, para)
                l.append(obj)
            [obj.result() for obj in l]

    # 数据请求
    def datas_(self):
        l = []
        req_dir = '/GetData'
        for tag in job_tags:
            para = {'myPortNo': config.myinfo.get('MyPortNo'), 'tagPortNo': tag,
                    'dataType': config.datatype.get('TgDt')}
            obj = pool.submit(self.gets_, req_dir, para)
            l.append(obj)
        [obj.result() for obj in l]
        threading.Timer(config.polling_time.get('GetTgDt'), self.datas_).start()

    # 控制器
    def controller(self):
        self.Bs_alive()  # 基站心跳
        if config.myinfo.get('MyTagType') is 'Infusion':
            pass
        elif config.myinfo.get('MyTagType') is 'Temperature':
            pass
        elif config.myinfo.get('MyTagType') is 'One-pieceColdChain' or config.myinfo.get(
                'MyTagType') is 'ProbeTypeColdChain':
            self.cold_chain_mode()  # 冷链模式

    # 输液模式
    def infusion_mode(self):
        pass

    # 冷链模式
    def cold_chain_mode(self):
        self.action()  # action请求
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


if __name__ == '__main__':
    a = SuperClinet()
