from setuptools import setup, find_packages

setup(
    name="mascotalm",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "torch>=2.0.0",
        "tokenizers>=0.19.0",
        "tqdm>=4.65.0",
        "numpy>=1.24.0",
        "datasets>=2.14.0",
    ],
)
