from setuptools import setup, find_packages

setup(
    name='peakfit',
    version='0.0.2',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},    
    install_requires=[
        "numpy==1.26.4",
        "pandas==2.2.2",
        "scipy==1.14.1",
        "matplotlib==3.9.0",
        "pybeads==1.0.1",
    ]
)
