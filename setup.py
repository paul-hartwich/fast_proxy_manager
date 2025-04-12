from setuptools import setup, find_packages
from ineedproxy.version import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name="ineedproxy",
    version=__version__,
    description="An aio library designed for easy and reliable access to working proxies. It primarily fetches, manages, rotates, and stores proxy data.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Paul Hartwich",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=required,
    license="MIT",
    url="https://github.com/paul-hartwich/ineedproxy",
)
