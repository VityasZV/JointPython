import hashlib
import os
import socket

from http_classes.base_classes import TokenConn, TokensConn, User
from server.demo_server import MyHTTPServer
from http_classes.http_classes import Request, Response, HTTPError, MAX_HEADERS, MAX_LINE, ConnStatus

import json
import logging

__all__ = ["FullHTTPServer"]

logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.DEBUG)


def handle_response(req: Request, resp_body, resp_status, resp_reason, encoding: str, default=None,
                    keep_alive=False) -> Response:
    accept = req.headers.get('Accept')
    if 'application/json' in accept:
        contentType = f'application/json; charset={encoding}'
        body = json.dumps(resp_body, default=default)
    else:
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/406
        raise HTTPError(406, 'Not Acceptable')

    body = body.encode(f'{encoding}')
    headers = [('Content-Type', contentType),
               ('Content-Length', len(body))]
    if keep_alive:
        headers.append(('Connection', 'Keep-Alive'))
        headers.append(('Keep-Alive', 'timeout=5, max=1000'))
    return Response(resp_status, resp_reason, headers, body)


class FullHTTPServer(MyHTTPServer):

    def handle_prepare(self, req: Request):
        accept = req.headers.get('Accept')
        data = json.loads(req.body)
        auth_token = data["auth_token"]
        if self._tokens_conn.get(auth_token):
            return accept, data, auth_token
        else:
            raise HTTPError(400, "Invalid token")

    def handle_request(self, req: Request, connection: socket.socket) -> Response:
        if req.path == '/registry' and req.method == 'POST':
            return self.handle_post_registry(req)

        if req.path == '/login' and req.method == 'POST':
            return self.handle_post_login(req, connection)

        if req.path == '/logout' and req.method == 'POST':
            self._connections[connection] = ConnStatus.closing
            return self.handle_post_logout(req)

        if req.path == '/users' and req.method == 'GET':
            return self.handle_get_users(req)

        if req.path == '/test' and req.method == 'GET':
            return self.handle_inf_test(req)

        if req.path.startswith('/message/') and req.method == 'POST':
            return self.handle_message(req, connection)

        if req.path.startswith('/users/'):
            user_id = req.path[len('/users/'):]
            if user_id.isdigit():
                return self.handle_get_user(req, user_id)

        raise HTTPError(404, 'Not found')

    def handle_post_registry(self, req: Request) -> Response:
        data = json.loads(req.body.decode('utf-8'))
        login, name, password = data["login"], data["name"], data["password"]
        self._users[login] = User(login, name, password)
        return handle_response(req=req, resp_body={"status": "user created"}, resp_status=204,
                               resp_reason='Created', encoding='utf-8')

    def handle_post_login(self, req, connection: socket.socket):
        data = json.loads(req.body)
        login, password = data["login"], data["password"]
        if self._users[login] is None:
            raise HTTPError(404, 'Not found')

        if self._users[login].password != password:
            raise HTTPError(404, "Unauthorized - wrong password")

        auth_token = self._users.token_for_user(login=login, tokens_conn=self._tokens_conn,
                                                conn_pool=self._pool, conn=connection)
        return handle_response(req=req, resp_body={"status": "logged in", "token": auth_token}, resp_status=200,
                               resp_reason='OK', encoding='utf-8', keep_alive=True)

    '''
        just for testing threads, it works perfectly
    '''

    def handle_inf_test(self, req):
        for k in range(10000000000000):
            i = 0
            while i < 100000000000000000000000:
                i += 1
        return handle_response(req=req, resp_body="OK",
                               resp_status=200, resp_reason='OK', encoding='utf-8')

    def handle_post_logout(self, req):
        data = json.loads(req.body)
        auth_token = data["auth_token"]
        self._tokens_conn.delete_token_from_user(token=auth_token, users=self._users)
        return handle_response(req=req, resp_body={"status": "logged out"}, resp_status=200, resp_reason='OK',
                               encoding='utf-8', keep_alive=True)

    def handle_get_users(self, req: Request) -> Response:
        users = []
        for user in self._users.values():
            users.append(user.json_prepare())

        return handle_response(req=req, resp_body=users,
                               resp_status=200, resp_reason='OK', encoding='utf-8')

    def handle_get_user(self, req: Request, login : str) -> Response:
        user = self._users[login]
        if not user:
            raise HTTPError(404, 'Not found')
        return handle_response(req=req, resp_body=user.json_prepare(), resp_status=200, resp_reason='OK', encoding='utf-8')

    '''
    Request:
        query: /message/<recievers_group>
        recievers_group = {'all' - все юзеры, т.е глобальный чат,
                           '<chat_name>' - все пользователи данного чата
                           }
        P.S:  имена чатов сохраню в базу, вместе с логинами пользователей чата
            также параметр chat_name - может просто равняться 
        body: 
            {
                text : str - текст сообщения
                auth_token : str - авторизационный токен пользователя
            }
    Response:
        200 OK - для пославшего сообщение в случае успеха отправки. 
        404 Not found - неверный токен
        404 Recievers Not Found - не нашлась группа получателей
        500 Internal Error - при внутренних ошибках сервака. 
    '''

    def handle_message(self, req: Request, connection: socket.socket) -> Response:
        recievers_group = req.path[len('/message/'):]
        data = json.loads(req.body)
        auth_token = data["auth_token"]
        if self._tokens_conn[auth_token] is None:
            raise HTTPError(404, 'Not found')
        self.send_message(recievers_group, data, connection)
        return handle_response(req=req, resp_body={"status": "sent"}, resp_status=200, resp_reason='OK', encoding='utf-8')

    def send_message(self, recievers_group, data, connection):
        if recievers_group == 'all':
            for reciever in self._users.values():
                if reciever.connection == connection:
                    # не хотим отправлять сообщение самому себе
                    # test
                    #reciever["connection"].send(data["text"].encode('utf-8'))
                    continue
                else:
                    if reciever.connection:
                        contentType = f'application/json; charset=utf-8'
                        body = json.dumps({"status": "message", "text": data["text"]})
                        body = body.encode(f'utf-8')
                        headers = [('Content-Type', contentType), ('Content-Length', len(body)),
                                   ('Connection', 'Keep-Alive'), ('Keep-Alive', 'timeout=5, max=1000')]
                        resp = Response(200, "OK", headers, body)
                        self.send_response(reciever.connection, resp)


if __name__ == '__main__':
    host = 'localhost'
    port = 8000
    name = 'server'
    server = FullHTTPServer(host, port, name)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info('server shut down')
        pass
