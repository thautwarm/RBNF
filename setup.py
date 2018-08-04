from setuptools import setup
from Redy.Tools.Version import Version
from Redy.Tools.PathLib import Path

with open('./README.md', encoding='utf-8') as f:
    readme = f.read()

version_filename = 'next_version'
with open(version_filename) as f:
    version = Version(f.read().strip())

with Path("./rbnf/__release_info__.py").open('w') as f:
    f.write('__VERSION__ = {}\n__AUTHOR__ = "thautwarm"'.format(
        repr(str(version))))

setup(
    name='rbnf',
    version=str(version),
    keywords='parser-generator, context-sensitive, ebnf',
    description="context sensitive grammar parser generator for CPython",
    long_description=readme,
    long_description_content_type='text/markdown',
    license='MIT',
    python_requires='>=3.6.0',
    url='https://github.com/thautwarm/Ruiko',
    author='thautwarm',
    author_email='twshere@outlook.com',
    packages=[
        'rbnf', 'rbnf.core', 'rbnf.core.parser_algo', 'rbnf.py_tools',
        'rbnf.bootstrap', 'rbnf.edsl', 'rbnf.auto_lexer', 'rbnf.std',
        'rbnf.zero'
    ],
    entry_points={'console_scripts': ['rbnf=rbnf.cli:main']},
    package_data={
        'rbnf': [
            'rbnf_libs/std/*.rbnf', 'edsl/*.pyi', 'core/*.pyi', 'zero/*.pyi',
            'rbnf_libs/*.rbnf'
        ]
    },
    install_requires=['linq-t>=0.1', 'Redy>=0.2.2', 'rtpy>=0.2.8'],
    platforms='any',
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    zip_safe=False)

version.increment(version_number_idx=2, increment=1)
if version[2] is 42:
    version.increment(version_number_idx=1, increment=1)
if version[1] is 42:
    version.increment(version_number_idx=0, increment=1)

with open(version_filename, 'w') as f:
    f.write(str(version))
