# encoding: utf-8
"""Python client library for Pôle Emploi's "Emploi Store Dev"."""

import setuptools

__version__ = '0.8.0'

setuptools.setup(
    name='python-emploi-store',
    packages=['emploi_store'],
    version=__version__,
    description=__doc__,
    author='Pascal Corpet',
    author_email='pascal@bayesimpact.org',
    url='https://github.com/bayesimpact/python-emploi-store',
    download_url='https://github.com/bayesimpact/python-emploi-store/tarball/' + __version__,
    license='The MIT License (MIT)',
    keywords=['Pôle Emploi', 'France', 'emploi', 'OpenData'],
    install_requires=['requests'],
    extras_require={'dev': ['mock', 'nose', 'nose-watch', 'requests-mock']},
    classifiers=[],
)
