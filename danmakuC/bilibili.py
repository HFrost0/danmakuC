# import json
from ._c.ass import Ass
from .protobuf import BiliCommentProto, NNDComment
import re
import io
import gzip
import os

__all__ = ['proto2ass']

def is_gzip_file(filename: str | os.PathLike) -> bool:
    gzip_magic = b'\x1f\x8b'
    with open(filename, mode='rb') as fp:
            if fp.read(2) == gzip_magic:
                res = True
            else:
                res = False
    return res

def proto2ass(
        proto_file: str | bytes | io.IOBase | os.PathLike,
        width: int,
        height: int,
        reserve_blank: int = 0,
        font_face: str = "sans-serif",
        font_size: float = 25.0,
        alpha: float = 1.0,
        duration_marquee: float = 5.0,
        duration_still: float = 5.0,
        comment_filter: str = "",
        reduced: bool = False,
        out_filename: str = "",
) -> str | int:
    if isinstance(proto_file, (str, os.PathLike)):
        if is_gzip_file(proto_file):
            open_func = gzip.open
        else:
            open_func = open
        with open_func(proto_file, mode='rb') as fp:
            firstbyte = fp.read(1)
    elif isinstance(proto_file, bytes):
        firstbyte = proto_file[0:1]
    elif isinstance(proto_file, io.IOBase):
        firstbyte = proto_file.read(1)
        proto_file.seek(-1, 1)
    else:
        raise TypeError('proto_file must be str, bytes, os.PathLike object or a file object')

    if firstbyte == b'\x0a':
        convert_func = proto2assbili
    else:
        convert_func = proto2assnico
    return convert_func(
        proto_file,
        width,
        height,
        reserve_blank=reserve_blank,
        font_face=font_face,
        font_size=font_size,
        alpha=alpha,
        duration_marquee=duration_marquee,
        duration_still=duration_still,
        comment_filter=comment_filter,
        reduced=reduced,
        out_filename=out_filename,
    )

def proto2assbili(
        proto_file: bytes | io.IOBase,
        width: int,
        height: int,
        reserve_blank: int = 0,
        font_face: str = "sans-serif",
        font_size: float = 25.0,
        alpha: float = 1.0,
        duration_marquee: float = 5.0,
        duration_still: float = 5.0,
        comment_filter: str = "",
        reduced: bool = False,
        out_filename: str = "",
) -> str | int:
    ass = Ass(width, height, reserve_blank, font_face, font_size, alpha, duration_marquee,
              duration_still, comment_filter, reduced)

    if isinstance(proto_file, io.IOBase):
        proto_bytes = proto_file.read()
    elif isinstance(proto_file, (str, os.PathLike)): # TODO
        if is_gzip_file(proto_file):
            open_func = gzip.open
        else:
            open_func = open
        proto_bytes = open_func(proto_file, mode='rb').read()
    elif isinstance(proto_file, bytes):
        proto_bytes = proto_file
    target = BiliCommentProto()
    target.ParseFromString(proto_bytes)
    for elem in target.elems:
        if elem.mode == 8:
            continue  # ignore scripted comment
        ass.add_comment(
            elem.progress / 1000,  # 视频内出现的时间
            elem.ctime,  # 弹幕的发送时间（时间戳）
            elem.content,
            elem.fontsize,
            {1: 0, 4: 2, 5: 1, 6: 3, 7: 4}[elem.mode],
            elem.color,
        )
    if out_filename:
        return ass.write_to_file(out_filename)
    else:
        return ass.to_string()


# https://w.atwiki.jp/nicoapi/pages/20.html
NICONICO_COLOR_MAPPINGS = {
    # Regular users
    'red': 0xff0000,
    'pink': 0xff8080,
    'orange': 0xffcc00,
    'yellow': 0xffff00,
    'green': 0x00ff00,
    'cyan': 0x00ffff,
    'blue': 0x0000ff,
    'purple': 0xc000ff,
    'black': 0x000000,
    # Premium users
    'niconicowhite': 0xcccc99,
    'white2': 0xcccc99,
    'truered': 0xcc0033,
    'red2': 0xcc0033,
    'passionorange': 0xff6600,
    'orange2': 0xff6600,
    'madyellow': 0x999900,
    'yellow2': 0x999900,
    'elementalgreen': 0x00cc66,
    'green2': 0x00cc66,
    'marineblue': 0x33ffcc,
    'blue2': 0x33ffcc,
    'nobleviolet': 0x6633cc,
    'purple2': 0x6633cc,
}

HEX_COLOR_REGEX = re.compile('#([a-fA-F0-9]{6})')
def process_mailstyle(mail, fontsize):
    pos, color, size, patissier = 0, 0xffffff, fontsize, False
    if not mail:
        return pos, color, size #, patissier
    for mailstyle in mail.split():
        if mailstyle == 'ue': # top middle
            pos = 1
        elif mailstyle == 'shita': # bottom middle
            pos = 2
        elif mailstyle == 'naka': # flying left-to-right
            pos = 0
        elif mailstyle == 'big':
            size = fontsize * 1.44
        elif mailstyle == 'small':
            size = fontsize * 0.64
        elif mailstyle in NICONICO_COLOR_MAPPINGS:
            color = NICONICO_COLOR_MAPPINGS[mailstyle]
        elif len(mailstyle) == 7 and re.match(HEX_COLOR_REGEX, mailstyle):
            color = int(re.match(HEX_COLOR_REGEX, mailstyle).group(1), base=16)
        elif mailstyle == 'patissier': #for comment art/fixed speed?
            patissier = True

    return pos, color, size #, patissier

def proto2assnico(
        proto_file: str | bytes | io.IOBase,
        width: int,
        height: int,
        reserve_blank: int = 0,
        font_face: str = "sans-serif",
        font_size: float = 25.0,
        alpha: float = 1.0,
        duration_marquee: float = 5.0,
        duration_still: float = 5.0,
        comment_filter: str = "",
        reduced: bool = False,
        out_filename: str = "",
) -> str | int:
    ass = Ass(width, height, reserve_blank, font_face, font_size, alpha, duration_marquee,
              duration_still, comment_filter, reduced)
    if isinstance(proto_file, bytes):
        proto_file = io.BytesIO(proto_file)
    if isinstance(proto_file, io.IOBase):
        comment = NNDComment()
        while True:
            size = int.from_bytes(proto_file.read(4), byteorder='big', signed=False)
            if size == 0:
                break

            comment_serialized = proto_file.read(size)
            comment.ParseFromString(comment_serialized)
            pos, color, size = process_mailstyle(comment.mail, font_size)
            ass.add_comment(
                comment.vpos / 100,
                comment.date,
                comment.content,
                size,
                pos,
                color,
            )
    elif isinstance(proto_file, str):
        ass.add_comments_from_file_niconico(proto_file)
    elif isinstance(proto_file, os.PathLike):
        ass.add_comments_from_file_niconico(proto_file.__fspath__())
    if out_filename:
        return ass.write_to_file(out_filename)
    else:
        return ass.to_string()
