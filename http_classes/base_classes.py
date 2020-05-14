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


class ChatGroup:
    def __init__(self, name, admin, user_set=set()):
        self.name = name
        self.admin = admin
        self.users = user_set
        if admin != "init":
            self.users.add(admin)

    def add_users(self, users):
        self.users.update(set(users))

    def remove_users(self, users):
        self.users.difference_update(set(users))

    def has_user(self, user):
        return user in self.users


class ChatGroups:
    def __init__(self, db_pool: psycopg2.pool.ThreadedConnectionPool):
        self.chat_groups = defaultdict(ChatGroup)
        self._conn = db_pool.getconn()
        self._cursor = None

        with Cursor(self._conn) as cursor:
            cursor.execute('SELECT * FROM chats')
            records = cursor.fetchall()
            for (name, admin) in records:
                cursor.execute(f"SELECT login FROM users_to_chats WHERE chat = '{name}'")
                users = cursor.fetchall()
                self.chat_groups[name] = ChatGroup(name, admin, set(user for (user,) in users))

    def __getitem__(self, chat_name):
        if self.chat_groups.get(chat_name):
            return self.chat_groups[chat_name]
        else:
            return None

    def __setitem__(self, chat_name, group):
        if self[chat_name] is None:
            self.chat_groups[chat_name] = group
            with Cursor(self._conn) as cursor:
                cursor.execute(f"INSERT INTO chats "
                               f"SELECT '{chat_name}', '{group.admin}';")
                for each in group.users:
                    cursor.execute(f"INSERT INTO users_to_chats "
                                   f"SELECT '{each}', '{chat_name}';")
                self._conn.commit()
                count = cursor.rowcount
                logging.info(f'insert {count} values into chats')
                if count == 0:
                    raise HTTPError(500, "chat group created locally but not inserted into database")

    def __delitem__(self, chat_name):
        if self[chat_name]:
            with Cursor(self._conn) as cursor:
                cursor.execute(f"DELETE FROM chats "
                               f"WHERE name = '{chat_name}';"
                               f"DELETE FROM users_to_chats "
                               f"WHERE chat = '{chat_name}';")
                self._conn.commit()
                count = cursor.rowcount
                logging.info(f'removed {count} values from chats and user_to_chats')
                if count == 0:
                    raise HTTPError(500, "failed to remove the chat")
                del self.chat_groups[chat_name]

        else:
            raise HTTPError(404, "The chat does not exist")

    def add_users(self, chat_name, users):
        if self[chat_name]:
            with Cursor(self._conn) as cursor:
                for each in users:
                    if not self[chat_name].has_user(each):
                        cursor.execute(f"INSERT INTO users_to_chats "
                                       f"SELECT '{each}', '{chat_name}'")
                self._conn.commit()
                count = cursor.rowcount
                logging.info(f'insert {count} values into chats')
                if count == 0:
                    raise HTTPError(500, "users added locally but not inserted into database")
            self[chat_name].add_users(users)

    def remove_users(self, chat_name, users):
        if self[chat_name]:
            with Cursor(self._conn) as cursor:
                for each in users:
                    if self[chat_name].has_user(each):
                        cursor.execute(f"DELETE FROM users_to_chats "
                                       f"WHERE login ='{each}' AND chat = '{chat_name}'")
                self._conn.commit()
                count = cursor.rowcount
                logging.info(f'insert {count} values into chats')
                if count == 0:
                    raise HTTPError(500, "users removed locally but not from database")
            self[chat_name].remove_users(users)

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

    def exists(self, chat_name):
        return chat_name in self.chat_groups.keys()

class User:
    def __init__(self, login: str, name: str, password: str):
        self.login = login
        self.name = name
        self.password = password
        self.auth_token = None
        self.connection = None
        self.chats = None

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
            "login": self.login,
            "name": self.name,
            "auth_token": self.auth_token
        }


class Users:

    def __init__(self, conn):
        self.users = {}
        self.conn = conn
        with Cursor(self.conn) as cursor:
            cursor.execute('SELECT * FROM users')
            records = cursor.fetchall()
            for (login, name, password) in records:
                self.users[login] = User(login, name, password)
                cursor.execute(f"SELECT chat FROM users_to_chats WHERE login = '{login}'")
                chats = cursor.fetchall()
                self.users[login].chats = set(chat for (chat,) in chats)

    def __getitem__(self, login) -> User or None:
        if self.users.get(login):
            return self.users[login]
        else:
            return None

    def __setitem__(self, login, user: User):
        if self[login] is None:
            self.users[login] = user
            self.users[login].chats = {"all"}
            with Cursor(self.conn) as cursor:
                cursor.execute(f"INSERT INTO users "
                               f"SELECT '{user.login}', '{user.name}', '{user.password}';")
                self.conn.commit()
                count = cursor.rowcount
                logging.info(f'insert {count} values into users')
                if count == 0:
                    raise HTTPError(500, "user created locally but not inserted into database")
                cursor.execute(f"INSERT INTO users_to_chats "
                               f"SELECT '{user.login}',  'all';")
                self.conn.commit()
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
