from setuptools import find_packages, setup

setup(
    name="stacker",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "stacker = stacker.stacker:main",
        ],
    },
    install_requires=[
        "termcolor",
    ],
)