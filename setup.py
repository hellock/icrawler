import os.path as osp
from setuptools import find_packages, setup


def get_version():
    version_file = osp.join(osp.dirname(__file__), 'icrawler/version.py')
    with open(version_file, 'r') as f:
        exec(compile(f.read(), version_file, 'exec'))
    return locals()['__version__']


def readme():
    filename = osp.join(osp.dirname(__file__), 'README.rst')
    with open(filename, 'r') as f:
        return f.read()


setup(
    name='icrawler',
    version=get_version(),
    description='A mini framework of image crawlers',
    long_description=readme(),
    keywords='image crawler spider',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Utilities',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    url='https://github.com/hellock/icrawler',
    author='Kai Chen',
    author_email='chenkaidev@gmail.com',
    license='MIT',
    install_requires=[
        'beautifulsoup4>=4.4.1',
        'lxml',
        'requests>=2.9.1',
        'six>=1.10.0',
        'Pillow'
    ],
    zip_safe=False
)  # yapf: disable
