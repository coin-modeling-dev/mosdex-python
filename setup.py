from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='mosdex-python',
    version='2020.1-dev1',
    packages=find_packages(exclude="tests"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/coin-modeling-dev/mosdex-python.git',
    author='Alan King',
    author_email='kingaj@us.ibm.com',
    description='Package for running demo of MOSDEX modular optimization problem data standard',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6'
)
