import logging
import math
from typing import Tuple, Sequence
from danmakuC.old.ass import AssText
from danmakuC.protobuf import DmSegMobileReply

Comment = Tuple[float, float, int, str, int, int, float, float, float]


def proto2comments(proto_bytes: bytes, font_size: float) -> Sequence[Comment]:
    target = DmSegMobileReply()
    target.ParseFromString(proto_bytes)
    res = []
    for i, elem in enumerate(target.elems):
        try:
            assert elem.mode in (1, 4, 5, 6, 7, 8)
            if elem.mode in (1, 4, 5, 6):
                c = elem.content.replace("/n", "\n")
                size = int(elem.fontsize) * font_size / 25.0
                res.append((
                    elem.progress / 1000,  # 视频内出现的时间
                    elem.ctime,  # 弹幕的发送时间（时间戳）
                    i,
                    c,
                    {1: 0, 4: 2, 5: 1, 6: 3}[elem.mode],
                    elem.color,
                    size,
                    (c.count("\n") + 1) * size,
                    CalculateLength(c) * size,
                ))
            elif elem.mode == 7:  # positioned comment
                c = elem.content
                res.append((elem.progress / 1000, elem.ctime, i, c, "bilipos", elem.color, elem.fontsize, 0, 0))
            elif elem.mode == 8:
                pass  # ignore scripted comment
        except (AssertionError, AttributeError, IndexError, TypeError, ValueError):
            logging.warning("Invalid comment: %s" % elem.content)
            continue
    res.sort()
    return res


def comments2ass(
        comments: Sequence[Comment],
        width: int,
        height: int,
        reserve_blank: int = 0,
        font_face: str = "sans-serif",
        font_size: float = 25.0,
        text_opacity: float = 1.0,
        duration_marquee: float = 5.0,
        duration_still: float = 5.0,
        reduced: bool = False,
) -> str:
    """todo c++ speed up this"""
    ass = AssText(width, height, reserve_blank, font_face, font_size, text_opacity, duration_marquee, duration_still)
    rows = [[None] * (height - reserve_blank + 1) for _ in range(4)]
    for idx, i in enumerate(comments):
        if isinstance(i[4], int):
            row = 0
            rowmax = height - reserve_blank - i[7]
            while row <= rowmax:
                freerows = TestFreeRows(rows, i, row, width, height, reserve_blank, duration_marquee, duration_still)
                if freerows >= i[7]:
                    MarkCommentRow(rows, i, row)
                    ass.WriteComment(i, row)
                    break
                else:
                    row += freerows or 1
            else:
                if not reduced:
                    row = FindAlternativeRow(rows, i, height, reserve_blank)
                    MarkCommentRow(rows, i, row)
                    ass.WriteComment(i, row)
        elif i[4] == "bilipos":
            ass.WriteCommentBilibiliPositioned(i)
        else:
            logging.warning("Invalid comment: %r" % i[3])
    return str(ass)


def proto2ass(
        proto_bytes: bytes,
        width: int,
        height: int,
        reserve_blank: int = 0,
        font_face: str = "sans-serif",
        font_size: float = 25.0,
        text_opacity: float = 1.0,
        duration_marquee: float = 5.0,
        duration_still: float = 5.0,
        comment_filter: str = None,
        reduced: bool = False,
) -> str:
    comments = proto2comments(proto_bytes, font_size)
    ass_str = comments2ass(
        comments, width, height,
        reserve_blank, font_face, font_size, text_opacity, duration_marquee, duration_still, reduced)
    return ass_str


def TestFreeRows(rows, c, row, width, height, bottomReserved, duration_marquee, duration_still):
    res = 0
    rowmax = height - bottomReserved
    targetRow = None
    if c[4] in (1, 2):
        while row < rowmax and res < c[7]:
            if targetRow != rows[c[4]][row]:
                targetRow = rows[c[4]][row]
                if targetRow and targetRow[0] + duration_still > c[0]:
                    break
            row += 1
            res += 1
    else:
        try:
            thresholdTime = c[0] - duration_marquee * (1 - width / (c[8] + width))
        except ZeroDivisionError:
            thresholdTime = c[0] - duration_marquee
        while row < rowmax and res < c[7]:
            if targetRow != rows[c[4]][row]:
                targetRow = rows[c[4]][row]
                try:
                    if targetRow and (
                            targetRow[0] > thresholdTime
                            or targetRow[0] + targetRow[8] * duration_marquee / (targetRow[8] + width) > c[0]
                    ):
                        break
                except ZeroDivisionError:
                    pass
            row += 1
            res += 1
    return res


def FindAlternativeRow(rows, c, height, bottomReserved):
    res = 0
    for row in range(height - bottomReserved - math.ceil(c[7])):
        if not rows[c[4]][row]:
            return row
        elif rows[c[4]][row][0] < rows[c[4]][res][0]:
            res = row
    return res


def MarkCommentRow(rows, c, row):
    try:
        for i in range(row, row + math.ceil(c[7])):
            rows[c[4]][i] = c
    except IndexError:
        pass


def CalculateLength(s):
    return max(map(len, s.split("\n")))  # May not be accurate
