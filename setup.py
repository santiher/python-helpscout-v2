from setuptools import setup


def version():
    with open('helpscout/__init__.py', 'r') as f:
        for line in f:
            if line.startswith('__version__ ='):
                return line[15:-2]
    return '0.0.0'


setup(
    name='helpscout',
    version=version(),
    install_requires=['requests'],
    packages=['helpscout'],
    test_suite='tests',
)
