#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2018/12/05
del
配置文件
"""

# 参数
options = {
    'server_ip': 'http://127.0.0.1',
    'server_port': 8888,
    'socket_ip': '10.10.1.20',
    'socket_port': 6001,
    'my_port': 3000
}

# 基站的信息
myinfo = {
    'MyPortNo': '75654321',
    'MyTagNum': 30,
    'MyFirstTag': '81654321',
    'MyTagType': 'Infusion',  # Temperature,One-pieceColdChain,ProbeTypeColdChain
}

# 数据类型
datatype = {
    'BsHb': '0',  # 基站心跳
    'TgHb': '1',  # 标签心跳
    'Action': '2',  # action请求
    'TgDt': '3',  # 标签数据
    'TgEvt': '4',  # 标签事件
    'RespGtSer': '5',  # 获取参数返回
    'RespStSer': '6',  # 设置参数返回
    'HrMe': '7'  # 下达用药数据
}
