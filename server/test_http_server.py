from unittest import TestCase
import requests
import server.http_server as srv

class TestFullHTTPServer(TestCase):
    def setUp(self):
        self.url = 'http://127.0.0.1:8000'
        self.headers = {'host': 'server', 'user-agent': '', 'accept': 'application/json'}
        self.user1_json = {'login': 'user1', 'name': 'u1', 'password': '123'}
        #print(requests.post(self.url + '/remove', json=self.user1_json, headers=self.headers).text)


    def test_registry_correctness(self):
        print(requests.post(self.url + '/remove', json=self.user1_json, headers=self.headers).text)
        requests.post(self.url + '/registry', json=self.user1_json, headers=self.headers)
        us1 = requests.get(self.url + '/users', headers=self.headers)
        self.assertIn(self.user1_json['login'], us1.text)

    def test_double_registry(self):
        requests.post(self.url + '/registry', json=self.user1_json, headers=self.headers)
        reg2 = requests.post(self.url + '/registry', json=self.user1_json, headers=self.headers)
        self.assertEqual(reg2.text, 'This login is already in use')

    def test_double_login(self):
        requests.post(self.url + '/registry', json=self.user1_json, headers=self.headers)
        reg1 = requests.post(self.url+'/login', json=self.user1_json, headers=self.headers)
        reg2 = requests.post(self.url + '/login', json=self.user1_json, headers=self.headers)
        self.assertEqual(reg1.text, reg2.text)

    def test_login_not_exist(self):
        data = {'login': 'test_login_not_exist', 'name': '11', 'password': '123'}
        reg1 = requests.post(self.url + '/login', json=data, headers=self.headers)
        self.assertEqual(reg1.text, 'Not found')

    def test_logout(self):
        requests.post(self.url + '/registry', json=self.user1_json, headers=self.headers)
        status = requests.post(self.url + '/login', json=self.user1_json, headers=self.headers).json()
        self.assertEqual(status['status'], 'logged in')
        reg1 = requests.post(self.url + '/logout', json={'auth_token': status['token']}, headers=self.headers)
        self.assertEqual(reg1.json()['status'], 'logged out')

    def test_double_logout(self):
        requests.post(self.url + '/registry', json=self.user1_json, headers=self.headers)
        status = requests.post(self.url + '/login', json=self.user1_json, headers=self.headers).json()
        self.assertEqual(status['status'], 'logged in')
        reg1 = requests.post(self.url + '/logout', json={'auth_token': status['token']}, headers=self.headers)
        self.assertEqual(reg1.json()['status'], 'logged out')
        reg2 = requests.post(self.url + '/logout', json={'auth_token': status['token']}, headers=self.headers)
        self.assertEqual(reg2.text, 'Not found')

    def test_logout_not_exist(self):
        data = {'auth_token': '0'}
        reg1 = requests.post(self.url + '/logout', json=data, headers=self.headers)
        self.assertEqual(reg1.text, 'Not found')

    def tearDown(self) -> None:
        status = requests.post(self.url + '/login', json=self.user1_json, headers=self.headers).json()
        requests.post(self.url + '/logout', json={'auth_token': status['token']}, headers=self.headers)
        requests.post(self.url + '/remove', json=self.user1_json, headers=self.headers).text
