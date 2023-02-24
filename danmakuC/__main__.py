import argparse
import gzip
import os
from typing import Callable, Union

from danmakuC.__version__ import __version__
# sites
from danmakuC import bilibili, niconico


def is_gzip_file(filename: Union[str, os.PathLike]) -> bool:
    gzip_magic = b'\x1f\x8b'
    with open(filename, mode='rb') as fp:
        return fp.read(2) == gzip_magic


def get_convert_func(proto_file: Union[str, os.PathLike], ) -> Callable:
    if is_gzip_file(proto_file):
        open_func = gzip.open
    else:
        open_func = open
    with open_func(proto_file, mode='rb') as fp:
        firstbyte = fp.read(1)
    if firstbyte == b'\x0a':
        convert_func = bilibili.proto2ass
    else:
        convert_func = niconico.proto2ass
    return convert_func


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

    with open(args.file, 'rb') as f:
        res = get_convert_func(args.file)(
            f,
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
            out_filename=args.output,
        )
    if res is not None:
        print(res)


if __name__ == "__main__":
    main()
