# encoding: utf-8
"""Unit tests for emploi_store module."""
import codecs
import datetime
import itertools
import tempfile
import shutil
import unittest

import emploi_store
import mock
import requests

# TODO: Add more tests.


@mock.patch(emploi_store.__name__ + '.requests')
class ClientTestCase(unittest.TestCase):
    """Unit tests for the Client class."""

    def setUp(self):
        super(ClientTestCase, self).setUp()
        self.client = emploi_store.Client('my-ID', 'my-Secret')

    def test_access_token(self, mock_requests):
        """Test the access_token method."""
        mock_requests.post.return_value = mock.MagicMock()
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {
            "access_token": "foobar",
        }

        token = self.client.access_token(scope='my-scope')

        self.assertEqual(1, mock_requests.post.call_count)
        self.assertEqual(
            'my-ID',
            mock_requests.post.call_args[1]['data']['client_id'])
        self.assertEqual(
            'my-Secret',
            mock_requests.post.call_args[1]['data']['client_secret'])
        self.assertEqual(
            'application_my-ID my-scope',
            mock_requests.post.call_args[1]['data']['scope'])
        self.assertEqual('foobar', token)

    def test_access_fails(self, mock_requests):
        """Test the access_token method."""

        # TODO(marielaure): Use requests_mock package here.
        http_error = requests.exceptions.HTTPError()
        mock_requests.post().raise_for_status.side_effect = http_error

        self.assertRaises(ValueError)

    @mock.patch(emploi_store.__name__ + '.datetime')
    def test_access_token_reuse(self, mock_datetime, mock_requests):
        """Test the access_token just after a token was fetched."""
        mock_requests.post.return_value = mock.MagicMock()
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {
            "access_token": "foobar",
            "expires_in": 500,
        }
        now = datetime.datetime(2016, 3, 11)
        mock_datetime.datetime.now.return_value = now
        mock_datetime.timedelta = datetime.timedelta

        self.client.access_token('my-scope')

        mock_requests.post.reset_mock()
        now += datetime.timedelta(seconds=40)
        mock_datetime.datetime.now.return_value = now

        token = self.client.access_token('my-scope')

        self.assertEqual('foobar', token)
        self.assertFalse(mock_requests.post.called)

    @mock.patch(emploi_store.__name__ + '.datetime')
    def test_access_token_expired(self, mock_datetime, mock_requests):
        """Test the access_token just after a token was fetched."""
        mock_requests.post.return_value = mock.MagicMock()
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {
            "access_token": "foobar",
            "expires_in": 20,
        }
        now = datetime.datetime(2016, 3, 11)
        mock_datetime.datetime.now.return_value = now
        mock_datetime.timedelta = datetime.timedelta

        self.client.access_token('my-scope')

        mock_requests.post.reset_mock()
        now += datetime.timedelta(seconds=40)
        mock_datetime.datetime.now.return_value = now
        mock_requests.post.return_value.json.return_value = {
            "access_token": "second token",
        }

        token = self.client.access_token('my-scope')

        self.assertEqual('second token', token)
        self.assertTrue(mock_requests.post.called)

    def test_get_lbb_companies(self, mock_requests):
        """Test the get_lbb_companies method."""
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {
            "access_token": "foobar",
        }
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.json.return_value = {
            "companies": [
                {"one": 1},
                {"two": 2},
            ],
        }

        companies = self.client.get_lbb_companies(
            45, 2.1, rome_codes=['A1204', 'B1201'])

        self.assertFalse(mock_requests.get.called)

        companies = list(companies)

        self.assertEqual([{"one": 1}, {"two": 2}], companies)

        self.assertTrue(mock_requests.get.called)
        args, kwargs = mock_requests.get.call_args
        self.assertEqual(
            ('https://api.emploi-store.fr/partenaire/labonneboite/v1/company/',),
            args)
        self.assertEqual({'Authorization': 'Bearer foobar'}, kwargs['headers'])
        self.assertEqual(
            {
                'distance': 10,
                'latitude': 45,
                'longitude': 2.1,
                'rome_codes': 'A1204,B1201',
            },
            kwargs['params'])

    def test_get_lbb_companies_by_city_id(self, mock_requests):
        """Test the get_lbb_companies method using a city ID as input."""
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {
            "access_token": "foobar",
        }
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.json.return_value = {
            "companies": [],
        }

        list(self.client.get_lbb_companies(
            city_id='31555', rome_codes=['A1204']))

        self.assertTrue(mock_requests.get.called)
        unused_args, kwargs = mock_requests.get.call_args
        self.assertEqual(
            {
                'distance': 10,
                'commune_id': '31555',
                'rome_codes': 'A1204',
            },
            kwargs['params'])

    def test_get_lbb_companies_missing_location(self, mock_requests):
        """Test the get_lbb_companies method when no location is given."""
        generator = self.client.get_lbb_companies(rome_codes=['A1204'])
        self.assertRaises(ValueError, next, generator)

    def test_get_employment_rate_rank_for_training(self, mock_requests):
        """Test the get_employment_rate_rank_for_training method."""
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {
            "access_token": "foobar",
        }
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.json.return_value = [{
            "formacode": "22435",
            "codeinsee-bassin": "52114",
            "taux-bassin": "",
            "taux-departemental": "",
            "taux-regional": "0.4",
            "taux-national": "0.6",
        }]

        ranking = self.client.get_employment_rate_rank_for_training(
            city_id='69123', formacode='22435')

        self.assertEqual(
            {
                "formacode": "22435",
                "codeinsee-bassin": "52114",
                "taux-bassin": "",
                "taux-departemental": "",
                "taux-regional": "0.4",
                "taux-national": "0.6",
            },
            ranking)

        self.assertTrue(mock_requests.get.called)
        args, kwargs = mock_requests.get.call_args
        self.assertEqual(
            ('https://api.emploi-store.fr/partenaire/retouralemploisuiteformation/v1/rank',),
            args)
        self.assertEqual({'Authorization': 'Bearer foobar'}, kwargs['headers'])
        self.assertEqual(
            {
                'codeinseeville': '69123',
                'formacode': '22435',
            },
            kwargs['params'])

    def test_get_match_via_soft_skills(self, mock_requests):
        """Test the match_via_soft_skills method."""
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {
            "access_token": "foobar",
        }
        mock_requests.post.return_value.status_code = 201
        mock_requests.post.return_value.json.return_value = {
            "uuid": 'something',
            "code": "A1204",
            "create_at": 'a date and time',
            "skills": {
                "soft_skill_1": {"score": 1},
                "soft_skill_2": {"score" : 2},
            },
        }

        skills = self.client.get_match_via_soft_skills('A1204')

        self.assertFalse(mock_requests.get.called)

        skills = list(skills)

        self.assertEqual([{"score": 1}, {"score": 2}], sorted(skills, key=lambda s: s["score"]))

        self.assertTrue(mock_requests.post.called)
        args, kwargs = mock_requests.post.call_args
        self.assertEqual((
            'https://api.emploi-store.fr/partenaire/matchviasoftskills/v1/professions/job_skills',),
            args)
        self.assertEqual({'code': 'A1204'}, kwargs['params'])

    def test_la_bonne_alternance(self, mock_requests):
        """Test the get_lbb_companies method to access data from La Bonne Alternance."""
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {
            "access_token": "foobar",
        }
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.json.return_value = {
            "companies": [
                {"one": 1},
                {"two": 2},
            ],
        }

        companies = self.client.get_lbb_companies(
            45, 2.1, rome_codes=['A1204', 'B1201'], contract='alternance')

        self.assertFalse(mock_requests.get.called)

        companies = list(companies)

        self.assertEqual([{"one": 1}, {"two": 2}], companies)

        self.assertTrue(mock_requests.get.called)
        args, kwargs = mock_requests.get.call_args
        self.assertEqual(
            ('https://api.emploi-store.fr/partenaire/labonneboite/v1/company/',),
            args)
        self.assertEqual({'Authorization': 'Bearer foobar'}, kwargs['headers'])
        self.assertEqual(
            {
                'distance': 10,
                'latitude': 45,
                'longitude': 2.1,
                'rome_codes': 'A1204,B1201',
                'contract': 'alternance',
            },
            kwargs['params'])

    def test_list_emploistore_services(self, mock_requests):
        """Test the list_emploistore_services method."""
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {
            "access_token": "foobar",
        }
        mock_requests.get.return_value.json.return_value = [
            {
                "identifiantService": "bobEmploi",
                "nomService": "Bob",
                "typeService": "coaching",
            },
            {
                "identifiantService": "laBonneBoite",
                "nomService": "La Bonne Boite",
                "typeService": "Moteur de recherche",
            },
        ]

        services = self.client.list_emploistore_services()

        self.assertEqual(
            ['Bob', 'La Bonne Boite'],
            [service.get('nomService') for service in services])
        self.assertTrue(mock_requests.get_called)
        args, kwargs = mock_requests.get.call_args
        self.assertEqual(
            ('https://api.emploi-store.fr/partenaire/cataloguedesservicesemploistore/'
             'v1/api-emploistore/fichesservices',),
            args)
        self.assertEqual({'headers': {'Authorization': 'Bearer foobar'}}, kwargs)

    def test_describe_emploistore_service(self, mock_requests):
        """Test the describe_emploistore_service method."""
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {
            "access_token": "foobar",
        }
        mock_requests.get.return_value.json.return_value = {
            "ficheService": {
                "identifiantService": "bobEmploi",
                "nomService": "Bob",
                "typeService": "coaching",
            },
        }

        service = self.client.describe_emploistore_service('bobEmploi')

        self.assertEqual('Bob', service.get('ficheService', {}).get('nomService'))
        self.assertTrue(mock_requests.get_called)
        args, kwargs = mock_requests.get.call_args
        self.assertEqual(
            ('https://api.emploi-store.fr/partenaire/cataloguedesservicesemploistore/'
             'v1/api-emploistore/fichesservices/bobEmploi/false',),
            args)
        self.assertEqual({'headers': {'Authorization': 'Bearer foobar'}}, kwargs)

    def test_list_online_events(self, mock_requests):
        """Test the list_online_events method."""
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {
            'access_token': 'foobar',
        }
        mock_requests.get.return_value.json.return_value = [
            {
                'titre': 'Recrutement ADMR',
                'nombreOffres': 4,
            },
            {
                'titre': 'la transition écologique: rejoignez HITECH !',
                'nombreOffres': 2,
            },
        ]

        events = self.client.list_online_events()

        self.assertEqual(
            ['Recrutement ADMR', 'la transition écologique: rejoignez HITECH !'],
            [event.get('titre') for event in events])
        self.assertTrue(mock_requests.get_called)
        args, kwargs = mock_requests.get.call_args
        self.assertEqual(
            ('https://api.emploi-store.fr/partenaire/evenements/v1/salonsenligne',),
            args)
        self.assertEqual({'headers': {
            'Accept': 'application/json',
            'Authorization': 'Bearer foobar',
        }}, kwargs)


