from http_classes.http_classes import Request, Response, HTTPError, MAX_HEADERS, MAX_LINE
from http_classes.base_classes import TokenConn, ChatGroups, Reciever

from email.parser import Parser
import psycopg2
from psycopg2 import pool
import socket
import logging
from _collections import defaultdict
import threading

# setting all logs
__all__ = ["MyHTTPServer"]

logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
                    level=logging.DEBUG)


def init_users(conn) -> dict:
    users = {}
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM users')
    records = cursor.fetchall()
    cursor.close()
    for (login, name, password) in records:
        users[login] = {
            'name': name,
            'password': password
        }
    return users


class MyHTTPServer:
    def __init__(self, host, port, server_name):
        self._host = host
        self._port = port
        self._server_name = server_name
        self._tokens_conn = defaultdict(TokenConn)
        self._pool = psycopg2.pool.ThreadedConnectionPool(1, 50, user='admin', password='', host=self._host,
                                                          port=5432, database='chat')
        if self._pool:
            logging.info("connection pool created successfully")
        self._users_conn = self._pool.getconn()
        self._users = init_users(self._users_conn)
        self._chat_groups = ChatGroups(self._pool)
        self._chat_groups['all'] = {Reciever(login) for login in self._users.keys()}
        self._serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, proto=0)
        logging.info("server initialized")

    def __del__(self):
        logging.info("deleting server")
        if self._pool:
            self._pool.closeall()

    def serve_forever(self):
        try:
            self._serv_sock.bind((self._host, self._port))
            self._serv_sock.listen()

            while True:
                conn, address = self._serv_sock.accept()
                try:
                    th = threading.Thread(target=self.serve_client, args=(conn, address))
                    th.start()
                except Exception as e:
                    logging.warning(f'Client serving failed: {e}')

        finally:
            self._serv_sock.close()

    def serve_client(self, conn, address):
        req = None  # for net cat using
        try:
            logging.info(f"connected client: {address}")
            req = self.parse_request(conn)
            resp = self.handle_request(req, address)
            self.send_response(conn, resp)
        except ConnectionResetError:
            conn = None
            logging.warning("base disconnected")
        except Exception as e:
            try:
                self.send_error(conn, e)
            except BrokenPipeError as er:
                logging.warning(f'{er}')

        if conn:
            if req:
                req.rfile.close()
            # не стоит рвать соедиение сразу после обработки запроса, учитывая что это чат
            for user in self._users.values():
                if user.get('address') and user.get('address') == address:
                    pass  # TODO: here should be return statement - will fix after testing with client
            # for other handlers connection should be closed
            print("close connection")
            conn.close()
            return

    def parse_request(self, conn):
        rfile = conn.makefile('rb')
        method, target, ver = self.parse_request_line(rfile)
        headers = self.parse_headers(rfile)
        host = headers.get('Host')
        if not host:
            raise HTTPError(400, 'Bad request',
                            'Host header is missing')
        if host not in (self._server_name,
                        f'{self._server_name}:{self._port}'):
            raise HTTPError(404, 'Not found')
        return Request(method, target, ver, headers, rfile)

    def parse_request_line(self, rfile):
        raw = rfile.readline(MAX_LINE + 1)
        if len(raw) > MAX_LINE:
            raise HTTPError(400, 'Bad request',
                            'Request line is too long')

        req_line = str(raw, 'iso-8859-1')
        words = req_line.split()
        if len(words) != 3:
            raise HTTPError(400, 'Bad request',
                            'Malformed request line')
        method, target, ver = words
        if ver != 'HTTP/1.1':
            raise HTTPError(505, 'HTTP Version Not Supported')
        return method, target, ver

    def parse_headers(self, rfile):
        headers = []
        while True:
            line = rfile.readline(MAX_LINE + 1)
            if len(line) > MAX_LINE:
                raise HTTPError(494, 'Request header too large')

            if line in (b'\r\n', b'\n', b''):
                break

            headers.append(line)
            if len(headers) > MAX_HEADERS:
                raise HTTPError(494, 'Too many headers')

        sheaders = b''.join(headers).decode('iso-8859-1')
        return Parser().parsestr(sheaders)

    def handle_request(self, req: Request, address) -> Response:
        pass

    def send_response(self, conn, resp):
        wfile = conn.makefile('wb')
        status_line = f'HTTP/1.1 {resp.status} {resp.reason}\r\n'
        wfile.write(status_line.encode('iso-8859-1'))

        if resp.headers:
            for (key, value) in resp.headers:
                header_line = f'{key}: {value}\r\n'
                wfile.write(header_line.encode('iso-8859-1'))

        wfile.write(b'\r\n')

        if resp.body:
            wfile.write(resp.body)

        wfile.flush()
        wfile.close()

    def send_error(self, conn, err):
        try:
            status = err.status
            reason = err.reason
            body = (err.body or err.reason).encode('utf-8')
        except:
            logging.info(f'Internal error: {err}')
            status = 500
            reason = b'Internal Server Error'
            body = b'Internal Server Error'
        resp = Response(status, reason,
                        [('Content-Length', len(body))],
                        body)
        self.send_response(conn, resp)
