import errno
import json
import os
import pickle
import queue
import select
import socket
import ssl
import sys
import uuid

from chat_tab import newChatTab, recv_msg_queue, send_msg_queue, sys_msg_queue
from getpass import getpass
from im_ui_tabs import Ui_MainWindow
from ldap3 import Server, Connection, ALL, NTLM
from random import randint
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidgetItem
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from threading import Thread

## Static Definitions ##
ONE_USER_ACROSS_DEVICES = 0
HEADER_LENGTH = 20
IM_SERVER = os.getenv('IM_SERVER','example.com')
IM_PORT = os.getenv('IM_PORT', 5100)
LDAP_SERVER = os.getenv('LDAP_SERVER','ldap.example.com')
LDAP_DOMAIN = os.getenv('LDAP_DOMAIN','example.com')


ldap_username = input(f'Username for {LDAP_DOMAIN}: ')
ldap_password = getpass()
ldap_user = LDAP_DOMAIN+"\\"+ldap_username
conn = Connection(LDAP_SERVER, user=ldap_user, password=ldap_password, authentication=NTLM)
if not conn.bind():
    print("\nYour credentials were not authenticated successfully for user \""+ldap_username+"\"")
    sys.exit()

my_username = ldap_username+"@"+LDAP_DOMAIN
my_prefs_path = Path.home()
my_uuid = None

# prepare the data by adding a size to the front and pickled data at the end
def send_pickle(data):
    msg = pickle.dumps(data)
    msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", 'utf-8')+msg
    return msg


def check_valid_msg(message):
    # Check for nothing
    if message is False:
        return False

    # Check for nothing
    if message is None:
        return False

    # check for dictonary type
    if not isinstance(message, dict):
        return False

    # Check for user in the dictionary
    if 'sender' not in message:
        return False

    return True

class Ui_MainWindow_Extended(Ui_MainWindow):

    def setupUi_Extended(self, MainWindow):

        self.connected_user_list = {}

        self.server_status_label.setText("Server: Connected")
        self.server_status_label.setStyleSheet('background-color: green')

        # Signals:
        self.connectedUserListWidget.itemDoubleClicked.connect(self.connected_user_double_clicked)        
        self.new_msg_timer = QTimer()
        self.new_msg_timer.timeout.connect(self.process_new_messages)
        self.new_msg_timer.start(500)
        self.sys_msg_timer = QTimer()
        self.sys_msg_timer.timeout.connect(self.process_sys_messages)
        self.sys_msg_timer.start(500)

    def process_new_messages(self):
        while not recv_msg_queue.empty():
            message = recv_msg_queue.get_nowait()

            if 'room_uuid' in message and \
                'recipients' in message:
                
                t_info = self.get_all_tabs_info()
                if t_info and message['room_uuid'] in t_info.keys():
                    # existing room, process message
                    pass
                else:
                    # new room, create new tab
                    chat_name = ''
                    for name in message['recipients']:
                        #if name != my_username:
                        chat_name = name
                    self.chatTabWidget.addTab(newChatTab(self.chatTabWidget, message), chat_name)

            if 'message' in message and 'room_uuid' in message:
                self.send_msg_to_tab(message['room_uuid'], message)

            if 'cmd' in message and message['cmd'] == 'room_closed':
                self.send_msg_to_tab(message['room_uuid'], message)

            if 'connected_users' in message:
                sys_msg_queue.put_nowait(('orange',"Updated list of users"))
                self.connected_user_list = {}
                self.connectedUserListWidget.clear()
                for uuid, name in message['connected_users'].items():
                    if uuid == my_uuid:
                        self.me_label.setText(name)
                    else:
                        self.connected_user_list[uuid] = name
                        QListWidgetItem(name, self.connectedUserListWidget)
            
        self.new_msg_timer.start(500)

    def send_msg_to_tab(self, room_uuid, msg):
        num_tabs = self.chatTabWidget.count()

        tabs_data = None
        for idx in range(num_tabs):
            tab = self.chatTabWidget.widget(idx)
            (r_uuid, r_reciep) = tab.get_tab_data()
            if room_uuid == r_uuid:
                tab.new_messages(msg)
                return

    def get_all_tabs_info(self):
        num_tabs = self.chatTabWidget.count()

        tabs_data = {}

        for idx in range(num_tabs):
            tab = self.chatTabWidget.widget(idx)
            (r_uuid, r_reciep) = tab.get_tab_data()
            tabs_data[r_uuid] = r_reciep

        return tabs_data

    def check_for_dupe_room(self, new_chat_recipient):
        tabs_data = self.get_all_tabs_info()

        if tabs_data == {}:
            return False

        for r_uuid, r_recipts in tabs_data.items():
            if new_chat_recipient in r_recipts and len(r_recipts) <= 2:
                return True
        return False


    def connected_user_double_clicked(self, item):

        if self.check_for_dupe_room(item.text()) == True:
            #!! change focus to the chat window with this person
            pass
        else:
            for name_uuid, name in self.connected_user_list.items():
                if name == item.text():
                    #sys_msg_queue.put_nowait(('black',f"You selected {item.text()} to chat with you"))
                    # creating a new chat, so create a new uuid
                    message = {'uuid': str(uuid.uuid1()), 'cmd': 'new_chat', 'message': '', 'recipients': [name], 'recipients_uuids': [name_uuid]}
                    # queue the message
                    send_msg_queue.put_nowait(message)

    def process_sys_messages(self):

        if not sys_msg_queue.empty():
            (color, sys_msg) = sys_msg_queue.get_nowait()

            num_tabs = self.chatTabWidget.count()
            for idx in range(num_tabs):
                tab = self.chatTabWidget.widget(idx)
                tab.sys_message((color, sys_msg))

            if sys_msg.find("Server Closed") != -1:
                self.server_status_label.setText("Server: Disconnected")
                self.server_status_label.setStyleSheet('background-color: red')

                # don't want this status to be updated, so exit without restarting timer
                return

        self.sys_msg_timer.start(500)

