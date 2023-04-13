import json
from google.protobuf.json_format import MessageToJson
from .ass import Ass
from .protobuf.bilibili import BiliCommentProto, BiliViewProto
from typing import Union, Optional
import io

__all__ = ['proto2ass', 'parse_view']


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

    if isinstance(proto_file, io.IOBase):
        proto_file = proto_file.read()
    target = BiliCommentProto()
    target.ParseFromString(proto_file)
    for elem in target.elems:
        if elem.mode == 8:
            continue  # ignore scripted comment
        try:
            ass.add_comment(
                elem.progress / 1000,  # 视频内出现的时间
                elem.ctime,  # 弹幕的发送时间（时间戳）
                elem.content,
                elem.fontsize,
                {1: 0, 4: 2, 5: 1, 6: 3, 7: 4}[elem.mode],
                elem.color,
            )
        except TypeError:  # incase integer overflow https://github.com/HFrost0/bilix/issues/102
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
