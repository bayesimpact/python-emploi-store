# encoding: utf-8
"""Python client library for Pôle Emploi's "Emploi Store Dev"."""
from distutils import core

__version__ = '0.1.1'

core.setup(
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
    classifiers=[],
)
