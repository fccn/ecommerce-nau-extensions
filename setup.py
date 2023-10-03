"""
Setup file for the ecommerce-nau-extensions Open edX ecommerce NAU extensions.
"""

from pathlib import Path

from setuptools import setup

README = open(Path(__file__).parent / 'README.rst').read()
CHANGELOG = open(Path(__file__).parent / 'CHANGELOG.rst').read()


setup(
    name='ecommerce-nau-extensions',
    description='Ecommerce NAU extensions',
    version='0.1.0',
    author='FCCN',
    author_email='info@nau.edu.pt',
    long_description=f'{README}\n\n{CHANGELOG}',
    long_description_content_type='text/x-rst',
    url='https://github.com/fccn/ecommerce-nau-extensions',
    include_package_data=True,
    zip_safe=False,
    license="AGPL 3.0",
    keywords='Django openedx openedx-plugin ecommerce',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
    ],
    install_requires=[
        'Django~=3.2',
    ],
    packages=[
        'nau_extensions',
    ],
    entry_points={
        'ecommerce': [
            'nau_extensions = nau_extensions.apps:NauExtensionsConfig',
        ],
    },
)
