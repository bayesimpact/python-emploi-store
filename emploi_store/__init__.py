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
import csv
import datetime
import itertools
import json
import os
import sys

import requests

# Byte Order Mark. https://en.wikipedia.org/wiki/Byte_order_mark
_BOM = u'\ufeff'


class Client(object):
    """Client of the Emploi Store API.

    The client uses lazy connection and only send requests when it's needed to
    retrieve data.
    """

    api_url = 'https://api.emploi-store.fr/api/action'

    def __init__(self, client_id=None, client_secret=None):
        if not client_id:
            client_id = os.getenv('EMPLOI_STORE_CLIENT_ID')
            if not client_id:
                raise ValueError('Client needs a client ID')
        if not client_secret:
            client_secret = os.getenv('EMPLOI_STORE_CLIENT_SECRET')
            if not client_secret:
                raise ValueError('Client needs a client secret')
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = None
        self._token_expired = datetime.datetime.now()
        self._cached_packages = None

    def access_token(self, valid_for=datetime.timedelta(seconds=5)):
        """Return an access token valid for the next 5 seconds."""
        if self._access_token:
            next_request_time = datetime.datetime.now() + valid_for
            if next_request_time < self._token_expired:
                return self._access_token

        auth_request = requests.post(
            'https://www.emploi-store-dev.fr/identite/oauth2/access_token',
            data={
                'realm': 'developpeur',
                'grant_type': 'client_credentials',
                'client_id': self._client_id,
                'client_secret': self._client_secret,
            })
        if auth_request.status_code != 200:
            raise ValueError('Client ID or secret invalid')
        response = auth_request.json()
        self._access_token = response.get('access_token')
        expires_in = datetime.timedelta(seconds=response.get('expires_in', 600))
        self._token_expired = datetime.datetime.now() + expires_in
        return self._access_token

    def api_get(self, action, **params):
        """Retrieve JSON information from the API."""
        req = requests.get(
            self.api_url + action, params=params,
            headers={'Authorization': 'Bearer %s' % self.access_token()})
        if req.status_code != 200:
            raise EnvironmentError(
                'HTTP error %d for: \n%s' % (req.status_code, req.url))
        response = req.json()
        if not response.get('success'):
            return None
        return response.get('result')

    def list_packages(self):
        """List all available packages."""
        if self._cached_packages:
            return self._cached_packages
        response = self.api_get('/organization_show', id='digidata')
        packages_json = response.get('packages', [])
        self._cached_packages = dict((p['name'], p) for p in packages_json)
        return self._cached_packages

    def _get_package_id(self, name):
        packages = self.list_packages()
        package = packages[name]
        return package['id']

    def get_package(self, name=None, package_id=None):
        """Get description of a package.

        Existing packages include "imt", "offres", "rome", "bmo", etc.
        """
        if package_id is None:
            if name is None:
                raise ValueError('One of package_id and name must be set')
            package_id = self._get_package_id(name)
        package_json = self.api_get('/package_show', id=package_id)
        return Package(self, **package_json)


class Package(object):
    """A package of resources available.

    On Emploi Store Dev, a package is like a folder on a normal filesystem it
    regroups some datasets that share a logic. For instance the BMO package
    regroups all available datasets for the "Besoin en Main d'Oeuvres", the
    documentation of what it is, the codes that are used, and then one dataset
    for each year.
    """

    def __init__(self, client, name=None, resources=None, **unused_kwargs):
        self._client = client
        self.name = name
        self._resources = resources

    def list_resources(self):
        """List all available resources in package."""
        return [r['name'] for r in self._resources]

    def _get_resource_id(self, name, name_re):
        for res in self._resources:
            if res['name'] == name:
                return res['id']
            if name_re and name_re.match(res['name']):
                return res['id']
        raise ValueError(
            'No resource found in the package that are named "%s" or match '
            'the regular expression "%s". Here are the names available:\n%s'
            % (name, name_re, '\n'.join(self.list_resources())))

    def get_resource(self, name=None, name_re=None, resource_id=None):
        """Get description of a resource.

        Get the description either from its full ID, from its name within its
        package, or the first resouce which name matches a regular expression.
        """
        if resource_id is None:
            if name is None and name_re is None:
                raise ValueError('One of resource_id and name must be set')
            resource_id = self._get_resource_id(name, name_re)
        resource_json = self._client.api_get('/resource_show', id=resource_id)
        return Resource(self._client, **resource_json)


class Resource(object):
    """A resource from the Emploi Store Dev.

    On Emploi Store Dev a resource represents one dataset which is usually
    coming from one unique CSV file. For instance the results of the BMO 2016.
    """

    def __init__(self, client, name=None, **kwargs):
        self._client = client
        self.name = name
        self._id = kwargs.pop('id')

    def _records_batch(
            self, offset=0, batch_size=200, filters=None, fields=None):
        filters_json = json.dumps(filters) if filters else None
        fields_list = ','.join(fields) if fields else None
        res = self._client.api_get(
            '/datastore_search', limit=batch_size, offset=offset, id=self._id,
            filters=filters_json, fields=fields_list)
        return res.get('records')

    def records(self, batch_size=200, filters=None, fields=None):
        """Get all records from resource."""
        offset = 0
        while True:
            batch = self._records_batch(offset, batch_size, filters, fields)
            for record in batch:
                yield record
            if len(batch) != batch_size:
                return
            offset += batch_size

    def to_csv(self, file_name, fieldnames=None, batch_size=200):
        """Write all records to a CSV file.

        If fieldnames isn't set, it will get them from the first record and
        sort them alphabetically.
        """
        records = self.records(batch_size=batch_size)
        need_utf8_encode = sys.version_info < (3, 0)
        if not fieldnames:
            first = next(records)
            records = itertools.chain([first], records)  # pylint: disable=redefined-variable-type
            keys = set(_strip_bom(k) for k in first.keys())
            fieldnames = sorted(keys - set(['_id']))
        if need_utf8_encode:
            fieldnames = [f.encode('utf-8') for f in fieldnames]
        with open(file_name, 'wt') as csvfile:
            csv_writer = csv.DictWriter(
                csvfile, fieldnames, extrasaction='ignore')
            csv_writer.writeheader()
            for record in records:
                record = {_strip_bom(k): v for k, v in record.items()}
                if need_utf8_encode:
                    record = {
                        k.encode('utf-8'): v.encode('utf-8')
                        for k, v in record.items()}
                csv_writer.writerow(record)


def _strip_bom(field):
    if field.startswith(_BOM):
        return field[len(_BOM):]
    return field
