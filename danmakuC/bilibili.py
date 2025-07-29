import json
import xml.etree.ElementTree as ET
from google.protobuf.json_format import MessageToJson
from .ass import Ass
from .protobuf.bilibili import BiliCommentProto, BiliViewProto
from typing import Union, Optional
import io

__all__ = ['proto2ass', 'xml2ass', 'parse_view']


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

    if isinstance(proto_file, io.IOBase):
        proto_file = proto_file.read()
    target = BiliCommentProto()
    target.ParseFromString(proto_file)
    # elem.mode > 8, example: https://www.bilibili.com/video/BV1Js411f78P/
    mode_map = {1: 0, 4: 2, 5: 1, 6: 3, 7: 4}
    for elem in target.elems:
        if elem.mode not in mode_map:
            continue
        try:
            ass.add_comment(
                elem.progress / 1000,  # 视频内出现的时间
                elem.ctime,  # 弹幕的发送时间（时间戳）
                elem.content,
                elem.fontsize / 25.0,
                mode_map[elem.mode],
                elem.color,
                elem.pool
            )
        except TypeError:
            # TypeError: incase integer overflow https://github.com/HFrost0/bilix/issues/102
            continue
    if out_filename:
        return ass.write_to_file(out_filename)
    else:
        return ass.to_string()


def xml2ass(
        xml_file: Union[bytes, io.IOBase],
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
    # elem.mode > 8, example: https://www.bilibili.com/video/BV1Js411f78P/
    mode_map = {1: 0, 4: 2, 5: 1, 6: 3, 7: 4}
    for dm in root.findall("d"):
        # 0: progress, 1: mode, 2: fontsize, 3: color, 4: ctime, 5: pool/weight?, 6: midHash, 7: id
        p = dm.get("p", "").split(',')
        if not p:
            continue
        progress = float(p[0])
        mode = int(p[1])
        fontsize = float(p[2])
        color = int(p[3]) if p[3] != "undefined" else 16777215
        ctime = float(p[4]) / 1000
        pool = int(p[5]) if int(p[5]) <= 3 else 0
        content = dm.text or ""
        if mode not in mode_map:
            continue
        try:
            ass.add_comment(
                progress / 1000,  # 视频内出现的时间
                ctime,  # 弹幕的发送时间（时间戳）
                content,
                fontsize / 25.0,
                mode_map[mode],
                color,
                pool
            )
        except TypeError:
            # TypeError: incase integer overflow https://github.com/HFrost0/bilix/issues/102
            continue
    if out_filename:
        return ass.write_to_file(out_filename)
    else:
        return ass.to_string()


def parse_view(content: bytes) -> dict:
    dm_view = BiliViewProto()
    dm_view.ParseFromString(content)
    dm_view = json.loads(MessageToJson(dm_view))
    return dm_view
