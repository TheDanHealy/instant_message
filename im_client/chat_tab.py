import queue
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QColor

recv_msg_queue = queue.Queue()
send_msg_queue = queue.Queue()
sys_msg_queue = queue.Queue()


class newChatTab(QtWidgets.QWidget):

    def __init__(self, parent, msg):
        super().__init__()
        self.super_chat_widget = parent
        self.tabName = msg['recipients'][0]

        self.subscribed_room = msg['room_uuid']
        self.subscribed_room_recipients = msg['recipients']
        self.subscribed_room_recipients_uuids = msg['recipients_uuids']

        group = QtWidgets.QGroupBox('')
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(group)

        self.gridLayout_2 = QtWidgets.QGridLayout(group)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout_chatDisp = QtWidgets.QGridLayout()
        self.gridLayout_chatDisp.setObjectName("gridLayout_chatDisp")
        self.chatAreaEdit = QtWidgets.QTextEdit()
        self.chatAreaEdit.setObjectName("chatAreaEdit")
        self.gridLayout_chatDisp.addWidget(self.chatAreaEdit, 0, 0, 1, 1)
        self.gridLayout_chatSend = QtWidgets.QGridLayout()
        self.gridLayout_chatSend.setObjectName("gridLayout_chatSend")
        self.endChatButton = QtWidgets.QPushButton()
        self.endChatButton.setObjectName("endChatButton")
        self.gridLayout_chatSend.addWidget(self.endChatButton, 0, 2, 1, 1)
        self.sendButton = QtWidgets.QPushButton()
        self.sendButton.setMaximumSize(QtCore.QSize(80, 16777215))
        self.sendButton.setObjectName("sendButton")
        self.gridLayout_chatSend.addWidget(self.sendButton, 0, 1, 1, 1)
        self.cmdEdit = QtWidgets.QLineEdit()
        self.cmdEdit.setObjectName("cmdEdit")
        self.gridLayout_chatSend.addWidget(self.cmdEdit, 0, 0, 1, 1)
        self.gridLayout_chatDisp.addLayout(self.gridLayout_chatSend, 1, 0, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout_chatDisp, 0, 0, 1, 1)

        _translate = QtCore.QCoreApplication.translate
        self.endChatButton.setText(_translate("MainWindow", "End Chat"))
        self.sendButton.setText(_translate("MainWindow", "Send"))

        self.sendButton.clicked.connect(self.send_button_clicked)
        self.endChatButton.clicked.connect(self.end_chat_button_clicked)
        self.cmdEdit.returnPressed.connect(self.cmd_edit_return_pressed)

        self.cmdEdit.setFocus()
        self.chatAreaEdit.setReadOnly(True)

    def get_tab_data(self):
        return (self.subscribed_room, self.subscribed_room_recipients)

    def send_button_clicked(self):
        self.cmd_edit_return_pressed()

    def end_chat_button_clicked(self):
        sys_msg_queue.put_nowait(('blue', f"You commanded an exit from chat"))
        # if connected to a room, just send the message
        message = {'uuid': self.subscribed_room, 'cmd': 'exit_chat', 'message': 'End Chat', 'recipients': [], 'recipients_uuids': []}
        # queue the message
        send_msg_queue.put_nowait(message)
        self._end_chat()

    def cmd_edit_return_pressed(self):
        new_msg = self.cmdEdit.text()
        if new_msg != '':

            # private messages can be sent by double clicking on the user.
            # This extracts the recipients
            tags, message = self._extract_nametags(new_msg)

            # check to make sure the tag is a connected user
            tag_check = False
            tags_uuid = []
            for tag in tags:
                for name_uuid, name in self.connected_user_list.items():
                    if tag == name:
                        tags_uuid.append(name_uuid)
                        tag_check = True

            if self.subscribed_room == None:
                if tag_check and tags != []:
                    # creating a new chat, so create a new uuid
                    message = {'uuid': str(uuid.uuid1()), 'cmd': 'new_chat', 'message': message, 'recipients': tags, 'recipients_uuids': tags_uuid}
                    # queue the message
                    send_msg_queue.put_nowait(message)
                else:
                    sys_msg_queue.put_nowait(('red',"Not connected to a user, double click on user in user list"))
            else:
                # if connected to a room, just send the message
                message = {'uuid': self.subscribed_room, 'message': message, 'recipients': tags, 'recipients_uuids': tags_uuid}
                # queue the message
                send_msg_queue.put_nowait(message)


        self.cmdEdit.clear()

    def _end_chat(self):
        self.subscribed_room = None
        self.subscribed_room_recipients = []
        self.subscribed_room_recipients_uuids = []
        idx = self.super_chat_widget.currentIndex()
        self.super_chat_widget.removeTab(idx)


    def sys_message(self, msg):
        
        color = msg[0]
        sys_msg = msg[1]

        self.chatAreaEdit.setTextColor(QColor(color))
        self.chatAreaEdit.append('system msg> ' + sys_msg)
        self.chatAreaEdit.setTextColor(QColor('black'))

    def new_messages(self, message):

        if 'message' in message:
            self.chatAreaEdit.append(f"{message['sender']} > {message['message']}")
            
        if 'cmd' in message and message['cmd'] == 'room_closed':
            self.chatAreaEdit.append(f"server> The users have left the chat.")
            self._end_chat()

        if 'error' in message:
            self.chatAreaEdit.append(f"server> {message['error']}")


    # function to find nametags in the leading part of a string 
    def _extract_nametags(self, text): 
        
        # initializing hashtag_list variable 
        hashtag_list = [] 
        
        # splitting the text into words 
        for word in text.split(): 
            
            # checking the first charcter of every word 
            if word[0] == '@': 
                
                # adding the word to the hashtag_list 
                hashtag_list.append(word[1:])
            else:
                break
        
        s = text
        for tag in hashtag_list:
            s = s.replace('@'+tag, '')
        s = s.lstrip()

        return (hashtag_list, s)  
