from setuptools import setup, find_packages

setup(
    name="qhld-data",
    version="1.1.0",
    description="QHLD Data",
    url="https://github.com/politicalwatch/qhld-data",
    author="pr3ssh",
    packages=find_packages(),
    install_requires=[
        "marshmallow==3.22.0",
        "marshmallow-mongoengine==0.31.2",
        "mongoengine==0.29.1",
        "regex==2024.11.6",
        "natsort==8.4.0",
        "python-slugify==8.0.4",
    ],
)
