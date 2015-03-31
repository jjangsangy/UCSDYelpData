from setuptools import setup, find_packages

exec(open('yelp/__version__.py').read())

setup(
    name='UCSDYelpData',
    version=__version__,
    description='UCSD Yelp Data Challenge',
    author='UCSD',
    author_email='sah002@ucsd.edu',
    url='https://github.com/jjangsangy/YelpDataChallenge',
    install_requires=['numpy', 'pandas'],
    packages=find_packages(),
)

