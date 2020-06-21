import signal
import sys
import threading
from email.parser import Parser
import json
import logging
import socket
from http_classes.http_classes import Request, Response, HTTPError, MAX_HEADERS, MAX_LINE
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5 import QtWidgets, uic
from gui_templates.login import Ui_MainWindow
from gui_templates.registration import Ui_MainWindow as Ui_Form
from gui_templates.chatWindow import Ui_MainWindow as Ui_Chat
from gui_templates.group import MyApp as Ui_Group
import gettext


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

class RegWindow(QtWidgets.QMainWindow, Ui_Form):
    def __init__(self, *args, **kwargs):
        super(RegWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

class ChatWindow(QtWidgets.QMainWindow, Ui_Chat):
    def __init__(self, *args, **kwargs):
        super(ChatWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

__all__ = ['Client']


# logging.basicConfig(format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s',
#                    level=logging.DEBUG)




class Client(QObject):
    incoming_text = pyqtSignal(str)
    show_chat = pyqtSignal()
    show_group = pyqtSignal(set)

    @pyqtSlot()
    def run_group_gui(self):
        for x in self.chats:
            self.window4.addWidget(x)
            self.window4.widget.lblName.clicked.connect(self.choose_group_gui)
        self.window4.show()
        self.window.hide()

    @pyqtSlot()
    def run_chat_gui(self):
        self.window3.show()
        self.window4.hide()

    def __init__(self, *args, **kwargs):
        super(Client, self).__init__(*args, **kwargs)
        self.server_host = None
        self.server_port = None
        self.login = None
        self.auth_token = None
        self.sock_fd = None
        self.state = "start"
        self.chats = None
        self.shm = None
        self.gui = None
        self.receiver = None
        self.rcv_success = threading.Event()
        self.rcv_success.clear()
        self.read_shut = threading.Event()
        self.app = QtWidgets.QApplication(sys.argv)
        self.current_chat = None
        self.window = MainWindow()
        self.window.pushButton_3.clicked.connect(self.exit_gui)
        self.window2 = RegWindow()
        self.window3 = ChatWindow()
        self.window4 = Ui_Group()
        self.window3.pushButton_2.clicked.connect(self.log_out_gui)
        self.window3.pushButton.clicked.connect(self.send_gui)
        self.window3.pushButton_3.clicked.connect(self.back_to_choose_group_gui)
        self.show_chat.connect(self.run_chat_gui)
        self.show_group.connect(self.run_group_gui)

    def exit_gui(self):
        self.disconnect()
        sys.exit()


    def back_to_choose_group_gui(self):
        self.window4.show()
        self.window3.hide()
        self.window3.plainTextEdit.clear()
        self.window3.textBrowser.clear()

    def choose_group_gui(self):
        sender = self.sender()
        self.current_chat = sender.text()
        self.run_chat_gui()

    def put_txt_gui(self, str):
        self.window3.textBrowser.append("\n" + str)

    def send_gui(self):
        group = self.current_chat
        msg = self.window3.plainTextEdit.toPlainText()
        self.window3.plainTextEdit.clear()
        print(msg)
        data = json.dumps({"auth_token": self.auth_token, "text": msg})
        req = self.form_request_line(data, f"message/{group}")
        if req:
            self.transfer(req)

    def log_out_gui(self):
        data = json.dumps({"auth_token": self.auth_token})
        req = self.form_request_line(data, "logout")
        if req:
            self.transfer(req)
        self.window4 = Ui_Group()
        self.window3.hide()
        self.window3.plainTextEdit.clear()
        self.window3.textBrowser.clear()
        self.window.show()

    def run_gui(self):
        self.incoming_text.connect(self.put_txt_gui)
        self.window.show()
        self.window.pushButton.clicked.connect(self.log_in_gui)
        self.window.pushButton_2.clicked.connect(self.reg_gui)
        self.app.exec()

    def reg_gui(self):
        self.window.hide()
        self.window2.show()
        self.window2.pushButton_2.clicked.connect(self.registration_gui)

    def registration_gui(self):
        self.login = self.window2.lineEdit.text()
        name = self.window2.lineEdit_3.text()
        password = self.window2.lineEdit_2.text()
        data = json.dumps({"login": self.login, "name": name, "password": password})
        req = self.form_request_line(data, "registry")
        self.window2.hide()
        self.window.show()
        if req:
            self.transfer(req)




    def log_in_gui(self):
        self.login = self.window.lineEdit.text()
        password = self.window.lineEdit_2.text()
        data = json.dumps({"login": self.login, "password": password})
        req = self.form_request_line(data, "login")
        if req:
            self.transfer(req)

    def connect_to_server(self, host, port):
        try:
            self.sock_fd = socket.create_connection((host, port))
            self.server_host = host
            self.server_port = port
            self.receiver = threading.Thread(target=self.receive_forever, args=(self.rcv_success, self.read_shut, ))
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
        name = input(_("User name: "))
        password = input(_("Password: "))
        data = json.dumps({"login": self.login, "name": name, "password": password})
        req = self.form_request_line(data, "registry")
        if req:
            self.transfer(req)

    def log_in(self):
        self.login = input(_("Login name: "))
        password = input(_("Password: "))
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
                    #self.window3.show()

                    self.state = "logged"
                    self.chats = set(data["chats"])
                    if self.gui:
                        self.show_group.emit(self.chats)
                    else:
                        print(_('Your chats: {0}').format(self.chats))
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
                    if self.gui:
                        self.incoming_text.emit(data["text"])
                    else:
                        print(data["text"])
                    continue

                elif data["status"] == "sent":
                    logging.info("sent a message")
                    if self.gui:
                        self.incoming_text.emit(data["text"])
                    print(data["text"])

                elif data["status"] == "create group":
                    print(resp.reason)
                    self.chats.add(data["name"])

                elif data["status"] == "added to group":
                    print(_('You have been added to group: {0}').format(data['name']))
                    self.chats.add(data["name"])
                    continue
                elif data["status"] == "delete group":
                    print(resp.reason)
                    self.chats.discard(data["name"])
                elif data["status"] == "group deleted":
                    print(_('group {0} has been deleted').format(data['name']))
                    self.chats.discard(data["name"])
                    continue
                elif data["status"] == "added":
                    print(_('users {0} added to {1}').format(data["users"], data["name"]))
                elif data["status"] == "users added":
                    print(_('users {0} added to {1}').format(data["users"], data["name"]))
                    if self.login in data["users"]:
                        self.chats.add(data["name"])
                    continue
                elif data["status"] == "excluded":
                    print(_('users {0} excluded from {1}').format(data["users"], data["name"]))
                elif data["status"] == "users excluded":
                    print(_('users {0} excluded from {1}').format(data["users"], data["name"]))
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
        ver = None
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


el = gettext.translation('base', localedir='locales', languages=['ua'])
el.install()
_ = el.gettext

cl = Client()


def handler(sig, frame):
    cl.disconnect()
    sys.exit()


signal.signal(signal.SIGINT, handler)

if cl.connect_to_server('localhost', 8000):
    ans = input(_("Gui y/n"))
    if ans == "y":
        cl.gui = True
    else:
        cl.gui = False
        ans = input("Language: en [1], ua [2]")
        if ans == "1":
            el = gettext.translation('base', localedir='locales', languages=['en'])
            el.install()
            _ = el.gettext
    while True:
        try:
            if not cl.gui:
                if cl.state == "connected":
                    answer = input(_("Register or Login?[r/l]"))
                    if answer == "r":
                        cl.register()
                    elif answer == "l":
                        cl.log_in()
                if cl.state == "logged":
                    answer = input(_("Logout, post message or group action?[l/p/g]"))
                    if answer == "l":
                        cl.log_out()
                    if answer == "p":
                        group = input(_("Which group?"))
                        msg = input(_("Type here: "))
                        print(msg)
                        cl.post_message(msg, group)
                    if answer == "g":
                        reply = input(_("Create group, delete group, add users or exclude users?[c/d/a/e]: "))
                        if reply == "c":
                            msg = input(_("Group name: "))
                            users = input(_("List the users:"))
                            users = users.split(",")
                            cl.create_group(msg, users)
                        elif reply == "d":
                            msg = input(_("Group name: "))
                            cl.delete_group(msg)
                        elif reply == "a":
                            msg = input(_("Group name: "))
                            users = input(_("List the users:"))
                            users = users.split(",")
                            cl.add_to_group(msg, users)
                        elif reply == "e":
                            msg = input(_("Group name: "))
                            users = input(_("List the users:"))
                            users = users.split(",")
                            cl.exclude_from_group(msg, users)
            if cl.gui:
                cl.run_gui()

        except Exception as e:
            cl.disconnect()
            raise e

