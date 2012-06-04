from setuptools import setup, find_packages
from gimpanel import __version__

setup(name='gimpanel',
      version=__version__,
      description='A GTK+ front-end for Fcitx',
      author='Tualatrix Chou',  
      author_email='tualatrix@gmail.com',
      url='http://imtx.com',
      scripts=['fcitx-gimpanel'],
      packages=find_packages(exclude=['tests']),
      data_files=[
          ('../etc/xdg/autostart/', ['build/share/applications/fcitx-gimpanel.desktop']),
      ],
      license='GNU GPL',
      platforms='linux',
      test_suite='tests',
)
