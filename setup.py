import os
from setuptools import setup, find_packages

version = '0.3.2'


def read(f):
    return open(os.path.join(os.path.dirname(__file__), f)).read().strip()


reqs = [
    'aiohttp >=3, <3.4',
]

setup(name='ks-translation-notifier',
      version=version,
      description=('Verifies the translation from WebTranslateIt is correct and notifies if it is not'),
      long_description='\n\n'.join((read('README.md'))),
      classifiers=[
          'License :: OSI Approved :: BSD License',
          'Intended Audience :: Developers',
          'Programming Language :: Python'],
      author='Keepsafe',
      author_email='support@getkeepsafe.com',
      url='https://github.com/KeepSafe/translation-notifier/',
      license='Apache',
      packages=find_packages(exclude=['tests']),
      package_data={'notifier': ['templates/*.css', 'templates/*.hbs']},
      namespace_packages=[],
      install_requires=reqs,
      entry_points={
          'paste.app_factory': ['app = notifier:app']
      },
      include_package_data = False)
