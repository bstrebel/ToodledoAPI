from setuptools import setup
import re

version = re.search(
    "^__version__\s*=\s*'(.*)'",
    open('oxapi/__init__.py').read(),
    re.M).group(1)

setup(
    name='ToodledoAPI',
    version=version,
    packages=['tdapi'],
    url='https://github.com/bstrebel/ToodledoAPI',
    license='GPL2',
    author='Bernd Strebel',
    author_email='b.strebel@digitec.de',
    description='Toodledo Web Service API',
    long_description=open('README.md').read(),
    install_requires=['requests']
)
