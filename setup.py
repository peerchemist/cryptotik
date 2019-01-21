from setuptools import setup
from os import path

classifiers = [
  'Development Status :: 4 - Beta',
  'Intended Audience :: Financial and Insurance Industry',
  'Programming Language :: Python',
  'Operating System :: OS Independent',
  'Natural Language :: English',
  'License :: OSI Approved :: BSD License'
]

# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(name='cryptotik',
      version='0.35.1',
      description='Standardized common API for several cryptocurrency exchanges.',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/indiciumfund/cryptotik',
      author='Peerchemist',
      author_email='peerchemist@protonmail.ch',
      license='BSD-3',
      packages=['cryptotik'],
      install_requires=['requests', 'python-dateutil'],
      tests_require=['pytest']
      )
