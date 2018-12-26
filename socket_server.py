import socket

# 创建服务端的socket对象socketserver
socketserver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = '10.10.1.20'
port = 6000
# 绑定地址（包括ip地址会端口号）
socketserver.bind((host, port))
# 设置监听
socketserver.listen(5)
# 等待客户端的连接
# 注意：accept()函数会返回一个元组
# 元素1为客户端的socket对象，元素2为客户端的地址(ip地址，端口号)
clientsocket, addr = socketserver.accept()

# while循环是为了能让对话一直进行，直到客户端输入q
while True:
    # 接收客户端的请求
    recvmsg = clientsocket.recv(1024)
    # 把接收到的数据进行解码

    strData = str(recvmsg.hex())
    # 判断客户端是否发送q，是就退出此次对话
    print("收到:" + str(strData))
    if strData[4:6] == '22':
        tag = strData[14:22]
        bs = strData[6:14]
        msg = '3e0da2{}{}01ffff3f'.format(bs, tag)
        print(msg)
        clientsocket.send(bytes.fromhex(msg))

socketserver.close()
