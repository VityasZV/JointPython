from email.parser import Parser
import json
import logging
import socket
from http_classes.http_classes import Request, Response, HTTPError, MAX_HEADERS, MAX_LINE


class Client:
    def __init__(self, host, port, name):
        self.host = host
        self.port = port
        self.server_host = None
        self.server_port = None
        self.name = None
        self.login = None
        self.auth_token = None
        self.sock_fd = None

    def connect_to_server(self, host, port):
        try:
            self.sock_fd = socket.create_connection((host, port))
            self.server_host = host
            self.server_port = port
        except socket.gaierror:
            logging.warning("trouble finding server host")
        except socket.timeout:
            logging.info("can't find server")
        except socket.error:
            logging.warning("trouble creating socket")

    async def register(self):
        self.login = input("Login name: " )
        self.name = input("User name: ")
        password = input("Password: ")
        data = json.dumps({"login": self.login, "name": self.name, "password": password})
        if self.server_host and self.server_port:
            target = "https://"+f"{self.server_host}" + f":{self.server_port}"
            req = f'POST {target} HTTP/1.1\nHost: server\nUser-Agent: demo-client\n\n{data}'
            try:
                self.sock_fd.send(req.encode())
                resp = await self.parse_response()
                print(resp.reason)
                resp.buffer.flush()
                resp.buffer.close()
            except socket.error:
                logging.warning("cant send to server")

    async def parse_response(self):
        buffer = self.sock_fd.makefile('rb')
        status, reason, ver = await self.parse_response_line(buffer)
        headers = await self.parse_headers(buffer)
        return Response(status, reason, ver, headers, buffer)

    async def parse_response_line(self, rfile):
        raw = rfile.readline()
        resp_line = str(raw, 'iso-8859-1')
        words = resp_line.split()
        if len(words) != 3:
            logging.info ("Bad response")
        return words

    async def parse_headers(self, rfile):
        headers = []
        while True:
            line = rfile.readline()
            if line in (b'\r\n', b'\n', b''):
                break
            headers.append(line)
        sheaders = b''.join(headers).decode('iso-8859-1')
        return Parser().parsestr(sheaders)