from setuptools import setup
from Redy.Tools.Version import Version
from Redy.Tools.PathLib import Path
# with open('./README.rst', encoding='utf-8') as f:
#     readme = f.read()
readme = ''

version_filename = 'next_version'
with open(version_filename) as f:
    version = Version(f.read().strip())

setup(name='rbnf',
      version=str(version),
      keywords='parser-generator, context-sensitive, ebnf',
      description="context sensitive grammar parser generator",
      long_description=readme,
      license='MIT',
      url='https://github.com/thautwarm/Ruiko',
      author='thautwarm',
      author_email='twshere@outlook.com',
      packages=['rbnf', 'rbnf.std', 'rbnf.AutoLexer', 'rbnf.zero'],
      package_data={
      	'rbnf_libs':[
      		str(each) for each in 
      			Path('./rbnf_libs')
      			.collect(
      				lambda path: path.endswith('.rbnf'))
      		]},
      install_requires=[
          'Redy'
      ],
      platforms='any',
      classifiers=[
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: Implementation :: CPython'],
      zip_safe=False)

version.increment(version_number_idx=2, increment=1)
if version[2] is 42:
    version.increment(version_number_idx=1, increment=1)
if version[1] is 42:
    version.increment(version_number_idx=0, increment=1)

with open(version_filename, 'w') as f:
    f.write(str(version))
