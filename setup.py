from pybind11.setup_helpers import build_ext, Pybind11Extension
from setuptools import setup, find_packages

ext_modules = [
    Pybind11Extension(
        "danmakuC.ass",
        [
            'danmakuC/csrc/ass.cpp',
            'third_party/fmt/src/format.cc',
        ],
        include_dirs=[
            'third_party/boost_1_81_0',
            'third_party/fmt/include',
        ],
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
    description="Faster conversion for larger Danmaku to Ass format",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    classifiers=[
        'Programming Language :: C++',
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3 :: Only",
    ],
    author="HFrost0, m13253, Nyakku Shigure",
    license="GPLv3",
    packages=find_packages(exclude=['tests', 'danmaku_old']),
    package_data={'danmakuC': ["*.pyi"]},
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    # https://cibuildwheel.readthedocs.io/en/stable/faq/#windows-importerror-dll-load-failed-the-specific-module-could-not-be-found
    python_requires=">=3.8.3",
    install_requires=["protobuf>=4.21.0"],
    entry_points={
        "console_scripts": "danmakuC=danmakuC.__main__:main",
    },
)
