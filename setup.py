from setuptools import find_packages, setup

setup(
    name="stacker",
    version="1.0.1",
    packages=find_packages(),
    package_data={'stacker': ['data/*']},
    entry_points={
        "console_scripts": [
            "stacker = stacker.stacker:main",
        ],
    },
)