def receive_thread_func(client_socket):

    # Now we want to loop over received messages (there might be more than one) and print them
    while True:
        # receive message dict from server
        try:
            # Receive our "header" containing message length, it's size is defined and constant
            message_header = client_socket.recv(HEADER_LENGTH)

            # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
            if not len(message_header):
                sys_msg_queue.put_nowait(('red',"Server Closed connection. Must exit and start again!"))
                return False

            # Convert header to int value
            message_length = int(message_header.decode('utf-8').strip())

            # Read in message
            message_data = client_socket.recv(message_length)
            # Add a check here for message length
            
            # convert message data back to object
            message = pickle.loads(message_data)

        except Exception as e:
            # Any other exception - something happened, exit
            sys_msg_queue.put_nowait(('red',"Server Closed socket receive exception. Must exit and start again!"))
            print('Reading error: {}'.format(str(e)))
            return False

        if check_valid_msg(message) == False:
            print("got a bad message")
            continue

        recv_msg_queue.put_nowait(message)

def send_thread_func(client_socket):

    while True:
            message = send_msg_queue.get(block=True, timeout=None)

            # Encode then send
            client_socket.send(send_pickle(message))


if __name__ == "__main__":

    if ONE_USER_ACROSS_DEVICES == False:
        my_uuid = str(uuid.uuid1())
    else:
        try:
            with open(os.path.join(my_prefs_path, '.chat_prefs.json')) as json_file:
                data = json.load(json_file)

            if 'user_uuid' in data:
                my_uuid = data['user_uuid']
        except:
            my_uuid = str(uuid.uuid1())

            with open(os.path.join(my_prefs_path, '.chat_prefs.json'), 'w') as outfile:
                json.dump({'user_uuid': my_uuid}, outfile)

    print(f'\nConnecting with as user \"{my_username}\"')

    context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    # Create a socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sclient_socket = context.wrap_socket(client_socket, server_side=False, server_hostname=IM_SERVER)

    # Connect to a given ip and port
    try:
        IP = socket.gethostbyname(IM_SERVER)
        sclient_socket.connect((IP, IM_PORT))

    except IOError as e:
        print("no server connection, exiting")
        sys.exit()

    # Set connection to non-blocking state, so .recv() call won;t block, just return some exception we'll handle
    sclient_socket.setblocking(True)

    # Prepare username and header and send them
    connect_data = {'name': my_username, 'my_uuid': my_uuid }
    sclient_socket.send(send_pickle(connect_data))

    receive_thread = Thread(target=receive_thread_func, args=(sclient_socket,), daemon=True).start()
    send_thread = Thread(target=send_thread_func, args=(sclient_socket,), daemon=True).start()

    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = Ui_MainWindow_Extended()
    ui.setupUi(MainWindow)
    ui.setupUi_Extended(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
