from pybind11.setup_helpers import build_ext, Pybind11Extension
from setuptools import setup, find_packages

ext_modules = [
    Pybind11Extension(
        "danmakuC._c.ass",
        ['danmakuC/csrc/ass.cpp'],
        libraries=['fmt'],
        library_dirs=['/opt/homebrew/Cellar/fmt/9.1.0/lib'],  # Sort source files for reproducibility
    ),
]


def get_version() -> str:
    with open('danmakuC/__version__.py', 'r', encoding='utf8') as f:
        for line in f.readlines():
            if line.startswith("__version__"):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")


def get_long_description():
    with open('README.md', 'r', encoding='utf8') as f:
        return f.read()


setup(
    name="danmakuC",
    version=get_version(),
    description="Large danmaku conversion c++ speed up",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    classifiers=[
        'Programming Language :: C++',
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ],
    author="HFrost0, m13253, Nyakku Shigure",
    license="GPLv3",
    packages=find_packages(),
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    include_dirs=[
        '/opt/homebrew/Cellar/boost/1.79.0_2/include',
        '/opt/homebrew/Cellar/fmt/9.1.0/include'
    ],
    python_requires=">=3.7",
    setup_requires=["wheel"],
    install_requires=["protobuf>=4.21.0"],
)
