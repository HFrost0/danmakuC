import io
import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from .ass import Ass
from .protobuf.niconico import NNDCommentProto
from typing import Union, Optional

__all__ = ['proto2ass', 'json2ass', 'xml2ass']


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
        bold: bool = False,
        live: bool = False,
        out_filename: str = "",
) -> Optional[str]:
    ass = Ass(width, height, reserve_blank, font_face, font_size, alpha, duration_marquee,
              duration_still, comment_filter, reduced, bold, live)
    if isinstance(proto_file, bytes):
        proto_file = io.BytesIO(proto_file)
    comment = NNDCommentProto()
    while True:
        size = int.from_bytes(proto_file.read(4), byteorder='big', signed=False)
        if size == 0:
            break
        comment_serialized = proto_file.read(size)
        comment.ParseFromString(comment_serialized)
        pool = 1 if comment.fork == "owner" else 0
        style = {"pos": 0, "size": 1, "color": 0xFFFFFF, "font": "defont"}
        style, commands = process_mailstyle(comment.mail, style)
        pos, color, size = style["pos"], style["color"], style["size"]
        ass.add_comment(
            comment.vpos / 100,
            comment.date,
            comment.content,
            size,
            pos,
            color,
            pool,
        )
    if out_filename:
        return ass.write_to_file(out_filename)
    return ass.to_string()


def json2ass(
        json_file: Union[str, bytes, io.IOBase],
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
        bold: bool = False,
        live: bool = False,
        out_filename: str = "",
) -> Optional[str]:
    ass = Ass(width, height, reserve_blank, font_face, font_size, alpha, duration_marquee,
              duration_still, comment_filter, reduced, bold, live)
    if isinstance(json_file, (str, bytes)):
        data = json.loads(json_file)
    else:
        data = json.load(json_file)
    frk = None
    if isinstance(data, dict):
        for key in ["data", "threads", "comments"]:
            if key in data:
                if key == "comments":
                    frk = data.get("fork", "")
                data = data[key]
    if frk is not None:
        commentlist = {frk: data}
    elif data and data[0].get("comments") is not None:
        commentlist = {}
        for cmt in data:
            if comments := cmt["comments"]:
                commentlist.setdefault(cmt.get("fork", ""), []).extend(comments)
    else:
        commentlist = {"": data}
    scripts = []
    for f, comments in commentlist.items():
        if f == "owner":
            comments.sort(key=lambda c: c["vposMs"])
            pool = 1
        else:
            pool = 0
        for comment in comments:
            fork = f
            vpos = comment["vposMs"] / 1000
            text = comment["body"]
            unixdate = datetime.fromisoformat(comment["postedAt"]).timestamp()
            mail = comment["commands"]
            style = {"pos": 0, "size": 1, "color": 0xFFFFFF, "font": "defont"}
            if text.startswith(('@', '＠', '/')) and fork == "owner":
                style, commands = process_mailstyle(mail, style)
                dr = commands.get("duration", 30)
                parse_nicoscript(text, vpos, dr, style, scripts)
                continue
            text, style = process_nicoscript(text, style, vpos, fork, scripts)
            style, commands = process_mailstyle(mail, style)
            if commands.get("invisible"):
                continue
            pos, color, size = style["pos"], style["color"], style["size"]
            dr = commands.get("duration") or (duration_still if pos in [1, 2] else duration_marquee)
            alpha_factor = style["alpha"]
            font = style["font"]
            ass.add_nico_comment(
                vpos,
                dr,
                int(unixdate),
                text,
                size,
                pos,
                color,
                alpha_factor,
                font,
                pool,
                live or commands["full"],
                commands["ender"]
            )
    if out_filename:
        return ass.write_to_file(out_filename)
    return ass.to_string()


def xml2ass(
        xml_file: Union[str, bytes, io.IOBase],
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
        bold: bool = False,
        live: bool = False,
        out_filename: str = "",
) -> Optional[str]:
    ass = Ass(width, height, reserve_blank, font_face, font_size, alpha, duration_marquee,
              duration_still, comment_filter, reduced, bold, live)
    if isinstance(xml_file, (str, bytes)):
        root = ET.fromstring(xml_file)
    else:
        root = ET.parse(xml_file).getroot()
    scripts = []
    for chat in root.findall("chat"):
        fork = chat.get("fork", "")
        pool = 1 if fork == "owner" else 0
        vpos = int(chat.get("vpos")) / 100
        date = int(chat.get("date"))
        mail = chat.get("mail", '')
        text = chat.text or ''
        style = {"pos": 0, "size": 1, "color": 0xFFFFFF, "font": "defont"}
        if text.startswith(('@', '＠', '/')) and fork == "owner":
            style, commands = process_mailstyle(mail, style)
            dr = commands.get("duration", 30)
            parse_nicoscript(text, vpos, dr, style, scripts)
            continue
        text, style = process_nicoscript(text, style, vpos, fork, scripts)
        style, commands = process_mailstyle(mail, style)
        if commands.get("invisible"):
            continue
        pos, color, size = style["pos"], style["color"], style["size"]
        dr = commands.get("duration") or (duration_still if pos in [1, 2] else duration_marquee)
        alpha_factor = style["alpha"]
        font = style["font"]
        ass.add_nico_comment(
            vpos,
            dr,
            date,
            text,
            size,
            pos,
            color,
            alpha_factor,
            font,
            pool,
            live or commands["full"],
            commands["ender"]
        )
    if out_filename:
        return ass.write_to_file(out_filename)
    return ass.to_string()


