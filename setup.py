from setuptools import setup

setup(name='cryptotik',
      version='0.2.8',
      description='Standardized common API for several cryptocurrency exchanges.',
      url='https://github.com/peerchemist/cryptotik',
      author='Peerchemist',
      author_email='peerchemist@protonmail.ch',
      license='BSD',
      packages=['cryptotik'],
      install_requires=['requests'],
      tests_require=['pytest'],
      zip_safe=False)
