class Root(object):
    def __init__(self):
        print('ok, good luck!')


class A(Root):
    def __init__(self):
        super(A, self).__init__()


class B(A):
    def __init__(self):
        super(B, self).__init__()


class C(B):
    def __init__(self):
        super(C, self).__init__()


if __name__ == '__main__':
    c = C()

