import os
from setuptools import setup, find_packages

version = '0.3.1'


def read(f):
    return open(os.path.join(os.path.dirname(__file__), f)).read().strip()

#install_reqs = parse_requirements('requirements.txt', session=PipSession())
#reqs = [str(ir.req) for ir in install_reqs]
deps= [
    'git://github.com/KeepSafe/html-structure-diff.git@#egg=sdiff',
    'git://github.com/KeepSafe/content-validator.git#egg=content_validator'
]
reqs= [
    'aiohttp==0.21.2',
    'gunicorn==19.3.0',
    'docopt==0.4.0',
    'hoep==1.0.2',
    'parse==1.6.6',
    'requests==2.13.0',
    'inlinestyler==0.2.0',
    'PasteDeploy==1.5.2',
    'simplejson==3.8.2',
    'pybars3==0.9.1',
    'raven==5.26.0',
    'datadog==0.14.0',
    'content-validator',
    'sdiff'
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
      install_requires = reqs,
      dependency_links = deps,
      entry_points={
          'paste.app_factory': ['app = notifier:app']
      },
      include_package_data = False)
