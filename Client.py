#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2018/12/05
del
客户端
"""
import binascii
import re
import threading
import time

import config
import socket
import queue
from concurrent.futures import ThreadPoolExecutor as Pool

send_que = queue.Queue()
recv_que = queue.Queue()
Message_buf = bytes()


# socket客户端
# noinspection PyTypeChecker
class SocketClient(object):

    # 连接服务器初始化以及其他配置
    def __init__(self):
        self.message_buf = bytes()
        self.TCP_SOCKET = socket.socket()
        self.SocketConnection = False
        self.my_address = (socket.gethostbyname(socket.gethostname()), config.options.get("my_port"))  # 设置本地地址
        self.tcpserver_address = (config.options.get('socket_ip'), config.options.get('socket_port'))  # 设置tcpserver地址
        pass

    # 发送
    def send_(self):
        l = []
        try:
            # msg = send_que.get()
            msg = "1"
            obj = Pool.submit(self.send, msg)
            l.append(obj)
            [obj.result() for obj in l]
        except Exception as es:
            print('发送出现异常')
            # mainlog_.logger.info(es.args)
        else:
            threading.Timer(0, self.send_).start()

    # 发送
    def send(self, msg):
        try:
            self.TCP_SOCKET.send(bytes.fromhex(msg))
        except Exception:
            print("发送出错")
        else:
            # self.send_counter += 1
            print("{}:发送了___{}".format(time.strftime("%Y-%m-%d %H:%M:%S $ms", time.localtime()), msg))

    # 接收
    def recv_(self):
        try:
            if len(self.message_buf) > 0:
                msg = self.message_buf[0:2]
                msg_len = int.from_bytes(msg[1:], byteorder='big', signed=False) + 2
                msg += self.message_buf[2:msg_len]
                self.message_buf = self.message_buf[msg_len:]
                msg = str(binascii.b2a_hex(msg))[2:-1]
                msg = re.sub(r'(?<=\w)(?=(?:\w\w)+$)', " ", msg).upper()
                print("{}接收到___{} ".format(time.strftime("%Y-%m-%d %H:%M:%S $ms", time.localtime()), msg))
                # self.recv_counter += 1
                recv_que.put(msg)
        except Exception:
            # self.rountdown_(3)
            print('接收发生了异常')
        else:
            threading.Timer(0, self.recv_).start()

    # 接收
    def recv(self):
        try:
            msg = self.TCP_SOCKET.recv(2048)
            if msg != b'':
                self.message_buf += msg
        except Exception:
            print("接收出错")
        else:
            threading.Timer(0, self.recv).start()

    # 连接
    def connection_(self):
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tcp_socket.bind(self.my_address)
            tcp_socket.connect(self.tcpserver_address)
        except Exception as ex:
            print("\033[0;31m%s\033[0m" % "<<<Socket connection Succeeded>>")
        else:
            self.TCP_SOCKET = tcp_socket
            self.SocketConnection = True
            print("\033[0;32m%s\033[0m" % ">>Socket Connection Failed<<")


# Http客户端
class HttpClinet(object):

    # 连接服务器初始化（往服务器发送请求）以及其他配置
    def __init__(self):
        pass

    # get请求
    def get_(self):
        pass

    # post请求
    def post_(self):
        pass

    # 心跳请求
    def alive(self):
        pass

    # action请求
    def action(self):
        pass

    # 事件请求
    def event(self):
        pass

    # 数据请求
    def datas_(self):
        pass

    # 控制器
    def controller(self):
        pass


# 客户端
class SuperClinet(HttpClinet, SocketClient):


    pass

