from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name="can_of_proxy",
    version="0.1.0",
    description="""Easy but powerful proxy management python package. Used to fetch, manage, rotate and use proxies. """,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Paul Hartwich",
    packages=find_packages(include=["bitefix"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=required,
    license="MIT",
    url="https://github.com/paul-hartwich/can_of_proxy",
)
