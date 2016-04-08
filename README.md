[Emploi Store Dev](https://www.emploi-store-dev.fr/) is a platform setup by
Pôle Emploi, the French unemployment agency, to share their public data.

This is a Python client library for their API. 

The library is in `emploi_store` and works both in Python 2 and Python 3.
Usage information and required environment variables is documented in the
library's docstring.

An example on how to use it is in `example.py`.

## API Key

This client library doesn't provide direct access to the data. To use it, you
need to get a client ID and client secret from Emploi Store Dev.

As documented on their
[website](https://www.emploi-store-dev.fr/portail-developpeur/donneesdoctechnique) you need to:

* [Sign-in](https://www.emploi-store-dev.fr/portail-developpeur/donneesdoctechnique:connexion) or [create a new account](https://www.emploi-store-dev.fr/portail-developpeur/creationutilisateur)
* Go to your [dashboard](https://www.emploi-store-dev.fr/portail-developpeur/tableaudebord)
* Add an application, check `Oui` to the question `Utilisation de l’API Pôle
  emploi` and agree to the terms of use
* The client ID and secret are then available as `Identifiant client` and `Clé secrète`