def process_mailstyle(mail: Union[str, list], style: dict):
    commands = {k: False for k in OTHERS}
    if isinstance(mail, str):
        mail = mail.split()
    # only the first command of each type is used, see https://qa.nicovideo.jp/faq/show/6167
    for mailstyle in (m.lower() for m in reversed(mail)):
        if mailstyle in POS_MAPPING:
            if style["pos"] == 3 and mailstyle == 'naka':
                continue
            style["pos"] = POS_MAPPING[mailstyle]
        elif mailstyle in SIZE_MAPPING:
            style["size"] = SIZE_MAPPING[mailstyle]
        elif mailstyle in NICONICO_COLOR_MAPPINGS:
            style["color"] = NICONICO_COLOR_MAPPINGS[mailstyle]
        elif match := HEX_COLOR_REGEX.match(mailstyle):
            style["color"] = int(match.group(1), 16)
        elif mailstyle in FONT_MAPPING:
            style["font"] = mailstyle
        elif mailstyle in OTHERS:
            commands[mailstyle] = True
        elif match := DURATION_REGEX.match(mailstyle):
            commands["duration"] = float(match.group(2) or match.group(4))
    style["alpha"] = 0.5 if commands.get("_live") or commands.get("translucent") else 1
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
    "defont", # MS PGothic, Hiragino Sans
    "mincho", # Yu Mincho, SimSun, Hiragino Mincho
    "gothic", # Yu Gothic, Gulim, SimHei, Hiragino Sans
}

OTHERS = {
    # "184",
    # "ca",
    "invisible",
    # "patissier",
    "full",
    "ender",
    "_live", # alpha = 0.5
    "translucent", # alpha = 0.5? niconama
}

DURATION_REGEX = re.compile(r'^(@(\d+(\.\d+)?)|(\d+)sec)$')
HEX_COLOR_REGEX = re.compile('^#([a-fA-F0-9]{6})$')


# https://qa.nicovideo.jp/faq/show/7386
NAME_PATTERN = re.compile(r'^[＠@](\S+)(?:\s+(.*))?$', re.DOTALL)
FUNC_PARAMS = {
            "デフォルト": {},
            "置換": {
                "keyword": {
                    "default": '',
                },
                "replacement": {
                    "default": '',
                },
                "range": {
                    "default": '単',
                    "values": {'単', '全'},
                },
                "target": {
                    "default": 'コメ',
                    "values": {'全', 'コメ', '投コメ', '含まない', '含む'},
                },
                "condition": {
                    "default": '部分一致',
                    "values": {'部分一致', '完全一致'},
                },
            },
            "逆": {"target": {
                "default": '全',
                "values": {'全', 'コメ', '投コメ'},}
            },
        }


def parse_nicoscript(text: str, vpos: float, dr: float, style: dict, scripts: list):
    text = text.replace(r'\n', '\n').replace(r'\t', '\t')
    match = NAME_PATTERN.match(text.strip())
    if not match:
        return
    func_name = match.group(1)
    if func_name not in FUNC_PARAMS:
        return
    params = FUNC_PARAMS[func_name]
    result = {key: param.get("default") for key, param in params.items()}
    if match.group(2):
        args_string = match.group(2).strip()
        args = re.findall(r'"[^"]*"|\'[^\']*\'|\S+', args_string)
        args = [arg.strip('"').strip("'") for arg in args]
        i = 0
        for key in params:
            if i < len(args):
                value = args[i]
                if "values" in params[key] and value not in params[key]["values"]:
                    continue
                result[key] = value
                i += 1
    result["func_name"] = func_name
    result["style"] = style
    result["start"] = vpos
    result["end"] = vpos + dr
    scripts.append(result)


def is_target(target: str, fork: str):
    if target in ["全", "含む"]:
        return True
    if target == "コメ" and fork != "owner":
        return True
    if target in ["投コメ", "含まない"] and fork == "owner":
        return True
    return False

def process_nicoscript(text: str, style: dict, vpos: float, fork: str, scripts: list):
    for s in (s for s in scripts if s["start"] <= vpos <= s["end"]):
        if s["func_name"] == "デフォルト":
            if style != s["style"]:
                style = s["style"].copy()
        elif is_target(s["target"], fork):
            if s["func_name"] == "置換":
                keyword = s["keyword"]
                replacement = s["replacement"]
                if (
                    (s["condition"] == '部分一致' and keyword in text) or
                    (s["condition"] == '完全一致' and keyword == text)
                ):
                    text = text.replace(keyword, replacement) if s["range"] == '単' else replacement
                    if style != s["style"]:
                        style = s["style"].copy()
            elif s["func_name"] == "逆":
                style["pos"] = 3
                # todo: calculations when the comment doesn’t always fly l-to-r
    return text, style
