from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='icrawler',
      version='0.1.0',
      description='A mini framework of image crawlers',
      long_description='This package is a mini framework for multi-thread image'
                       ' crawler. It also provides some useful built-in'
                       ' crawlers such as google, bing, baidu, flickr image'
                       ' crawlers and a greedy website crawler.',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Topic :: Utilities',
      ],
      keywords='image crawler spider',
      url='https://github.com/hellock/icrawler',
      author='Kai Chen',
      author_email='chenkaidev@gmail.com',
      license='MIT',
      packages=['icrawler'],
      install_requires=[
          'beautifulsoup4',
          'lxml',
          'Pillow',
          'requests'
      ],
      zip_safe=False)
