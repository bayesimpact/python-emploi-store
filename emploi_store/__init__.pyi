"""Module to help access data from Emploi Store Dev.

Emploi Store Dev (https://www.emploi-store-dev.fr/) is a platform setup by Pole
Emploi to share public data.

Usage example:

First set up your Client ID and secret in the following env variables:
EMPLOI_STORE_CLIENT_ID and EMPLOI_STORE_CLIENT_SECRET. To get them, see
documentation at
https://www.emploi-store-dev.fr/portail-developpeur/donneesdoctechnique

Then in a python interpreter, script or notebook:
```
import emploi_store

# Create a client for the Emploi Store API.
client = emploi_store.Client()

# Get the BMO package.
bmo_package = client.get_package('bmo')

# Retrieve the reference to the BMO for 2014.
bmo_2014 = bmo_package.get_resource(name='Résultats enquête BMO 2014')

# Download the full BMO 2014 as a CSV file.
bmo_2014.to_csv('data/bmo_2014.csv')
```
"""

import datetime
import typing

A = typing.TypeVar('A')


class Resource(object):
    """A resource from the Emploi Store Dev.

    On Emploi Store Dev a resource represents one dataset which is usually
    coming from one unique CSV file. For instance the results of the BMO 2016.
    """

    def __init__(
            self,
            client: 'Client',
            name: typing.Optional[str] = None,
            **kwargs: typing.Any) -> None:
        ...

    def records(
            self,
            batch_size: int = 200,
            filters: typing.Optional[typing.Dict[str, typing.Any]] = None,
            fields: typing.Optional[typing.Iterable[str]] = None) -> typing.Iterator:
        """Get all records from resource."""

        ...

    def to_csv(
            self,
            file_name: str,
            fieldnames: typing.Optional[typing.List[str]] = None,
            batch_size: int = 200,
            filters: typing.Optional[typing.Dict[str, typing.Any]] = None,
            iterator: typing.Optional[typing.Callable[..., typing.Iterator]] = None
    ) -> None:
        """Write all records to a CSV file.

        Args:
            file_name: the path to the CSV file to create.
            fieldnames: the list of fields to save. If not set, it will get
                them from the first record and sort them alphabetically.
            batch_size: the size of the batch of records to download.
            filters: optional filters not to ask the whole resource.
            iterator: a wrapper around the iterator on records, so that you can
                modify the records or just keep track of progress.
        """

        ...


class Package(object):
    """A package of resources available.

    On Emploi Store Dev, a package is like a folder on a normal filesystem it
    regroups some datasets that share a logic. For instance the BMO package
    regroups all available datasets for the "Besoin en Main d'Oeuvres", the
    documentation of what it is, the codes that are used, and then one dataset
    for each year.
    """

    def __init__(
            self,
            client: 'Client',
            name: typing.Optional[str] = None,
            resources: typing.Optional[typing.List[typing.Dict[str, typing.Any]]] = None,
            **unused_kwargs: typing.Any) -> None:
        ...

    def list_resources(self) -> typing.List[str]:
        """List all available resources in package."""

        ...

    def get_resource(
            self,
            name: typing.Optional[str] = None,
            name_re: typing.Optional[typing.Pattern] = None,
            resource_id: typing.Optional[str] = None,
            pe_version: typing.Optional[str] = None) -> Resource:
        """Get description of a resource.

        Get the description either from its full ID, from its name within its
        package, or the first resouce which name matches a regular expression.
        """

        ...


