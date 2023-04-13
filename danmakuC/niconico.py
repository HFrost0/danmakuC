import io
import re
from .ass import Ass
from .protobuf.niconico import NNDCommentProto
from typing import Union, Optional

__all__ = ['proto2ass']


def proto2ass(
        proto_file: Union[bytes, io.IOBase],
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
) -> Optional[str]:
    ass = Ass(width, height, reserve_blank, font_face, font_size, alpha, duration_marquee,
              duration_still, comment_filter, reduced)
    if isinstance(proto_file, bytes):
        proto_file = io.BytesIO(proto_file)
    comment = NNDCommentProto()
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
    if out_filename:
        return ass.write_to_file(out_filename)
    else:
        return ass.to_string()


def process_mailstyle(mail, fontsize):
    pos, color, size, patissier = 0, 0xffffff, fontsize, False
    if not mail:
        return pos, color, size  # , patissier
    for mailstyle in mail.split():
        if mailstyle == 'ue':  # top middle
            pos = 1
        elif mailstyle == 'shita':  # bottom middle
            pos = 2
        elif mailstyle == 'naka':  # flying left-to-right
            pos = 0
        elif mailstyle == 'big':
            size = fontsize * 1.44
        elif mailstyle == 'small':
            size = fontsize * 0.64
        elif mailstyle in NICONICO_COLOR_MAPPINGS:
            color = NICONICO_COLOR_MAPPINGS[mailstyle]
        elif len(mailstyle) == 7 and re.match(HEX_COLOR_REGEX, mailstyle):
            color = int(re.match(HEX_COLOR_REGEX, mailstyle).group(1), base=16)
        elif mailstyle == 'patissier':  # for comment art/fixed speed?
            patissier = True

    return pos, color, size  # , patissier


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
