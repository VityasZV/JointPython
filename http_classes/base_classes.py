import hashlib
import os
from socket import socket
from _collections import defaultdict
import psycopg2
from psycopg2 import pool
import logging
from http_classes.http_classes import HTTPError

__all__ = ['TokenConn', 'Reciever', 'ChatGroups', 'Cursor', 'TokensConn', 'Users', 'User']

logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.DEBUG)


class Users(object):
    pass


class Cursor:
    def __init__(self, conn):
        self.cursor = conn.cursor()

    def __del__(self):
        self.cursor.close()

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(exc_val)
        self.cursor.close()


class TokenConn:

    def __init__(self, token=None, db_pool=psycopg2.pool.ThreadedConnectionPool, login=None):
        self._cursor = None
        self.token = token
        self.conn = None
        self._pool = db_pool
        self.login = login

    def __del__(self):
        if self._cursor:
            self._cursor.close()
        if self._pool and self.conn and not self._pool.closed:
            self._pool.putconn(self.conn)

    def connect_to_db(self):
        self.conn = self._pool.getconn()

    @property
    def cursor(self):
        return self._cursor

    @cursor.getter
    def cursor(self):
        return self._cursor

    @cursor.deleter
    def cursor(self):
        if self._cursor:
            self._cursor.close()

    @cursor.setter
    def cursor(self):
        pass

    def set_cursor(self):
        self._cursor = self.conn.cursor()

    def delete_token_from_user(self, users: Users):
        users[self.login].auth_token = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.cursor
        if exc_type:
            raise exc_val


class TokensConn:
    def __init__(self):
        self.tokens_conn = dict()  # mapping (auth_token: str)  to (TokenConn)

    def __setitem__(self, token: str, value: TokenConn):
        self.tokens_conn[token] = value

    def __getitem__(self, item: str):
        if self.tokens_conn.get(item):
            return self.tokens_conn[item]
        else:
            return None

    def __delitem__(self, token):
        self.tokens_conn.pop(token)

    def delete_token_from_user(self, token: str, users: Users):
        if self[token] is None:
            raise HTTPError(404, 'Not found')
        self[token].delete_token_from_user(users)
        print(self.user(token, users).login)
        self.user(token, users).connection = None
        del self[token]

    def user(self, token: str, users: Users):
        try:
            return users[self[token].login]
        except Exception:
            return None


class Reciever:
    """
        i will iterate through users dict by logins of recievers in chats,
        trying to find needed address for sending message
    """

    def __init__(self, login):
        self.login = login


class ChatGroups:
    def __init__(self, db_pool: psycopg2.pool.ThreadedConnectionPool):
        self.chat_groups = defaultdict(set)
        self._conn = db_pool.getconn()
        self._cursor = None

    def __getitem__(self, chat_name) -> set:
        if self.chat_groups.get(chat_name):
            return self.chat_groups[chat_name]
        else:
            return set()

    def __setitem__(self, chat_name, recievers):
        for r in recievers:
            self.chat_groups[chat_name].add(r)

    def __delitem__(self, chat_name):
        del self.chat_groups[chat_name]

    @property
    def cursor(self):
        return self._cursor

    @cursor.getter
    def cursor(self):
        return self._cursor

    @cursor.deleter
    def cursor(self):
        if self._cursor:
            self._cursor.close()

    @cursor.setter
    def cursor(self):
        pass

    def set_cursor(self):
        self._cursor = self._conn.cursor()


class User:
    def __init__(self, login: str, name: str, password: str):
        self.login = login
        self.name = name
        self.password = password
        self.auth_token = None
        self.connection = None

    def logout(self):
        self.connection = None

    def generate_auth_token(self, tokens_conn: TokensConn, conn_pool: psycopg2.pool.ThreadedConnectionPool,
                            conn: socket) -> str:
        if self.auth_token is None:
            self.auth_token = hashlib.sha256(os.urandom(1024)).hexdigest()
            tokens_conn[self.auth_token] = TokenConn(self.auth_token, conn_pool, self.login)
            tokens_conn[self.auth_token].connect_to_db()
            self.connection = conn
        return self.auth_token

    def json_prepare(self):
        return {
            "login"         : self.login,
            "name"          : self.name,
            "auth_token"    : self.auth_token
        }


class Users:

    def __init__(self, conn):
        self.users = {}
        self.conn = conn
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users')
        records = cursor.fetchall()
        cursor.close()
        for (login, name, password) in records:
            self.users[login] = User(login, name, password)

    def __getitem__(self, login) -> User or None:
        if self.users.get(login):
            return self.users[login]
        else:
            return None

    def __setitem__(self, login, user: User):
        if self[login] is None:
            self.users[login] = user
            with Cursor(self.conn) as cursor:
                cursor.execute(f"INSERT INTO users "
                               f"SELECT '{user.login}', '{user.name}', '{user.password}';")
                self.conn.commit()
                count = cursor.rowcount
                logging.info(f'insert {count} values into users')
                if count == 0:
                    raise HTTPError(500, "user created locally but not inserted into database")
        else:
            raise HTTPError(405, "This login is already in use")

    def __delitem__(self, login):
        if self[login]:
            with Cursor(self.conn) as cursor:
                cursor.execute(f"DELETE FROM users "
                                     f"WHERE login = '{login}';")
                self.conn.commit()
                count = cursor.rowcount
                logging.info(f'removed {count} values into users')
                if count == 0:
                    raise HTTPError(500, "failed to remove the user")
        else:
            raise HTTPError(405, "The user does not exist")

    def keys(self):
        return self.users.keys()

    def values(self):
        return self.users.values()

    def token_for_user(self, login: str, tokens_conn: TokensConn, conn_pool: psycopg2.pool.ThreadedConnectionPool,
                       conn: socket):
        token = self[login].generate_auth_token(tokens_conn=tokens_conn, conn_pool=conn_pool, conn=conn)
        return token
