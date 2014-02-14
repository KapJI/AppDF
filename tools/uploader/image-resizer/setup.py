from distutils.core import setup, Command
from distutils.command.build import build as _build
import os, sys

class build_server(_build):
  description = 'custom build command'
  sub_commands = []

  def initialize_options(self):
    _build.initialize_options(self)
    self.cwd = None
  def finalize_options(self):
    _build.finalize_options(self)
    self.cwd = os.getcwd()
  def run(self):
    if os.environ.get('READTHEDOCS', None) == 'True':
      # won't build on readthedocs.org
      return
    assert os.getcwd() == self.cwd, 'Must be in package root.'
    os.system('qmake && make')

if os.name == 'nt':
  image_resizer_binary = 'release/image_resizer.exe'
else:
  image_resizer_binary = 'image_resizer'

setup(name='image-resizer',
      version='0.1',
      description='Simple Qt-base tool for image resizing',
      author='Ruslan Sayfutdinov',
      author_email='ruslan-s@yandex-team.ru',
      license='MIT',
      url='https://github.com/KapJI/AppDF',
      py_modules=['image_resizer'],
      cmdclass={
        'build': build_server,
      },
      data_files=[('qtbin', [image_resizer_binary])],
)
