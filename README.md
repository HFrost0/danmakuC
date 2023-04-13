# danmakuC

Faster conversion for larger Danmaku to Ass format. Core conversion part is written in C++ while with
user-friendly Python api and cli.

Currently, support types:

* [bilibili](htts://wwww.bilibili.com) protobuf
* [niconico](https://www.nicovideo.jp) protobuf since 0.3.1

## Why danmakuC?

.ass format can be recognized by your local video player,
while [Danmaku2ASS](https://github.com/m13253/danmaku2ass) and [biliass](https://github.com/yutto-dev/biliass) provides
a great tool to convert danmaku to ass format, the conversion of large danmaku is **incredibly slow** since it's a heavy
CPU bound task for Python🥲. danmakuC refactor those two repos and provide a much faster C++ implementation to speed up
conversion. Let's see how fast it is:

|                     | test_dm.bin (218 comments) | test_dm_large.bin (59,003 comments) |
|---------------------|----------------------------|-------------------------------------|
| Danmaku2ASS/biliass | 0.0105 s                   | 47.0650 s                           |
| danmakuC            | 0.0009 s                   | 0.2077 s                            |

> Results are obtained in M1 arm64 chip mac with python3.10 danmakuC v0.1a0, danmaku file is downloaded from bilibili by
> [bilix](https://github.com/HFrost0/bilix).

As you can see, over 100 times faster in large conversion. For video with more viewer and comments
(like movie and tv play), a fast tool like danmakuC is just what you need✊.

## Install

```shell
pip install danmakuC
```

## Usage

In python, you can use danmakuC like:

```python
from danmakuC.bilibili import proto2ass

with open("test_dm_large.bin", "rb") as f:
    ass_text = proto2ass(f.read(), 1920, 1080)

```

If you prefer to use cli, you can use danmakuC like:

```shell
danmakuC src.bin -o tgt.ass
```

for more feature, you can check `-h`

```shell
danmakuC -h

usage: danmakuC [-h] [-o OUTPUT] [-s SIZE] [-rb RESERVE_BLANK] [-fn FONT] [-fs FONTSIZE] [-a ALPHA] [-dm DURATION_MARQUEE] [-ds DURATION_STILL] [-fl FILTER] [-r] [-v] file

danmakuC cli version 0.2a0

positional arguments:
  file                  Comment file to be processed

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file
  -s SIZE, --size SIZE  Stage size in pixels [default: 1920x1080]
  -rb RESERVE_BLANK, --reserve-blank RESERVE_BLANK
                        Reserve blank on the bottom of the stage [default: 0]
  -fn FONT, --font FONT
                        Specify font face [default: sans-serif]
  -fs FONTSIZE, --fontsize FONTSIZE
                        Default font size [default: 25.0]
  -a ALPHA, --alpha ALPHA
                        Alpha [default: 1.0]
  -dm DURATION_MARQUEE, --duration-marquee DURATION_MARQUEE
                        Duration of scrolling comment display [default: 5.0]
  -ds DURATION_STILL, --duration-still DURATION_STILL
                        Duration of still comment display [default: 5.0]
  -fl FILTER, --filter FILTER
                        Regular expression to filter comments
  -r, --reduce          Reduce the amount of comments if stage is full
  -v, --version         show program's version number and exit


```
