# implementing 3-tier structure: Hall --> Room --> Clients; 
# 14-Jun-2013

import socket
import pickle

HEADER_LENGTH = 20

# prepare the data by adding a size to the front and pickled data at the end
def send_pickle(data):
    msg = pickle.dumps(data)
    msg = bytes(f"{len(msg):<{HEADER_LENGTH}}", 'utf-8')+msg
    return msg


# class Hall:
#     def __init__(self):
#         self.rooms = {} # {room_name: Room}
#         self.room_player_map = {} # {playerName: roomName}

#     def welcome_new(self, new_player):
#         new_player.socket.sendall(b'Welcome to pychat.\nPlease tell us your name:\n')

#     def list_rooms(self, player):
        
#         if len(self.rooms) == 0:
#             msg = 'Oops, no active rooms currently. Create your own!\n' \
#                 + 'Use [<join> room_name] to create a room.\n'
#             player.socket.sendall(msg.encode())
#         else:
#             msg = 'Listing current rooms...\n'
#             for room in self.rooms:
#                 msg += room + ": " + str(len(self.rooms[room].players)) + " player(s)\n"
#             player.socket.sendall(msg.encode())
    
#     def handle_msg(self, player, msg):
        
#         instructions = b'Instructions:\n'\
#             + b'[<list>] to list all rooms\n'\
#             + b'[<join> room_name] to join/create/switch to a room\n' \
#             + b'[<manual>] to show instructions\n' \
#             + b'[<quit>] to quit\n' \
#             + b'Otherwise start typing and enjoy!' \
#             + b'\n'

#         print(player.name + " says: " + msg)
#         if "name:" in msg:
#             name = msg.split()[1]
#             player.name = name
#             print("New connection from:", player.name)
#             player.socket.sendall(instructions)

#         elif "<join>" in msg:
#             same_room = False
#             if len(msg.split()) >= 2: # error check
#                 room_name = msg.split()[1]
#                 if player.name in self.room_player_map: # switching?
#                     if self.room_player_map[player.name] == room_name:
#                         player.socket.sendall(b'You are already in room: ' + room_name.encode())
#                         same_room = True
#                     else: # switch
#                         old_room = self.room_player_map[player.name]
#                         self.rooms[old_room].remove_player(player)
#                 if not same_room:
#                     if not room_name in self.rooms: # new room:
#                         new_room = Room(room_name)
#                         self.rooms[room_name] = new_room
#                     self.rooms[room_name].players.append(player)
#                     self.rooms[room_name].welcome_new(player)
#                     self.room_player_map[player.name] = room_name
#             else:
#                 player.socket.sendall(instructions)

#         elif "<list>" in msg:
#             self.list_rooms(player) 
#         elif "<manual>" in msg:
#             player.socket.sendall(instructions)
#         elif "<quit>" in msg:
#             player.socket.sendall(QUIT_STRING.encode())
#             self.remove_player(player)

#         else:
#             # check if in a room or not first
#             if player.name in self.room_player_map:
#                 self.rooms[self.room_player_map[player.name]].broadcast(player, msg.encode())
#             else:
#                 msg = 'You are currently not in any room! \n' \
#                     + 'Use [<list>] to see available rooms! \n' \
#                     + 'Use [<join> room_name] to join a room! \n'
#                 player.socket.sendall(msg.encode())
    
#     def remove_player(self, player):
#         if player.name in self.room_player_map:
#             self.rooms[self.room_player_map[player.name]].remove_player(player)
#             del self.room_player_map[player.name]
#         print("Player: " + player.name + " has left\n")

class User:
    def __init__(self, name, uuid, sock):
        self.name = name
        self.full_name = name
        self.uuid = uuid
        self.socket_list = [sock]

    def get_name(self):
        return self.name

    def get_uuid(self):
        return self.uuid

    def get_sockets(self):
        return self.socket_list

    def add_socket(self, sock):
        if sock not in self.socket_list:
            self.socket_list.append(sock)

    def erase_socket(self, sock):
        if sock in self.socket_list:
            self.socket_list.remove(sock)
        return len(self.socket_list)
    
    def send_msg(self, msg):
        for socket in self.socket_list:
            socket.send(send_pickle(msg))

class Room:
    def __init__(self, users, name, uuid):
        self.users = users
        self.name = name
        self.uuid = uuid

    def add_user(self, user):
        # check to make sure not adding the same user to the room twice
        if user.get_uuid() not in self.user_uuids_list():
            self.users.append(user)

    def user_names_list(self):
        user_list = []
        for user in self.users:
            user_list.append(user.get_name())
        return user_list
    
    def user_uuids_list(self):
        user_list = []
        for user in self.users:
            user_list.append(user.get_uuid())
        return user_list
    
    def send_room_update(self, msg):
        message = {'sender': 'server', 'room_uuid': self.uuid, 'room_name': self.name, 
                   'recipients': self.user_names_list(), 'recipients_uuids': self.user_uuids_list(), 
                   'message': msg}
        self._send_all(message)

    def send_broadcast(self, from_player, msg):
        message = {'sender': from_player.name, 'room_uuid': self.uuid, 'message': msg }
        self._send_all(message)

    def remove_user(self, user):
        # might want to send this to the person leaving the room too.
        if user in self.users:
            self.users.remove(user)
            self.send_room_update(f"{user.get_name()} has left the room")
        return self.users

    def room_closing(self):
        message = {'sender': 'system', 'cmd': 'room_closed', 'room_uuid': self.uuid, 'message': 'All Users exited chat' }
        self._send_all(message)
        for user in self.users:
            self.users.remove(user)

    def check_for_user(self, u_uuid):
        for user in self.users:
            if user.get_uuid() == u_uuid:
                return True
        return False

    def _send_all(self, message):
        for user in self.users:
            user.send_msg(message)
