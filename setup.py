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
    zip_safe=False,
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'dict2dict = yelp.__main__:main'
        ]
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Unix Shell',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Utilities',
    ],
)

