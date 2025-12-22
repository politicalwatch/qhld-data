from setuptools import setup, find_packages

setup(
    name="tipi-data",
    version="1.1.0",
    description="TIPI Data",
    url="https://github.com/politicalwatch/tipi-data",
    author="pr3ssh",
    packages=find_packages(),
    install_requires=[
        "marshmallow==3.26.2",
        "marshmallow-mongoengine==0.31.2",
        "mongoengine==0.29.1",
        "regex==2024.11.6",
        "natsort==8.4.0",
        "python-slugify==8.0.4",
    ],
)
