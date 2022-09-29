import time
from danmakuC.old import proto2ass as proto2ass_old
from danmakuC.utils import proto2ass


def test_dm2ass():
    """"
    test_dm.bin and test_dm_large.bin is obtained by bilix from bilibili.com
    """
    a = time.time()
    with open("test_dm_large.bin", "rb") as f:
        text = proto2ass(f.read(), 1920, 1080)
    print(time.time() - a)

    a = time.time()
    with open("test_dm.bin", "rb") as f:
        text2 = proto2ass_old(f.read(), 1920, 1080)
    print(time.time() - a)

    for l1, l2 in zip(text.split('\n'), text2.split('\n')):
        # todo different time convert due to ceil ?
        if l1 != l2:
            print(l1)
            print(l2)
