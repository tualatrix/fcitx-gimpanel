from setuptools import setup, find_packages
from gimpanel import __version__

setup(name='gimpanel',
      version=__version__,
      description='The GTK font of Fcitx',
      author='Tualatrix Chou',  
      author_email='tualatrix@gmail.com',
      url='http://imtx.com',
      scripts=['fcitx-gimpanel'],
      packages=find_packages(exclude=['tests']),
      license='GNU GPL',
      platforms='linux',
      test_suite='tests',
)
