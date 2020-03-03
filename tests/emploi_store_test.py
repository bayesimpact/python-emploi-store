# encoding: utf-8
"""Unit tests for emploi_store module."""

import codecs
import datetime
import itertools
import tempfile
import shutil
import unittest

import mock
import requests_mock

import emploi_store

# TODO: Add more tests.


@requests_mock.Mocker()
class ClientTestCase(unittest.TestCase):
    """Unit tests for the Client class."""

    def setUp(self):
        super(ClientTestCase, self).setUp()
        self.client = emploi_store.Client('my-ID', 'my-Secret')

    def test_access_token(self, mock_requests):
        """Test the access_token method."""

        def _match_request_data(request):
            data = (request.text or '').split('&')
            return 'client_id=my-ID' in data and \
                'client_secret=my-Secret' in data and \
                'scope=application_my-ID+my-scope' in data

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            additional_matcher=_match_request_data,
            json={'access_token': 'foobar'})

        token = self.client.access_token(scope='my-scope')
        self.assertEqual('foobar', token)

    def test_access_fails(self, mock_requests):
        """Test the access_token method."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            status_code=401)

        with self.assertRaises(ValueError):
            self.client.access_token(scope='my-scope')

    @mock.patch(emploi_store.__name__ + '.datetime')
    def test_access_token_reuse(self, mock_requests, mock_datetime):
        """Test the access_token just after a token was fetched."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'first-token', 'expires_in': 500})
        now = datetime.datetime(2016, 3, 11)
        mock_datetime.datetime.now.return_value = now
        mock_datetime.timedelta = datetime.timedelta

        self.client.access_token('my-scope')

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'second-token', 'expires_in': 500})
        now += datetime.timedelta(seconds=40)
        mock_datetime.datetime.now.return_value = now

        token = self.client.access_token('my-scope')

        self.assertEqual('first-token', token)

    @mock.patch(emploi_store.__name__ + '.datetime')
    def test_access_token_expired(self, mock_requests, mock_datetime):
        """Test the access_token just after a token was fetched."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'first-token', 'expires_in': 20})
        now = datetime.datetime(2016, 3, 11)
        mock_datetime.datetime.now.return_value = now
        mock_datetime.timedelta = datetime.timedelta

        self.client.access_token('my-scope')

        now += datetime.timedelta(seconds=40)
        mock_datetime.datetime.now.return_value = now
        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'second token', 'expires_in': 20})

        token = self.client.access_token('my-scope')

        self.assertEqual('second token', token)

    def test_get_lbb_companies(self, mock_requests):
        """Test the get_lbb_companies method."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.get(
            'https://api.emploi-store.fr/partenaire/labonneboite/v1/company/?'
            'distance=10&latitude=45&longitude=2.1&rome_codes=A1204%2CB1201',
            headers={'Authorization': 'Bearer foobar'},
            json={'companies': [{'one': 1}, {'two': 2}]})

        companies = self.client.get_lbb_companies(45, 2.1, rome_codes=['A1204', 'B1201'])
        companies = list(companies)

        self.assertEqual([{'one': 1}, {'two': 2}], companies)

    def test_get_lbb_companies_by_city_id(self, mock_requests):
        """Test the get_lbb_companies method using a city ID as input."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.get(
            'https://api.emploi-store.fr/partenaire/labonneboite/v1/company/?'
            'distance=10&commune_id=31555&rome_codes=A1204',
            headers={'Authorization': 'Bearer foobar'},
            json={'companies': [{'one': 1}, {'two': 2}]})

        companies = list(self.client.get_lbb_companies(city_id='31555', rome_codes=['A1204']))

        self.assertEqual([{'one': 1}, {'two': 2}], companies)

    def test_get_lbb_companies_missing_location(self, unused_mock_requests):
        """Test the get_lbb_companies method when no location is given."""

        generator = self.client.get_lbb_companies(rome_codes=['A1204'])
        self.assertRaises(ValueError, next, generator)

    def test_get_lbb_companies_fail(self, mock_requests):
        """Test the get_lbb_companies method if the server fails."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.get(
            'https://api.emploi-store.fr/partenaire/labonneboite/v1/company/?'
            'distance=10&latitude=45&longitude=2.1&rome_codes=A1204%2CB1201',
            headers={'Authorization': 'Bearer foobar'},
            status_code=502, reason='Internal Failure')

        companies = self.client.get_lbb_companies(45, 2.1, rome_codes=['A1204', 'B1201'])
        with self.assertRaises(emploi_store.requests.exceptions.HTTPError):
            list(companies)

    def test_get_employment_rate_rank_for_training(self, mock_requests):
        """Test the get_employment_rate_rank_for_training method."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.get(
            'https://api.emploi-store.fr/partenaire/retouralemploisuiteformation/v1/rank?'
            'codeinseeville=69123&formacode=22435',
            headers={'Authorization': 'Bearer foobar'},
            json=[{
                'formacode': '22435',
                'codeinsee-bassin': '52114',
                'taux-bassin': '',
                'taux-departemental': '',
                'taux-regional': '0.4',
                'taux-national': '0.6',
            }])

        ranking = self.client.get_employment_rate_rank_for_training(
            city_id='69123', formacode='22435')

        self.assertEqual(
            {
                'formacode': '22435',
                'codeinsee-bassin': '52114',
                'taux-bassin': '',
                'taux-departemental': '',
                'taux-regional': '0.4',
                'taux-national': '0.6',
            },
            ranking)

    def test_get_employment_rate_rank_for_training_fail(self, mock_requests):
        """Test the get_employment_rate_rank_for_training method when the server fails."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.get(
            'https://api.emploi-store.fr/partenaire/retouralemploisuiteformation/v1/rank?'
            'codeinseeville=69123&formacode=22435',
            headers={'Authorization': 'Bearer foobar'},
            status_code=502, reason='Internal Failure')

        with self.assertRaises(emploi_store.requests.exceptions.HTTPError):
            self.client.get_employment_rate_rank_for_training(
                city_id='69123', formacode='22435')

    def test_get_match_via_soft_skills(self, mock_requests):
        """Test the match_via_soft_skills method."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.post(
            'https://api.emploi-store.fr/partenaire/matchviasoftskills/v1/professions/job_skills?'
            'code=A1204',
            headers={'Authorization': 'Bearer foobar'},
            status_code=201,
            json={
                'uuid': 'something',
                'code': 'A1204',
                'create_at': 'a date and time',
                'skills': {
                    'soft_skill_1': {'score': 1},
                    'soft_skill_2': {'score': 2},
                },
            })

        skills = list(self.client.get_match_via_soft_skills('A1204'))

        self.assertEqual([{'score': 1}, {'score': 2}], sorted(skills, key=lambda s: s['score']))

    def test_get_match_via_soft_skills_fail(self, mock_requests):
        """Test the match_via_soft_skills method when the server fails."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.post(
            'https://api.emploi-store.fr/partenaire/matchviasoftskills/v1/professions/job_skills?'
            'code=A1204',
            headers={'Authorization': 'Bearer foobar'},
            status_code=502, reason='Internal Failure')

        with self.assertRaises(emploi_store.requests.exceptions.HTTPError):
            list(self.client.get_match_via_soft_skills('A1204'))

    def test_la_bonne_alternance(self, mock_requests):
        """Test the get_lbb_companies method to access data from La Bonne Alternance."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.get(
            'https://api.emploi-store.fr/partenaire/labonneboite/v1/company/?'
            'distance=10&latitude=45&longitude=2.1&rome_codes=A1204%2CB1201&contract=alternance',
            headers={'Authorization': 'Bearer foobar'},
            json={
                'companies': [
                    {'one': 1},
                    {'two': 2},
                ],
            })

        companies = list(self.client.get_lbb_companies(
            45, 2.1, rome_codes=['A1204', 'B1201'], contract='alternance'))

        self.assertEqual([{'one': 1}, {'two': 2}], companies)

    def test_list_emploistore_services(self, mock_requests):
        """Test the list_emploistore_services method."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.get(
            'https://api.emploi-store.fr/partenaire/cataloguedesservicesemploistore/'
            'v1/api-emploistore/fichesservices',
            headers={'Authorization': 'Bearer foobar'},
            json=[
                {
                    'identifiantService': 'bobEmploi',
                    'nomService': 'Bob',
                    'typeService': 'coaching',
                },
                {
                    'identifiantService': 'laBonneBoite',
                    'nomService': 'La Bonne Boite',
                    'typeService': 'Moteur de recherche',
                },
            ])

        services = self.client.list_emploistore_services()

        self.assertEqual(
            ['Bob', 'La Bonne Boite'],
            [service.get('nomService') for service in services])

    def test_describe_emploistore_service(self, mock_requests):
        """Test the describe_emploistore_service method."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.get(
            'https://api.emploi-store.fr/partenaire/cataloguedesservicesemploistore/'
            'v1/api-emploistore/fichesservices/bobEmploi/false',
            headers={'Authorization': 'Bearer foobar'},
            json={
                'ficheService': {
                    'identifiantService': 'bobEmploi',
                    'nomService': 'Bob',
                    'typeService': 'coaching',
                },
            })

        service = self.client.describe_emploistore_service('bobEmploi')

        self.assertEqual('Bob', service.get('ficheService', {}).get('nomService'))

    def test_list_online_events(self, mock_requests):
        """Test the list_online_events method."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.get(
            'https://api.emploi-store.fr/partenaire/evenements/v1/salonsenligne',
            headers={
                'Accept': 'application/json',
                'Authorization': 'Bearer foobar',
            },
            json=[
                {
                    'titre': 'Recrutement ADMR',
                    'nombreOffres': 4,
                },
                {
                    'titre': u'la transition écologique: rejoignez HITECH !',
                    'nombreOffres': 2,
                },
            ])

        events = self.client.list_online_events()

        self.assertEqual(
            ['Recrutement ADMR', u'la transition écologique: rejoignez HITECH !'],
            [event.get('titre') for event in events])

    def test_list_physical_events(self, mock_requests):
        """Test the list_physical_events method."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token',
            json={'access_token': 'foobar'})
        mock_requests.get(
            'https://api.emploi-store.fr/partenaire/evenements/v1/evenementsphysiques',
            headers={
                'Accept': 'application/json',
                'Authorization': 'Bearer foobar',
            },
            json=[
                {
                    'titre': u'"Tremplin de l\'emploi" à Wittelsheim',
                    'categorie': 'Salon',
                    'dateDebut': '12/03/2019',
                    'dateFin': '12/03/2019',
                    'periode': 'de 9h à 17h',
                    'rue': '111, rue de Reiningue',
                    'codePostal': '68310',
                    'ville': 'Wittelsheim',
                    'region': 'Grand Est',
                    'latitudeGps': '47.792960',
                    'longitudeGps': '7.228931',
                },
                {
                    'titre': '10 clics pour un emploi',
                    'categorie': "Semaine d'événements",
                    'dateDebut': '25/02/2019',
                    'dateFin': '25/02/2019',
                    'periode': '14h - 15h30',
                    'rue': '3 bis Avenue des Noëlles',
                    'codePostal': '44500',
                    'ville': 'LA BAULE',
                    'region': 'Pays de la Loire',
                    'latitudeGps': '47.290804',
                    'longitudeGps': '-2.393948',
                },
            ])

        events = self.client.list_physical_events()

        self.assertEqual(
            [u'"Tremplin de l\'emploi" à Wittelsheim', '10 clics pour un emploi'],
            [event.get('titre') for event in events])

        self.assertEqual(
            ['Wittelsheim', 'LA BAULE'],
            [event.get('ville') for event in events])


@requests_mock.Mocker()
class PackageTest(unittest.TestCase):
    """Unit tests for the Package class."""

    def setUp(self):
        super(PackageTest, self).setUp()
        self._client = emploi_store.Client('my-ID', 'my-Secret')

    def test_get_resource_newer_version(self, mock_requests):
        """Test the get_resource method with a specific pe_version."""

        package = emploi_store.Package(
            self._client, name='BMO', resources=[
                {'name': 'BMO 2013', 'id': 'bmo-2013-1', 'pe_version': '1'},
                {'name': 'BMO 2013', 'id': 'bmo-2013-2', 'pe_version': '2'},
            ])

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.get(
            'https://api.emploi-store.fr/partenaire/infotravail/v1/resource_show?id=bmo-2013-2',
            headers={'Authorization': 'Bearer foobar'},
            json={
                'success': True,
                'result': {
                    'id': 'downloaded-id',
                    'name': 'Downloaded BMO',
                },
            },
        )

        res = package.get_resource(name='BMO 2013', pe_version='2')
        self.assertEqual('Downloaded BMO', res.name)


@requests_mock.Mocker()
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

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.get(
            'https://api.emploi-store.fr/partenaire/infotravail/v1/datastore_search?'
            'id=1234-abc',
            headers={'Authorization': 'Bearer foobar'},
            json={
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
        self.assertEqual('''CODE,NAME
123,First
456,Second
''', csv_content)

    def test_to_csv_number(self, mock_requests):
        """Test the to_csv method when resource returns numbers directly."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.get(
            'https://api.emploi-store.fr/partenaire/infotravail/v1/datastore_search?'
            'id=1234-abc',
            headers={'Authorization': 'Bearer foobar'},
            json={
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
        self.assertEqual('''CODE,NAME
123,First
456,Second
''', csv_content)

    def test_to_csv_utf8(self, mock_requests):
        """Test the to_csv method when resource has Unicode chars."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.get(
            'https://api.emploi-store.fr/partenaire/infotravail/v1/datastore_search?'
            'id=1234-abc',
            headers={'Authorization': 'Bearer foobar'},
            json={
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
        self.assertEqual(u'''CÖDE,NAME
123,Fïrst
456,Ségond
''', csv_content)

    def test_to_csv_utf8_with_bom(self, mock_requests):
        """Test the to_csv method when resource has the BOM bug."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.get(
            'https://api.emploi-store.fr/partenaire/infotravail/v1/datastore_search?'
            'id=1234-abc',
            headers={'Authorization': 'Bearer foobar'},
            json={
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
        self.assertEqual(u'''CÖDE,NAME
123,Fïrst
456,Ségond
''', csv_content)

    def test_to_csv_iterator(self, mock_requests):
        """Test the iterator arg of the to_csv method."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.get(
            'https://api.emploi-store.fr/partenaire/infotravail/v1/datastore_search?'
            'id=1234-abc',
            headers={'Authorization': 'Bearer foobar'},
            json={
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
        self.assertEqual('''CODE,NAME
1,First
3,Third
''', csv_content)

    def test_num_records(self, mock_requests):
        """Test the length of the records method."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.get(
            'https://api.emploi-store.fr/partenaire/infotravail/v1/datastore_search?'
            'id=1234-abc',
            headers={'Authorization': 'Bearer foobar'},
            json={
                'success': True,
                'result': {
                    'total': 42429,
                    'records': [{'id': 'hello'}],
                },
            })

        records = self.res.records()
        self.assertEqual(42429, len(records))
        self.assertEqual([{'id': 'hello'}], list(records))

    def test_to_csv_iterator_using_num_records(self, mock_requests):
        """Test the iterator arg of the to_csv method."""

        mock_requests.post(
            'https://entreprise.pole-emploi.fr/connexion/oauth2/access_token?realm=%2Fpartenaire',
            json={'access_token': 'foobar'})
        mock_requests.get(
            'https://api.emploi-store.fr/partenaire/infotravail/v1/datastore_search?'
            'id=1234-abc',
            headers={'Authorization': 'Bearer foobar'},
            json={
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
        self.assertEqual('''CODE,NAME
1 1/201,First
2 2/201,Second
3 3/201,Third
''', csv_content)


if __name__ == '__main__':
    unittest.main()
