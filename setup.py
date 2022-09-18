from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='search_package',
    version='0.0.1',    
    description='A simple Python package to find papers by title or doi and export the data to bib file.',
    url='',
    author='Jacek Barszczewski',
    author_email='jacek.barszczewski@bse.eu',
    license='MIT',
    packages=['search_paper'],
    install_requires=required,
    package_data={'': ['data/*.txt']},
    include_package_data=True,
)