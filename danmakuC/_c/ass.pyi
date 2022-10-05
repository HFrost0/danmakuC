# Defined in csrc/ass.cpp

class VectorComment:
    def append(self, comment: Comment) -> None: ...


class Comment:
    def __init__(self, progress: float, ctime: int, content: str, font_size: float, mode: int, color: int) -> None: ...


def comments2ass(
        comments: VectorComment,
        width: int,
        height: int,
        reserve_blank: int = 0,
        font_face: str = "sans-serif",
        font_size: float = 25.0,
        alpha: float = 1.0,
        duration_marquee: float = 5.0,
        duration_still: float = 5.0,
        reduced: bool = False
) -> str: ...
