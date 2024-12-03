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
        style, commands = process_mailstyle(comment.mail)
        pos, color, size = style["pos"], style["color"], style["size"] * font_size
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
    return ass.to_string()


def process_mailstyle(mail):
    style = {"pos": 0, "size": 1, "color": 0xFFFFFF, "font": "defont"}
    commands = {k: False for k in OTHERS}
    if isinstance(mail, str):
        mail = mail.split()
    # only the first command of each type is used, see https://qa.nicovideo.jp/faq/show/6167
    for mailstyle in (m.lower() for m in reversed(mail)):
        if mailstyle in POS_MAPPING:
            style["pos"] = POS_MAPPING[mailstyle]
        elif mailstyle in SIZE_MAPPING:
            style["size"] = SIZE_MAPPING[mailstyle]
        elif mailstyle in NICONICO_COLOR_MAPPINGS:
            style["color"] = NICONICO_COLOR_MAPPINGS[mailstyle]
        elif match := HEX_COLOR_REGEX.match(mailstyle):
            style["color"] = int(match.group(1), 16)
        elif mailstyle in FONT_MAPPING:
            style["font"] = FONT_MAPPING[mailstyle]
        elif mailstyle in OTHERS:
            commands[mailstyle] = True
        elif match := DURATION_REGEX.match(mailstyle):
            style["duration"] = float(match.group(2) or match.group(4))
    style["alpha"] = 0.5 if commands.get("_live") else 1
    return style, commands


# https://dic.nicovideo.jp/a/コマンド
# https://w.atwiki.jp/nicoapi/pages/20.html
NICONICO_COLOR_MAPPINGS = {
    # Regular users
    'white': 0xffffff,
    'red': 0xff0000,
    'pink': 0xff8080,
    'orange': 0xffc000,
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
    'marineblue': 0x3399ff,
    'blue2': 0x3399ff,
    'nobleviolet': 0x6633cc,
    'purple2': 0x6633cc,
    'pink2': 0xff33cc,
    'cyan2': 0x00cccc,
    'black2': 0x666666,
}

POS_MAPPING = {
    "naka": 0, # flying left-to-right
    "ue": 1, # top middle
    "shita": 2, # bottom middle
    # "＠逆": 3, # flying right-to-left, not a command

    # http://himado.in/help.php?name=comment_command
    "middle": 0,
    "top": 1,
    "bottom": 2,
    # "hidari",
    # "left",
    # "chu",
    # "center",
    # "migi",
    # "right",
    # "(X,Y)",
}

SIZE_MAPPING = {
    "small": 2/3,
    "medium": 1,
    "big": 13/9,
}

FONT_MAPPING = {
    "mincho": "Yu Mincho", # Simsun
    "gothic": "Yu Gothic", # Gulim, SimHei
}

OTHERS = {
    # "184",
    # "ca",
    "invisible",
    # "patissier",
    "full",
    "ender",
    "_live", # alpha = 0.5
}

DURATION_REGEX = re.compile(r'^(@(\d+(\.\d+)?)|(\d+)sec)$')
HEX_COLOR_REGEX = re.compile('^#([a-fA-F0-9]{6})$')
