from codecs import open
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

with open('LICENSE', 'r', encoding='utf-8') as f:
    license = f.read()


with open('requirements.txt', 'r', encoding='utf-8') as f:
    install_requires = f.read()

setup(
    author='remokasu',
    name="pystacker",
    version="1.2.2",
    license=license,
    url='https://github.com/remokasu/stacker',
    install_requires=install_requires,
    packages=find_packages(),
    package_data={'stacker': ['data/*', 'plugins/*']},
    description='Stacker: RPN Calculator in Python',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='reverse-polish-calculator rpn terminal-app',
    entry_points={
        "console_scripts": [
            "stacker = stacker.stacker:main",
        ],
    },
)
