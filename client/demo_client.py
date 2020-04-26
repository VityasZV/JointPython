import threading
from email.parser import Parser
import json
import logging
import socket
from http_classes.http_classes import Request, Response, HTTPError, MAX_HEADERS, MAX_LINE

__all__ = ['Client']


class Client:
    def __init__(self):
        self.server_host = None
        self.server_port = None
        self.login = None
        self.auth_token = None
        self.sock_fd = None
        self.state = "start"
        self.receiver = None
        self.rcv_success = threading.Event()
        self.rcv_success.clear()

    def connect_to_server(self, host, port):
        try:
            self.sock_fd = socket.create_connection((host, port))
            self.server_host = host
            self.server_port = port
            self.receiver = threading.Thread(target=self.receive_forever, args=((self.rcv_success),))
            self.receiver.start()
        except socket.gaierror:
            logging.warning("trouble finding server host")
            return False
        except socket.timeout:
            logging.info("can't find server")
            return False
        except socket.error:
            logging.warning("trouble creating connection")
            return False
        self.state = "connected"
        return True

    def register(self):
        self.login = input("Login name: ")
        name = input("User name: ")
        password = input("Password: ")
        data = json.dumps({"login": self.login, "name": name, "password": password})
        req = self.form_request_line(data, "registry")
        if req:
            self.transfer(req)

    def log_in(self):
        self.login = input("Login name: ")
        password = input("Password: ")
        data = json.dumps({"login": self.login, "password": password})
        req = self.form_request_line(data, "login")
        if req:
            self.transfer(req)

    def log_out(self):
        if not self.state == "logged":
            return
        data = json.dumps({"auth_token": self.auth_token})
        req = self.form_request_line(data, "logout")
        if req:
            self.transfer(req)

    def post_message(self, msg, group):
        if not self.state == "logged":
            return
        data = json.dumps({"auth_token": self.auth_token, "text": msg})
        req = self.form_request_line(data, f"message/{group}")
        if req:
            self.transfer(req)

    def receive_forever(self, success):
        while True:
            resp = self.get_response()
            if resp and resp.status != '200' and resp.status != '204':
                print(resp.reason)
            else:
                data = json.loads(resp.body.decode('utf-8'))
                if data["status"] == "user_created":
                    print(resp.reason)
                elif data["status"] == "logged in":
                    self.auth_token = data["token"]
                    self.state = "logged"
                    print(self.state)
                elif data["status"] == "logged out":
                    self.auth_token = None
                    self.login = None
                    self.state = "connected"
                elif data["status"] == "message":
                    print(data["text"])
                    continue
                elif data["status"] == "sent":
                    pass
            success.set()

    def transfer(self, req):
        try:
            self.sock_fd.send(req.encode())
        except socket.error:
            logging.warning("cant send to server")
        self.rcv_success.wait()
        self.rcv_success.clear()

    def form_request_line(self, data, path):
        if self.server_host and self.server_port:
            target = "https://" + f"{self.server_host}" + f":{self.server_port}/{path}"
            req = f"POST {target} HTTP/1.1\r\nHost: server\r\nUser-Agent: demo-client\r\nContent-Length:{len(data)}\r" \
                  f"\nAccept: application/json\r\n\n{data}"
            return req
        return None

    def get_response(self):
        buffer = self.sock_fd.makefile('rb')
        ver, status, reason = self.parse_response_line(buffer)
        headers = self.parse_headers(buffer)
        size = headers.get('Content-Length')
        if not size:
            body = None
        else:
            body = buffer.read(int(size))
        buffer.flush()
        buffer.close()
        return Response(status, reason, headers, body)

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
    while True:
        if cl.state == "connected":
            answer = input("Register or Login?[r/l]")
            if answer == "r":
                cl.register()
            elif answer == "l":
                cl.log_in()
        if cl.state == "logged":
            answer = input("Logout or post message?[l/p]")
            if answer == "l":
                cl.log_out()
            if answer == "p":
                msg = input("Type here:")
                cl.post_message(msg, "all")
