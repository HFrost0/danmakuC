# import json
from ._c.ass import Ass
from .protobuf import BiliCommentProto

__all__ = ['proto2ass']


def proto2ass(
        proto_bytes: bytes,
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
) -> str:
    ass = Ass(width, height, reserve_blank, font_face, font_size, alpha, duration_marquee,
              duration_still, comment_filter, reduced)

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
    return ass.to_string()
