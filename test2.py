class Song():
    def __init__(self):

        print(1)

class Singer():
    def __init__(self):

        print(2)

class Mtv(Song, Singer):
    def __init__(self):
        super().__init__()         # init Song
        super(Song, self).__init__() # init Singer

mtv = Mtv()
