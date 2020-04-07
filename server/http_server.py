import hashlib
import os

from server.demo_server import MyHTTPServer, TokenConn
from http_classes.http_classes import Request, Response, HTTPError, MAX_HEADERS, MAX_LINE

import json
import logging
import psycopg2
from psycopg2 import pool
import asyncio
from decimal import Decimal

__all__ = ["FullHTTPServer"]

logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.DEBUG)


async def handle_response(req: Request, resp_body, encoding: str, default=None) -> Response:
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
    return Response(200, 'OK', headers, body)


class FullHTTPServer(MyHTTPServer):

    async def handle_prepare(self, req: Request):
        accept = req.headers.get('Accept')
        data = json.loads(req.body)
        auth_token = data["auth_token"]
        if self._tokens_conn.get(auth_token):
            return accept, data, auth_token
        else:
            raise HTTPError(400, "Invalid token")

    async def handle_request(self, req: Request) -> Response:
        if req.path == '/registry' and req.method == 'POST':
            return await self.handle_post_registry(req)

        if req.path == '/login' and req.method == 'POST':
            return await self.handle_post_login(req)

        if req.path == '/logout' and req.method == 'POST':
            return await self.handle_post_logout(req)

        if req.path == '/users' and req.method == 'GET':
            return await self.handle_get_users(req)

        if req.path.startswith('/users/'):
            user_id = req.path[len('/users/'):]
            if user_id.isdigit():
                return await self.handle_get_user(req, user_id)

        raise HTTPError(404, 'Not found')

    async def handle_post_registry(self, req: Request) -> Response:
        data = json.loads(req.body.decode('utf-8'))
        if self._users.get(data["login"]) is None:
            self._users[data["login"]] = {
                'name': data["name"],
                'password': data["password"],
            }
            users_cursor = self._users_conn.cursor()
            users_cursor.execute(f"INSERT INTO users "
                                 f"SELECT '{data['login']}', '{data['name']}', '{data['password']}';")
            self._users_conn.commit()
            count = users_cursor.rowcount
            logging.info(f'insert {count} values into users')
            users_cursor.close()
            if count == 0:
                return Response(500, "user created locally but not inserted into database")
            return Response(204, 'Created')
        else:
            return Response(405, "This login is already in use")

    async def handle_post_login(self, req):
        data = json.loads(req.body)
        if self._users.get(data["login"]) is None:
            return Response(404, 'Not found')

        if self._users[data["login"]]["password"] != data["password"]:
            return Response(401, "Unauthorized - wrong password")

        if self._users[data["login"]].get("auth_token") is None:
            auth_token = hashlib.sha256(os.urandom(1024)).hexdigest()
            self._users[data["login"]]["auth_token"] = auth_token
            self._tokens_conn[auth_token] = TokenConn(auth_token, self._pool, data["login"])
            await self._tokens_conn[auth_token].connect_to_db()
        else:
            auth_token = self._tokens_conn[self._users[data["login"]]["auth_token"]].token
        # print(f'main: {id(self._pool)}, in_token: {id(self._tokens_conn[self._users[data["login"]]["auth_token"]]._pool)}') --they are same
        return await handle_response(req=req, resp_body={"token": auth_token}, encoding='utf-8')

    async def handle_post_logout(self, req):
        data = json.loads(req.body)
        if self._tokens_conn.get(data["auth_token"]) is None:
            return Response(404, 'Not found')
        self._tokens_conn[data["auth_token"]].delete_token_from_user(self._users)
        # closing connection of a user
        self._tokens_conn.pop(data["auth_token"])
        return Response(200, "OK")

    async def handle_get_users(self, req: Request) -> Response:
        return await handle_response(req=req, resp_body=self._users, encoding='utf-8')

    async def handle_get_user(self, req: Request, user_id) -> Response:
        user = self._users.get(int(user_id))
        if not user:
            raise HTTPError(404, 'Not found')
        return await handle_response(req=req, resp_body=user, encoding='utf-8')


if __name__ == '__main__':
    host = 'localhost'
    port = 8000
    name = 'server'
    server = FullHTTPServer(host, port, name)
    try:
        asyncio.run(server.serve_forever())
    except KeyboardInterrupt:
        logging.info('server shut down')
        pass