@mock.patch(emploi_store.__name__ + '.requests')
class PackageTest(unittest.TestCase):
    """Unit tests for the Package class."""

    def setUp(self):
        super(PackageTest, self).setUp()
        self._client = emploi_store.Client('my-ID', 'my-Secret')

    def test_get_resource_newer_version(self, mock_requests):
        """Test the get_resource method with a specific pe_version."""
        self.package = emploi_store.Package(
            self._client, name='BMO', resources=[
                {'name': 'BMO 2013', 'id': 'bmo-2013-1', 'pe_version': '1'},
                {'name': 'BMO 2013', 'id': 'bmo-2013-2', 'pe_version': '2'},
            ])
        _setup_mock_requests(mock_requests, {
            'success': True,
            'result': {
                'id': 'downloaded-id',
                'name': 'Downloaded BMO',
            },
        })

        res = self.package.get_resource(name='BMO 2013', pe_version='2')
        self.assertEqual('Downloaded BMO', res.name)

        mock_requests.get.assert_called_once()
        id_requested = mock_requests.get.call_args[1]['params'].get('id')
        self.assertEqual('bmo-2013-2', id_requested)


@mock.patch(emploi_store.__name__ + '.requests')
class ResourceTest(unittest.TestCase):
    """Unit tests for the Resource class."""

    def setUp(self):
        super(ResourceTest, self).setUp()
        _client = emploi_store.Client('my-ID', 'my-Secret')
        self.res = emploi_store.Resource(
            _client, name='BMO 2016', id='1234-abc')
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        super(ResourceTest, self).tearDown()
        shutil.rmtree(self.tmpdir)

    def test_to_csv(self, mock_requests):
        """Test the to_csv method."""
        _setup_mock_requests(mock_requests, {
            'success': True,
            'result': {
                'records': [
                    {'CODE': '123', 'NAME': 'First'},
                    {'CODE': '456', 'NAME': 'Second'},
                ],
            },
        })
        filename = self.tmpdir + '/bmo_2016.csv'

        self.res.to_csv(filename)

        with open(filename) as csv_file:
            csv_content = csv_file.read().replace('\r\n', '\n')
        self.assertEqual("""CODE,NAME
123,First
456,Second
""", csv_content)

    def test_to_csv_number(self, mock_requests):
        """Test the to_csv method when resource returns numbers directly."""
        _setup_mock_requests(mock_requests, {
            'success': True,
            'result': {
                'records': [
                    {'CODE': 123, 'NAME': 'First'},
                    {'CODE': 456, 'NAME': 'Second'},
                ],
            },
        })
        filename = self.tmpdir + '/bmo_2016.csv'

        self.res.to_csv(filename)

        with open(filename) as csv_file:
            csv_content = csv_file.read().replace('\r\n', '\n')
        self.assertEqual("""CODE,NAME
123,First
456,Second
""", csv_content)

    def test_to_csv_utf8(self, mock_requests):
        """Test the to_csv method when resource has Unicode chars."""
        _setup_mock_requests(mock_requests, {
            'success': True,
            'result': {
                'records': [
                    {u'CÖDE': '123', 'NAME': u'Fïrst'},
                    {u'CÖDE': '456', 'NAME': u'Ségond'},
                ],
            },
        })
        filename = self.tmpdir + '/bmo_2016.csv'

        self.res.to_csv(filename)

        with codecs.open(filename, 'r', 'utf-8') as csv_file:
            csv_content = csv_file.read().replace('\r\n', '\n')
        self.assertEqual(u"""CÖDE,NAME
123,Fïrst
456,Ségond
""", csv_content)

    def test_to_csv_utf8_with_bom(self, mock_requests):
        """Test the to_csv method when resource has the BOM bug."""
        _setup_mock_requests(mock_requests, {
            'success': True,
            'result': {
                'records': [
                    {u'\ufeffCÖDE': '123', 'NAME': u'Fïrst'},
                    {u'\ufeffCÖDE': '456', 'NAME': u'Ségond'},
                ],
            },
        })
        filename = self.tmpdir + '/bmo_2016.csv'

        self.res.to_csv(filename)

        with codecs.open(filename, 'r', 'utf-8') as csv_file:
            csv_content = csv_file.read().replace('\r\n', '\n')
        self.assertEqual(u"""CÖDE,NAME
123,Fïrst
456,Ségond
""", csv_content)

    def test_to_csv_iterator(self, mock_requests):
        """Test the iterator arg of the to_csv method."""
        _setup_mock_requests(mock_requests, {
            'success': True,
            'result': {
                'records': [
                    {'CODE': '1', 'NAME': 'First'},
                    {'CODE': '2', 'NAME': 'Second'},
                    {'CODE': '3', 'NAME': 'Third'},
                    {'CODE': '4', 'NAME': 'Fourth'},
                ],
            },
        })
        filename = self.tmpdir + '/bmo_2016.csv'

        self.res.to_csv(filename, iterator=lambda r: itertools.islice(r, 0, None, 2))

        with open(filename) as csv_file:
            csv_content = csv_file.read().replace('\r\n', '\n')
        self.assertEqual("""CODE,NAME
1,First
3,Third
""", csv_content)

    def test_num_records(self, mock_requests):
        """Test the length of the records method."""
        _setup_mock_requests(mock_requests, {
            'success': True,
            'result': {
                'total': 42429,
                'records': [{'id': 'hello'}],
            },
        })

        records = self.res.records()
        self.assertEqual(42429, len(records))
        self.assertEqual([{'id': 'hello'}], list(records))

        self.assertEqual(1, mock_requests.get.call_count)

    def test_to_csv_iterator_using_num_records(self, mock_requests):
        """Test the iterator arg of the to_csv method."""
        _setup_mock_requests(mock_requests, {
            'success': True,
            'result': {
                'records': [
                    {'CODE': '1', 'NAME': 'First'},
                    {'CODE': '2', 'NAME': 'Second'},
                    {'CODE': '3', 'NAME': 'Third'},
                ],
                'total': 201,
            },
        })
        filename = self.tmpdir + '/bmo_2016.csv'

        def _update_records(records):
            num_records = len(records)
            for index, record in enumerate(records):
                yield dict(record, CODE='{} {}/{}'.format(record['CODE'], index + 1, num_records))

        self.res.to_csv(filename, iterator=_update_records)

        with open(filename) as csv_file:
            csv_content = csv_file.read().replace('\r\n', '\n')
        self.assertEqual("""CODE,NAME
1 1/201,First
2 2/201,Second
3 3/201,Third
""", csv_content)


def _setup_mock_requests(
        mock_requests, get_json, post_json=None):
    if post_json is None:
        post_json = {'access_token': 'foobar'}
    mock_requests.post.return_value = mock.MagicMock()
    mock_requests.post.return_value.status_code = 200
    mock_requests.post.return_value.json.return_value = post_json

    mock_requests.get.return_value = mock.MagicMock()
    mock_requests.get.return_value.status_code = 200
    mock_requests.get.return_value.json.return_value = get_json


if __name__ == '__main__':
    unittest.main()
