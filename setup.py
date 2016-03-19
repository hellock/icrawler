from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='image_crawler',
      version='0.1.0',
      description='A mini framework of image crawlers',
      long_description='This framework blabla',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Topic :: Utilities',
      ],
      keywords='image crawler spider',
      url='http://github.com/storborg/funniest',
      author='Kai Chen',
      author_email='chenkaidev@gmail.com',
      license='MIT',
      packages=['image_crawler'],
      install_requires=[
          'requests',
          'beautifulsoup4',
          'lxml'
      ],
      zip_safe=False)
