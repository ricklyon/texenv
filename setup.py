# setup.py

from setuptools import setup

setup(
    name='pytex',
    version='0.1.0',
    py_modules=['pytex'],
    install_requires=[
        'click',
    ],
    entry_points={
        'console_scripts': [
            'pytex = pytex:cli',
        ],
    },
)