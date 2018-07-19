from setuptools import setup

setup(name='cryptotik',
      version='0.34',
      description='Standardized common API for several cryptocurrency exchanges.',
      url='https://github.com/peerchemist/cryptotik',
      author='Peerchemist',
      author_email='peerchemist@protonmail.ch',
      license='BSD-3',
      packages=['cryptotik'],
      install_requires=['requests', 'python-dateutil'],
      tests_require=['pytest']
      )
