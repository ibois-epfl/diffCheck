from setuptools import setup, find_packages

setup(
    name='diffCheck',
    version='0.0.2',
    packages=find_packages(),
    description='DiffCheck is a package to check the differences between two timber structures',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Andrea Settimi, Damien Gilliard, Eleni Skevaki, Marirena Kladeftira, Julien Gamerro, Stefana Parascho, and Yves Weinand',
    author_email='andrea.settimi@epfl.ch',
    url='https://github.com/diffCheckOrg/diffCheck',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
)