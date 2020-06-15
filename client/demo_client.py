import signal
import sys
import threading
from email.parser import Parser
import json
import logging
import socket
from http_classes.http_classes import Request, Response, HTTPError, MAX_HEADERS, MAX_LINE

__all__ = ['Client']


# logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
#                    level=logging.DEBUG)

class Client:
    def __init__(self):
        self.server_host = None
        self.server_port = None
        self.login = None
        self.auth_token = None
        self.sock_fd = None
        self.state = "start"
        self.chats = None
        self.receiver = None
        self.rcv_success = threading.Event()
        self.rcv_success.clear()
        self.read_shut = threading.Event()

    def connect_to_server(self, host, port):
        try:
            self.sock_fd = socket.create_connection((host, port))
            self.server_host = host
            self.server_port = port
            self.receiver = threading.Thread(target=self.receive_forever, args=(self.rcv_success, self.read_shut,))
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

    def disconnect(self):
        self.log_out()  # log out before disconnecting if necessary
        data = json.dumps({"state": "connected"})
        data.encode('utf-8')
        req = self.form_request_line(data, "disconnect")
        if req:
            self.transfer(req)
            self.sock_fd.shutdown(socket.SHUT_WR)
            self.read_shut.wait()
            self.sock_fd.shutdown(socket.SHUT_RD)
            self.sock_fd.close()

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

    def create_group(self, chat_name, users):
        if not self.state == "logged":
            return
        data = json.dumps({"auth_token": self.auth_token, "name": chat_name, "users": users})
        req = self.form_request_line(data, f"group/create")
        if req:
            self.transfer(req)

    def delete_group(self, chat_name):
        if not self.state == "logged":
            return
        data = json.dumps({"auth_token": self.auth_token, "name": chat_name})
        req = self.form_request_line(data, f"group/delete")
        if req:
            self.transfer(req)

    def add_to_group(self, chat_name, users):
        if not self.state == "logged":
            return
        data = json.dumps({"auth_token": self.auth_token, "name": chat_name, "users": users})
        req = self.form_request_line(data, f"group/add")
        if req:
            self.transfer(req)

    def exclude_from_group(self, chat_name, users):
        if not self.state == "logged":
            return
        data = json.dumps({"auth_token": self.auth_token, "name": chat_name, "users": users})
        req = self.form_request_line(data, f"group/exclude")
        if req:
            self.transfer(req)

    def post_message(self, msg, group):
        if not self.state == "logged":
            return
        data = json.dumps({"auth_token": self.auth_token, "text": msg})
        req = self.form_request_line(data, f"message/{group}")
        if req:
            self.transfer(req)

    def receive_forever(self, success, read_shut):
        read_shut.clear()
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
                    self.chats = set(data["chats"])
                    print(f"Your chats: {self.chats}")
                    print(self.state)

                elif data["status"] == "logged out":
                    self.auth_token = None
                    self.login = None
                    self.chats = None
                    self.state = "connected"

                elif data["status"] == "disconnect OK":
                    success.set()
                    logging.info("exited reading thread")
                    read_shut.set()
                    sys.exit()

                elif data["status"] == "incoming":
                    logging.info("got a message")
                    print(data["text"])
                    continue

                elif data["status"] == "sent":
                    logging.info("sent a message")
                    print(data["text"])

                elif data["status"] == "create group":
                    print(resp.reason)
                    self.chats.add(data["name"])

                elif data["status"] == "added to group":
                    print(f"you've been added to group {data['name']}")
                    self.chats.add(data["name"])
                    continue
                elif data["status"] == "delete group":
                    print(resp.reason)
                    self.chats.discard(data["name"])
                elif data["status"] == "group deleted":
                    print(f"group {data['name']} has been deleted")
                    self.chats.discard(data["name"])
                    continue
                elif data["status"] == "added":
                    print(f'users {data["users"]} added to {data["name"]}')
                elif data["status"] == "users added":
                    print(f'users {data["users"]} added to {data["name"]}')
                    if self.login in data["users"]:
                        self.chats.add(data["name"])
                    continue
                elif data["status"] == "excluded":
                    print(f'users {data["users"]} excluded from {data["name"]}')
                elif data["status"] == "users excluded":
                    print(f'users {data["users"]} excluded from {data["name"]}')
                    if self.login in data["users"]:
                        self.chats.discard(data["name"])
                    continue
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


def handler(sig, frame):
    cl.disconnect()
    sys.exit()


signal.signal(signal.SIGINT, handler)

if cl.connect_to_server('localhost', 8000):
    while True:
        try:
            if cl.state == "connected":
                answer = input("Register or Login?[r/l]")
                if answer == "r":
                    cl.register()
                elif answer == "l":
                    cl.log_in()
            if cl.state == "logged":
                answer = input("Logout, post message or group action?[l/p/g]")
                if answer == "l":
                    cl.log_out()
                if answer == "p":
                    group = input("Which group?")
                    msg = input("Type here: ")
                    print(msg)
                    cl.post_message(msg, group)
                if answer == "g":
                    reply = input("Create group, delete group, add users or exclude users?[c/d/a/e]: ")
                    if reply == "c":
                        msg = input("Group name: ")
                        users = input("List the users:")
                        users = users.split(",")
                        cl.create_group(msg, users)
                    elif reply == "d":
                        msg = input("Group name: ")
                        cl.delete_group(msg)
                    elif reply == "a":
                        msg = input("Group name: ")
                        users = input("List the users:")
                        users = users.split(",")
                        cl.add_to_group(msg, users)
                    elif reply == "e":
                        msg = input("Group name: ")
                        users = input("List the users:")
                        users = users.split(",")
                        cl.exclude_from_group(msg, users)
        except Exception as e:
            cl.disconnect()
            raise e
            break
