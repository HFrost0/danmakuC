import argparse
import gzip
import io
import os
import sys

from danmakuC.__version__ import __version__
# sites
from danmakuC import bilibili
from danmakuC import niconico


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
        convert_func = bilibili.proto2ass
    else:
        convert_func = niconico.proto2ass
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


def main():
    parser = argparse.ArgumentParser(description=f"danmakuC cli version {__version__}", prog="danmakuC")
    parser.add_argument("file", help="Comment file to be processed")
    parser.add_argument("-o", "--output", help="Output file")

    parser.add_argument("-s", "--size", type=str, help="Stage size in pixels [default: 1920x1080]", default="1920x1080")
    parser.add_argument(
        "-rb", "--reserve-blank", help="Reserve blank on the bottom of the stage [default: 0]", type=int, default=0)
    parser.add_argument(
        "-fn",
        "--font",
        help="Specify font face [default: sans-serif]",
        default="sans-serif",
    )
    parser.add_argument(
        "-fs",
        "--fontsize",
        help="Default font size [default: 25.0]",
        type=float,
        default=25.0,
    )
    parser.add_argument("-a", "--alpha", help="Alpha [default: 1.0]", type=float, default=1.0)
    parser.add_argument(
        "-dm",
        "--duration-marquee",
        help="Duration of scrolling comment display [default: 5.0]",
        type=float,
        default=5.0,
    )
    parser.add_argument(
        "-ds",
        "--duration-still",
        help="Duration of still comment display [default: 5.0]",
        type=float,
        default=5.0,
    )
    parser.add_argument("-fl", "--filter", help="Regular expression to filter comments", default="")
    # parser.add_argument(
    #     "-flf", "--filter-file", help="Regular expressions from file (one line one regex) to filter comments"
    # )
    parser.add_argument("-r", "--reduce", action="store_true", help="Reduce the amount of comments if stage is full")
    parser.add_argument("-v", "--version", action="version", version=f"version {__version__}")
    # parse args
    args = parser.parse_args()
    width, height = args.size.split("x")
    width = int(width)
    height = int(height)
    fo = None
    if args.output == '-':
        fo = sys.stdout
        out_filename = ''
    elif args.output:
        # fo = open(args.output, "w", encoding="utf-8-sig", errors="replace", newline="\r\n")
        out_filename = args.output
    else:
        out_filename = args.file
        if out_filename.endswith('.bin'):
            out_filename = args.file[:-4]
        elif out_filename.endswith('.bin.gz'):
            out_filename = args.file[:-7]
        out_filename += '.ass'
    output = proto2ass(
        args.file,
        width,
        height,
        args.reserve_blank,
        args.font,
        args.fontsize,
        args.alpha,
        args.duration_marquee,
        args.duration_still,
        args.filter,
        args.reduce,
        out_filename=out_filename,
    )
    if fo:
        fo.write(output)
        fo.close()


if __name__ == "__main__":
    main()
