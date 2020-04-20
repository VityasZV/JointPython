from email.parser import Parser
import json
import logging
import socket
from http_classes.http_classes import Request, Response, HTTPError, MAX_HEADERS, MAX_LINE


class Client:
    def __init__(self):
        #self.host = host
        #self.port = port
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
            #resp = self.get_response()
            #print(resp.reason)
            #resp.body.flush()
            #resp.body.close()
        except socket.gaierror:
            logging.warning("trouble finding server host")
            return False
        except socket.timeout:
            logging.info("can't find server")
            return False
        except socket.error:
            logging.warning("trouble creating connection")
            return False
        return True

    def register(self):
        self.login = input("Login name: " )
        self.name = input("User name: ")
        password = input("Password: ")
        data = json.dumps({"login": self.login, "name": self.name, "password": password})
        if self.server_host and self.server_port:
            target = "https://"+f"{self.server_host}" + f":{self.server_port}/registry"
            req = f'POST {target} HTTP/1.1\r\nHost: server\r\nUser-Agent: demo-client\r\nContent-Length:{len(data)}\r\n\n{data}'

            try:
                self.sock_fd.send(req.encode())
                resp = self.get_response()
                msg = resp.body.readlines()
                print(resp.reason)
                resp.body.flush()
                resp.body.close()
            except socket.error:
                logging.warning("cant send to server")

    def get_response(self):
        buffer = self.sock_fd.makefile('rb')
        ver, status, reason = self.parse_response_line(buffer)
        headers = self.parse_headers(buffer)
        return Response(status, reason, headers, buffer)

    def parse_response_line(self, file):
        raw = file.readline()
        resp_line = str(raw, 'iso-8859-1')
        resp_line = resp_line.rstrip("\r\n")
        words = resp_line.split(" ")
        if len(words) != 3:
            words[2] = " ".join(words[2:])
            words = words[:3]
            logging.info("Bad response")
        return words

    def parse_headers(self, file):
        headers = []
        while True:
            line = file.readline()
            if line in (b'\r\n', b'\n', b''):
                break
            headers.append(line)
        sheaders = b''.join(headers).decode('iso-8859-1')
        return Parser().parsestr(sheaders)

cl = Client()
if cl.connect_to_server('localhost', 8000):
    cl.register()
