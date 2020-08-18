from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='mosdex-python',
    version='2020.1.dev4',
    packages=['mosdex'],
    package_dir={'mosdex': 'src/mosdex'},
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/coin-modeling-dev/mosdex-python/tree/2020.1.dev4',
    author='Alan King',
    author_email='kingaj@us.ibm.com',
    description='Package for running demo of MOSDEX modular optimization problem data standard',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=['pandas', 'jsonschema', 'records']
)
