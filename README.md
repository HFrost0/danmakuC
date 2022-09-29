# danmakuC

Faster conversion for larger Danmaku to Ass format. Core conversion part is written in C++ while with
user-friendly Python api and cli (working on it...).

## Why danmakuC?

While [Danmaku2ASS](https://github.com/m13253/danmaku2ass) and [biliass](https://github.com/yutto-dev/biliass) provides
a great tool to convert danmaku to ass format, the conversion of large danmaku is **incredibly slow** since it's a heavy
CPU bound task for Python🥲. danmakuC refactor those two repos and provide a much faster C++ implementation to speed up
conversion. Let's see how fast it is:

|                     | test_dm.bin (218 comments) | test_dm_large.bin (59,003 comments) |
|---------------------|----------------------------|-------------------------------------|
| Danmaku2ASS/biliass | 0.0105 s                   | 47.0650 s                           |
| danmakuC            | 0.0009 s                   | 0.2077 s                            |

> Results are obtained in M1 arm64 chip mac with python3.10, danmaku file is downloaded from bilibili by bilix.

As you can see, over 100 times faster in large conversion. For video with more viewer and comments
(like movie and tv play), a fast tool like danmakuC is just what you need✊.

## Install
Currently, author is learning how to provide c++ pypi extension...

## Usage

Working on more feature including cli and xml conversion...

```python
from danmakuC.utils import proto2ass

with open("test_dm_large.bin", "rb") as f:
    ass_text = proto2ass(f.read(), 1920, 1080)

```
