# encoding: utf-8
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

import collections
import csv
import datetime
import json
import os
import sys
import typing

import requests

# Byte Order Mark. https://en.wikipedia.org/wiki/Byte_order_mark
_BOM = u'\ufeff'


class _Token(typing.NamedTuple):
    expired_at: datetime.datetime
    value: typing.Optional[str]


def _strip_bom(field: str) -> str:
    if field.startswith(_BOM):
        return field[len(_BOM):]
    return field


A = typing.TypeVar('A')


class _ResourceIterator(typing.Iterator[A]):

    def __init__(
            self,
            get_batch: typing.Callable[[int], typing.Tuple[int, typing.List[A]]],
            batch_size: int) -> None:
        self._get_batch = get_batch
        self._batch_size = batch_size

        self._offset = 0
        self._generator = self._create_generator()

        self._num_records = 0
        self._first_batch: typing.Optional[typing.List[A]] = None

    def _ensure_first_batch(self) -> typing.Tuple[int, typing.List[A]]:
        if self._first_batch is None:
            self._num_records, self._first_batch = self._get_batch(0)
        return self._num_records, self._first_batch

    def __iter__(self) -> typing.Iterator[A]:
        return self

    def __next__(self) -> A:
        return next(self._generator)

    # For Python 2 compatibility.
    def next(self) -> A:
        return next(self._generator)

    def _create_generator(self) -> typing.Iterator[A]:
        offset = 0
        while True:
            if offset == 0:
                _, batch = self._ensure_first_batch()
            else:
                _, batch = self._get_batch(offset)
            yield from batch
            if len(batch) != self._batch_size:
                return
            offset += self._batch_size

    def __len__(self) -> int:
        self._ensure_first_batch()
        return self._num_records

    def peek_first(self) -> typing.Any:
        """Peek on the first record without consuming it."""
        _, first_batch = self._ensure_first_batch()
        return first_batch[0]


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
        self._client = client
        self.name = name
        self._id = kwargs.pop('id')

    def _records_batch(
            self,
            offset: int = 0,
            batch_size: int = 200,
            filters: typing.Optional[typing.Dict[str, typing.Any]] = None,
            fields: typing.Optional[typing.Iterable[str]] = None
        ) -> typing.Tuple[int, typing.List]:
        filters_json = json.dumps(filters) if filters else None
        fields_list = ','.join(fields) if fields else None
        res = self._client.api_get(
            '/datastore_search', limit=batch_size, offset=offset, id=self._id,
            filters=filters_json, fields=fields_list)
        if res is None:
            return 0, []
        return res.get('total', 0), res.get('records', [])

    def records(
            self,
            batch_size: int = 200,
            filters: typing.Optional[typing.Dict[str, typing.Any]] = None,
            fields: typing.Optional[typing.Iterable[str]] = None) -> _ResourceIterator:
        """Get all records from resource."""

        return _ResourceIterator(
            lambda offset: self._records_batch(offset, batch_size, filters, fields),
            batch_size)

    def to_csv(
            self,
            file_name: str,
            fieldnames: typing.Optional[typing.List[str]] = None,
            batch_size: int = 200,
            filters: typing.Optional[typing.Dict[str, typing.Any]] = None,
            iterator:
                typing.Optional[typing.Callable[[_ResourceIterator], typing.Iterator]] = None
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
        records = self.records(batch_size=batch_size, filters=filters)
        need_utf8_encode = sys.version_info < (3, 0)
        if not fieldnames:
            first = records.peek_first()
            keys = set(_strip_bom(k) for k in first.keys())
            fieldnames = sorted(keys - set(['_id']))
        if need_utf8_encode:
            fieldnames = [f.encode('utf-8') for f in fieldnames]  # type: ignore
        with open(file_name, 'wt') as csvfile:
            csv_writer = csv.DictWriter(
                csvfile, fieldnames, extrasaction='ignore')
            csv_writer.writeheader()
            for record in iterator(records) if iterator else records:
                record = {_strip_bom(k): v for k, v in record.items()}
                if need_utf8_encode:
                    record = {
                        k.encode('utf-8'): unicode(v).encode('utf-8')  # type: ignore
                        for k, v in record.items()}
                csv_writer.writerow(record)


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
        self._client = client
        self.name = name
        self._resources = resources

    def list_resources(self) -> typing.List[str]:
        """List all available resources in package."""
        return [r['name'] for r in self._resources or []]

    def _get_resource_id(
        self,
        name: typing.Optional[str],
        name_re: typing.Optional[typing.Pattern],
        pe_version: typing.Optional[str] = None) -> str:
        for res in self._resources or []:
            is_good_version = \
                pe_version is None or pe_version == res.get('pe_version')
            if res['name'] == name and is_good_version:
                return typing.cast(str, res['id'])
            if name_re and name_re.match(res['name']) and is_good_version:
                return typing.cast(str, res['id'])
        raise ValueError(
            'No resource found in the package that are named "%s" or match '
            'the regular expression "%s". Here are the names available:\n%s'
            % (name, name_re, '\n'.join(self.list_resources())))

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
        if resource_id is None:
            if name is None and name_re is None:
                raise ValueError('One of resource_id and name must be set')
            resource_id = self._get_resource_id(name, name_re, pe_version=pe_version)
        resource_json = self._client.api_get('/resource_show', id=resource_id) or {}
        return Resource(self._client, **resource_json)


class Client(object):
    """Client of the Emploi Store API.

    The client uses lazy connection and only send requests when it's needed to
    retrieve data.
    """

    api_url = 'https://api.emploi-store.fr/partenaire'

    def __init__(
            self,
            client_id: typing.Optional[str] = None,
            client_secret: typing.Optional[str] = None) -> None:
        if not client_id:
            client_id = os.getenv('EMPLOI_STORE_CLIENT_ID')
            if not client_id:
                raise ValueError('Client needs a client ID')
        if not client_secret:
            client_secret = os.getenv('EMPLOI_STORE_CLIENT_SECRET')
            if not client_secret:
                raise ValueError('Client needs a client secret')
        self._client_id: str = client_id
        self._client_secret: str = client_secret
        self._access_tokens: typing.Dict[str, _Token] = {}
        self._cached_packages: typing.Optional[typing.Dict[str, typing.Dict[str, typing.Any]]] = \
            None

    def access_token(
            self,
            scope: str,
            valid_for: datetime.timedelta = datetime.timedelta(seconds=5)) -> typing.Optional[str]:
        """Return an access token valid for the next 5 seconds."""

        if scope in self._access_tokens:
            cached_token = self._access_tokens[scope]
            next_request_time = datetime.datetime.now() + valid_for
            if next_request_time < cached_token.expired_at:
                return cached_token.value

        auth_request = requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token',
            data={
                'realm': '/partenaire',
                'grant_type': 'client_credentials',
                'client_id': self._client_id,
                'client_secret': self._client_secret,
                'scope': 'application_%s %s' % (self._client_id, scope),
            })
        try:
            auth_request.raise_for_status()
        except Exception as error:
            raise ValueError('Autentication failed: {}'.format(error))

        response = auth_request.json()
        token = typing.cast(typing.Optional[str], response.get('access_token'))
        expires_in = datetime.timedelta(seconds=response.get('expires_in', 600))
        self._access_tokens[scope] = _Token(
            value=token, expired_at=datetime.datetime.now() + expires_in)
        return token

    def api_get(self, action: str, **params: typing.Optional[typing.Union[str, int]]) \
            -> typing.Optional[typing.Dict[str, typing.Any]]:
        """Retrieve JSON information from the API."""

        scope = 'api_infotravailv1'
        req = requests.get(  # type: ignore
            self.api_url + '/infotravail/v1' + action, params=params,
            headers={'Authorization': 'Bearer %s' % self.access_token(scope)})
        req.raise_for_status()
        response = req.json()
        if not response.get('success'):
            return None
        return typing.cast(typing.Optional[typing.Dict[str, typing.Any]], response.get('result'))

    def list_packages(self) -> typing.Dict[str, typing.Dict[str, typing.Any]]:
        """List all available packages."""

        if self._cached_packages:
            return self._cached_packages
        response = self.api_get('/organization_show', id='digidata')
        packages_json = typing.cast(
            typing.List[typing.Dict[str, typing.Any]],
            response.get('packages', [])) if response else []
        self._cached_packages = dict((typing.cast(str, p['name']), p) for p in packages_json)
        return self._cached_packages

    def _get_package_id(self, name: str) -> str:
        packages = self.list_packages()
        package = packages[name]
        return typing.cast(str, package['id'])

    def get_package(
            self,
            name: typing.Optional[str] = None,
            package_id: typing.Optional[str] = None) -> Package:
        """Get description of a package.

        Existing packages include "imt", "offres", "rome", "bmo", etc.
        """
        if package_id is None:
            if name is None:
                raise ValueError('One of package_id and name must be set')
            package_id = self._get_package_id(name)
        package_json = self.api_get('/package_show', id=package_id) or {}
        return Package(self, **package_json)

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

        params: typing.Dict[str, typing.Union[str, float]] = {
            'distance': distance,
        }
        if city_id:
            params['commune_id'] = city_id
        elif latitude is None or longitude is None:
            raise ValueError(
                'One of city_id or (latitude, longitude) argument is required')
        else:
            params['latitude'] = latitude
            params['longitude'] = longitude
        if rome_codes:
            params['rome_codes'] = ','.join(rome_codes)
        if naf_codes:
            params['naf_codes'] = ','.join(naf_codes)
        if contract:
            params['contract'] = contract
        scope = 'api_labonneboitev1'
        req = requests.get(
            self.api_url + '/labonneboite/v1/company/', params=params,
            headers={'Authorization': 'Bearer %s' % self.access_token(scope)})
        req.raise_for_status()
        response = req.json()
        companies = response.get('companies')
        if companies:
            yield from companies

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

        scope = 'api_retouralemploisuiteformationv1'
        req = requests.get(
            self.api_url + '/retouralemploisuiteformation/v1/rank',
            params={'formacode': formacode, 'codeinseeville': city_id},
            headers={'Authorization': 'Bearer %s' % self.access_token(scope)})
        req.raise_for_status()
        response = req.json()
        return typing.cast(typing.Dict[str, typing.Union[str, float]], response[0])

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
        scope = 'api_matchviasoftskillsv1'
        req = requests.post(
            self.api_url + '/matchviasoftskills/v1/professions/job_skills',
            params={'code': rome},
            headers={'Authorization': 'Bearer %s' % self.access_token(scope)})
        req.raise_for_status()
        response = req.json(object_pairs_hook=collections.OrderedDict)
        skills = typing.cast(
            typing.Optional[typing.Dict[str, typing.Dict[str, typing.Any]]],
            response.get('skills'))
        if skills:
            yield from skills.values()

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
        scope = 'api_cataloguedesservicesemploistorev1 emploistoreusagers'
        req = requests.get(
            self.api_url + '/cataloguedesservicesemploistore/v1/api-emploistore/fichesservices',
            headers={'Authorization': 'Bearer %s' % self.access_token(scope)})
        req.raise_for_status()
        return typing.cast(typing.Dict[str, typing.Any], req.json())

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
        scope = 'api_cataloguedesservicesemploistorev1 emploistoreusagers'
        req = requests.get(
            self.api_url +
            '/cataloguedesservicesemploistore/v1/api-emploistore/fichesservices/%s/%s'
            % (service_id, 'true' if should_get_images else 'false'),
            headers={'Authorization': 'Bearer %s' % self.access_token(scope)})
        req.raise_for_status()
        return typing.cast(typing.Dict[str, typing.Any], req.json())

    def list_online_events(self) -> typing.Dict[str, typing.Any]:
        """List online events "salons en ligne".

        Returns:
            a list of dicts, see
            https://www.emploi-store-dev.fr/portail-developpeur-cms/home/catalogue-des-api/documentation-des-api/api-evenements-pole-emploi-v1/rechercher-les-salons-en-ligne.html
            for details of the fields.
        """
        scope = 'api_evenementsv1 evenements'
        req = requests.get(
            self.api_url + '/evenements/v1/salonsenligne',
            headers={
                'Accept': 'application/json',
                'Authorization': 'Bearer %s' % self.access_token(scope),
            })
        req.raise_for_status()
        return typing.cast(typing.Dict[str, typing.Any], req.json())
