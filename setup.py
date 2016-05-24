from setuptools import setup
from setuptools import find_packages


def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='icrawler',
      version='0.2.2',
      description='A mini framework of image crawlers',
      long_description=readme(),
      keywords='image crawler spider',
      packages=find_packages(),
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
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
          'Pillow',
          'requests>=2.9.1',
          'six>=1.10.0'
      ],
      zip_safe=False)