class Client(object):
    """Client of the Emploi Store API.

    The client uses lazy connection and only send requests when it's needed to
    retrieve data.
    """

    def __init__(
            self,
            client_id: typing.Optional[str] = None,
            client_secret: typing.Optional[str] = None) -> None:
        ...

    def access_token(
            self,
            scope: str,
            valid_for: datetime.timedelta = datetime.timedelta(seconds=5)) -> typing.Optional[str]:
        """Return an access token valid for the next 5 seconds."""

        ...

    def api_get(self, action: str, **params: typing.Optional[typing.Union[str, int]]) \
            -> typing.Optional[typing.Dict[str, typing.Any]]:
        """Retrieve JSON information from the API."""

        ...

    def list_packages(self) -> typing.Dict[str, typing.Dict[str, typing.Any]]:
        """List all available packages."""

        ...

    def get_package(
            self,
            name: typing.Optional[str] = None,
            package_id: typing.Optional[str] = None) -> Package:
        """Get description of a package.

        Existing packages include "imt", "offres", "rome", "bmo", etc.
        """

        ...

    def get_lbb_companies(
            self,
            latitude: typing.Optional[float] = None,
            longitude: typing.Optional[float] = None,
            distance: float = 10,
            rome_codes: typing.Optional[typing.List[str]] = None,
            naf_codes: typing.Optional[typing.List[str]] = None,
            city_id: typing.Optional[str] = None,
            contract: typing.Optional[str] = None) -> typing.Iterator[typing.Dict[str, str]]:
        """Get a list of hiring companies from La Bonne Boite API.

        See documentation at:
            https://www.emploi-store-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/api-la-bonne-boite-v1.html

        Args:
            latitude: the latitude of the point near which to search for
                companies.
            longitude: the longitude of the point near which to search for
                companies.
            distance: the maximum distance (in km) to search for companies.
            rome_codes: a list of ROME IDs defining job groups in which
                companies should hire.
            naf_codes: a list of NAF codes defining the activity sector of the
                companies.
            city_id: the INSEE code of the city to use as starting point for
                the search.
            contract: type of contract that the companies are most likely to
                propose: "dpae" (Déclaration Préalable À l'Embauche, i.e. actual
                hiring), or "alternance" (half-time job, with another half-time
                studying). The default (None) is equivalent to "dpae".
        Yields:
            a dict per company, see
            https://www.emploi-store-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/api-la-bonne-boite-v1.html
            for details of the fields.
        """

        ...

    def get_employment_rate_rank_for_training(self, formacode: str, city_id: str) \
            -> typing.Dict[str, typing.Union[str, float]]:
        """Get the ranking of the employment rate for trainings.

        See documentation at:
            https://www.emploi-store-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/api-retouralemploiformation-v1.html

        Args:
            formacode: unique ID for the domain of the training. See
                http://formacode.centre-inffo.fr
            city_id: the INSEE code of the city where the training takes place.

        Returns:
            a dict, see
            https://www.emploi-store-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/api/api-retouralemploiformation-v1.html
            for details of the fields.
        """

        ...

    def get_match_via_soft_skills(self, rome: str) -> typing.Iterator[typing.Dict[str, typing.Any]]:
        """Get the soft skills for a specific job group sorted by significance.

        See documentation at:
            https://www.emploi-store-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/api-matchviasoftskills-v1.html

        Args:
            rome: unique ID for the job group. See
                https://www.pole-emploi.fr/candidat/le-code-rome-et-les-fiches-metiers-@/article.jspz?id=60702

        Yields:
            a dict per skill, see
            https://www.emploi-store-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/api/api-matchviasoftskills-v1.html
            for details of the fields.
        """

        ...

    def list_emploistore_services(self) -> typing.Dict[str, typing.Any]:
        """List all the user-facing services proposed by the Emploi Store.

        See the user-facing website at:
            https://www.emploi-store.fr/portail/accueil

        Returns:
            a list of dicts, see
            https://www.emploi-store-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/api-catalogueemploistore-v1/recuperer-les-services.html
            for details of the fields. It includes "identifiantService" that
            you can use for describe_emploistore_service.
        """

        ...

    def describe_emploistore_service(
            self,
            service_id: str,
            should_get_images: bool = False) -> typing.Dict[str, typing.Any]:
        """Describe one of the service of the Emploi Store.

        See the user-facing website at:
            https://www.emploi-store.fr/portail/accueil

        Args:
            service_id: the unique ID of the service to describe, see the
                result of list_emploistore_services. It's also the last par of
                the URL on the Emploi Store website: e.g.
                https://www.emploi-store.fr/portail/services/sInformerSurLAlternance
            should_get_images: whether to retrieve related images (logo,
                screenshots, etc.). If True, the response will have a field
                ressourcesFicheService containing the imags base64 encoded.

        Returns:
            a list of dicts, see
            https://www.emploi-store-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/api-catalogueemploistore-v1/consulter-un-service.html
            for details of the fields.
        """

        ...

    def list_online_events(self) -> typing.Dict[str, typing.Any]:
        """List online events "salons en ligne".

        Returns:
            a list of dicts, see
            https://www.emploi-store-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/api-evenements-pole-emploi-v1/rechercher-les-salons-en-ligne.html
            for details of the fields.
        """

        ...
