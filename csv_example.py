# encoding: utf-8
"""An example script to use emploi_store library.

This downloads a resource from the API as a CSV.

To run it, you will need to set your environment variable:
    EMPLOI_STORE_CLIENT_ID and EMPLOI_STORE_CLIENT_SECRET.
See documentation about accessing the REST API at
https://www.emploi-store-dev.fr/portail-developpeur/donneesdoctechnique
"""
import emploi_store


def main():
    """Download the "Référentiel des familles de métier" from the API."""
    client = emploi_store.Client()
    bmo_package = client.get_package('bmo')
    fap_ref = bmo_package.get_resource(
        name=u'Référentiel des familles de métier')
    fap_ref.to_csv('ref_fap.csv')


if __name__ == '__main__':
    main()
