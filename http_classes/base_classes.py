from _collections import defaultdict
import psycopg2
from psycopg2 import pool

__all__ = ['TokenConn', 'Reciever', 'ChatGroups']


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

    def delete_token_from_user(self, users):
        users[self.login]["auth_token"] = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.cursor
        if exc_type:
            raise exc_val


class Reciever:

    '''
        i will iterate through users dict by logins of recievers in chats,
        trying to find needed address for sending message
    '''
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
