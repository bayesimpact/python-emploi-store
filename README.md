[Emploi Store Dev](https://www.emploi-store-dev.fr/) is a platform setup by
Pôle Emploi, the French unemployment agency, to share their public data.

This is a Python client library for their API. 

The library is in `emploi_store` and works both in Python 2 and Python 3.
Usage information and required environment variables is documented in the
library's docstring.

Examples on how to use it is are in:

* `example.py` for a server using multiple calls to the API.
* `csv_example.py` for a simpele download of a CSV from the API.

## Installation

The library is released on
[PyPi](https://pypi.python.org/pypi/python-emploi-store) thus can be installed
with pip:

```sh
pip install python-emploi-store
```

That's all, then you just need to use:

```py
import emploi_store
```

in your code.

## API Key

This client library doesn't provide direct access to the data. To use it, you
need to get a client ID and client secret from Emploi Store Dev.

As documented on their
[website](https://www.emploi-store-dev.fr/portail-developpeur/donneesdoctechnique) you need to:

* [Sign-in](https://www.emploi-store-dev.fr/portail-developpeur/donneesdoctechnique:connexion) or [create a new account](https://www.emploi-store-dev.fr/portail-developpeur/creationutilisateur)
* Go to your [dashboard](https://www.emploi-store-dev.fr/portail-developpeur/tableaudebord)
* Add an application and agree to the terms of use
* Subscribe to the [Infotravail v1 API](https://www.emploi-store-dev.fr/portail-developpeur/detailapicatalogue/-infotravail-v1?id=57909ba23b2b8d019ee6cc5e) by clicking `DEMANDE D'ACCÈS` and selecting your application.
* The client ID and secret are then available as `Identifiant` and `Clé secrète`

For more information about the Pole-Emploi API subscription, [read its documentation](https://www.emploi-store-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/souscrire-api.html).


## Development

If you want to contribute, make sure to send us a Pull Request with tests. To
setup a test environment we generally use Docker to isolate the tests.

* In a terminal, start a container and set the dev environment. Note that you
  need one environment for Python 2 and another for Python 3. You can have
  several ran in parallel if needed.

```sh
docker run --rm -it -v $(pwd):/work/:ro -w /work/ python:3 bash
pip install .[dev]
```

* Run the tests, and automatically re-run them when files are changed:

```sh
nosetests --with-watch
```

* Now you can edit the files and monitor the terminal.

* To stop watching the tests, hit Ctrl-C in the terminal. Then to exit the
  Docker container, hit Ctrl-D.

## Release

To release a new version of the library:

* Make sure the [Changelog](./CHANGELOG.md) file is up to date.
* Update the version number in [setup.py](./setup.py).
* Tag the code with git.
* Build and upload the package to [PyPi](https://pypi.org/project/python-emploi-store/):

```sh
python setup.py sdist upload
```
