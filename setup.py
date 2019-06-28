from setuptools import setup


def version():
    with open('helpscout/__init__.py', 'r') as f:
        for line in f:
            if line.startswith('__version__ ='):
                return line[15:-2]
    return '0.0.0'


def readme():
    with open('README.md') as f:
        return f.read()


setup(
    name='python-helpscout-v2',
    version=version(),
    author='santiher',
    url='https://github.com/santiher/python-helpscout-v2',
    description='Wrapper to query Help Scout v2 API',
    long_description=readme(),
    long_description_content_type='text/markdown',
    license='MIT',
    install_requires=['requests'],
    packages=['helpscout'],
    test_suite='tests',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3'
        ]
)
