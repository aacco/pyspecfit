from setuptools import setup, find_packages

setup(
    name='pyspecfit',
    version='0.0.3',
    author="Taiga Fuse",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=[
        "numpy>=1.26.4",
        "pandas>=2.2.2",
        "scipy>=1.14.1",
        "pybeads>=1.0.1",
    ],
)
