import json
import re
from danmakuC._c.ass import VectorComment, Comment, comments2ass
from danmakuC.protobuf import DmSegMobileReply


def proto2comments(proto_bytes: bytes) -> VectorComment:
    target = DmSegMobileReply()
    target.ParseFromString(proto_bytes)
    comments = VectorComment()
    for elem in target.elems:
        c = elem.content
        if elem.mode in (1, 4, 5, 6):
            c = c.replace("/n", "\n")
        elif elem.mode == 8:
            continue  # ignore scripted comment
        comments.append(Comment(
            elem.progress / 1000,  # 视频内出现的时间
            elem.ctime,  # 弹幕的发送时间（时间戳）
            c,
            elem.fontsize,
            {1: 0, 4: 2, 5: 1, 6: 3, 7: 4}[elem.mode],
            elem.color,
        ))
    return comments


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
        comment_filter: str = None,
        reduced: bool = False,
) -> str:
    comments = proto2comments(proto_bytes)
    res = comments2ass(comments, width, height, reserve_blank, font_face, font_size, alpha, duration_marquee,
                       duration_still, reduced)
    return res
