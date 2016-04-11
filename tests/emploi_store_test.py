"""Unit tests for emploi_store module."""
import datetime
import tempfile
import shutil
import unittest

import emploi_store
import mock

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

        token = self.client.access_token()

        self.assertEqual(1, mock_requests.post.call_count)
        self.assertEqual(
            'my-ID',
            mock_requests.post.call_args[1]['data']['client_id'])
        self.assertEqual(
            'my-Secret',
            mock_requests.post.call_args[1]['data']['client_secret'])
        self.assertEqual('foobar', token)

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

        self.client.access_token()

        mock_requests.post.reset_mock()
        now += datetime.timedelta(seconds=40)
        mock_datetime.datetime.now.return_value = now

        token = self.client.access_token()

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

        self.client.access_token()

        mock_requests.post.reset_mock()
        now += datetime.timedelta(seconds=40)
        mock_datetime.datetime.now.return_value = now
        mock_requests.post.return_value.json.return_value = {
            "access_token": "second token",
        }

        token = self.client.access_token()

        self.assertEqual('second token', token)
        self.assertTrue(mock_requests.post.called)


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
        mock_requests.post.return_value = mock.MagicMock()
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {
            "access_token": "foobar",
        }
        mock_requests.get.return_value = mock.MagicMock()
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.json.return_value = {
            'success': True,
            'result': {
                'records': [
                    {'CODE': '123', 'NAME': 'First'},
                    {'CODE': '456', 'NAME': 'Second'},
                ],
            },
        }
        filename = self.tmpdir + '/bmo_2016.csv'

        self.res.to_csv(filename)

        csv_content = open(filename).read().replace('\r\n', '\n')
        self.assertEqual("""CODE,NAME
123,First
456,Second
""", csv_content)



if __name__ == '__main__':
    unittest.main()
