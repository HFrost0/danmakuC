import time
from danmaku_old import proto2ass as proto2ass_old
from danmakuC import proto2ass

file = 'test_dm_large.bin'


def test_cmp():
    """"
    test_dm.bin and test_dm_large.bin is obtained by bilix from bilibili.com
    """
    text = test_new()
    text2 = test_old()
    for l1, l2 in zip(text.split('\n'), text2.split('\n')):
        # todo different time convert due to ceil ?
        if l1 != l2:
            print(l1)
            print(l2)


def test_new():
    a = time.time()
    with open(file, "rb") as f:
        text = proto2ass(f.read(), 1920, 1080)
    print(time.time() - a)
    return text


def test_old():
    a = time.time()
    with open(file, "rb") as f:
        text = proto2ass_old(f.read(), 1920, 1080)
    print(time.time() - a)
    return text
