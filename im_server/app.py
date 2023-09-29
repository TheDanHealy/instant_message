import os
import pickle
import socket
import select
import ssl

from im_util import User, Room, send_pickle, HEADER_LENGTH

## Static Definitions ##
IP = os.getenv('IM_BINDIP','0.0.0.0')
PORT = os.getenv('IM_BINDPORT',5100)
server_cert = os.getenv('IM_CERT','example.com.crt')
server_key = os.getenv('IM_KEY','example.com.key')

# List of sockets for select.select()
sockets_list = []

# List of connected clients - uuid as a key, value is user class
clients = {}

# List of current rooms - uuid will be the key, value is a dictionary with usernames and other things
master_room_dict = {}


# Handles message receiving
def receive_message(client_socket):

    try:
        # Receive our "header" containing message length, it's size is defined and constant
        message_header = client_socket.recv(HEADER_LENGTH)

        # If we received no data, client gracefully closed a connection, for example using socket.close() or socket.shutdown(socket.SHUT_RDWR)
        if not len(message_header):
            return False

        # Convert header to int value
        message_length = int(message_header.decode('utf-8').strip())

        # Read in message
        message_data = client_socket.recv(message_length)

        # convert message data back to object
        return pickle.loads(message_data)

    except:

        # If we are here, client closed connection violently, for example by pressing ctrl+c on his script
        # or just lost his connection
        # socket.close() also invokes socket.shutdown(socket.SHUT_RDWR) what sends information about closing the socket (shutdown read/write)
        # and that's also a cause when we receive an empty message
        return False

# socket has already closed, just need to clean up the data structures
def user_exit_cleanup(notified_socket):

    room_del_key_list = []

    # go through the clients and remove the socket from the socket lists
    for client_uuid, client_class in clients.items():
        if notified_socket in client_class.get_sockets():
            if client_class.erase_socket(notified_socket) == 0:
                # if it returned zero, then this user is disconnected on all of their
                #  sockets/computers

                # Remove user from all rooms
                for room_uuid, room_data in master_room_dict.items():
                    if len(room_data.remove_user(client_class)) < 2:
                        # if less than two users in room, send a closing room and remove the room
                        room_data.room_closing()
                        room_del_key_list.append(room_uuid)

                # if any rooms were tagged for deletion, remove them.
                for room_uuid in room_del_key_list:
                    del master_room_dict[room_uuid]

                # Remove from our list of users
                del clients[client_uuid]
                
                print('Closed final connection from: {}'.format(client_class.get_name()))

            else:
                # since this user has a non-zero socket list, it is still connected
                #  from another computer
                print('Closed non-final connection from: {}'.format(client_class.get_name()))
                pass

            # Remove from list for socket.socket()
            sockets_list.remove(notified_socket)

            # since this socket was assigned to this user, no need to keep searching
            break


# when the client list changes, the list goes out to all clients
def send_updated_client_list(clients):

    message = {'sender': 'server', 'connected_users': {}}

    for _, client_data in clients.items():
        message['connected_users'][client_data.get_uuid()] = client_data.get_name()

    # Iterate over connected clients and broadcast message
    for _, client_data in clients.items():
        client_data.send_msg(message)


def print_room_summary():
    print("room summary")
    for room_uuid, room_data in master_room_dict.items():
        print(f"room {room_data.name}, users {room_data.user_names_list()}")


if __name__ == "__main__":

    context = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=server_cert, keyfile=server_key)

    # Create a socket
    # socket.AF_INET - address family, IPv4, some otehr possible are AF_INET6, AF_BLUETOOTH, AF_UNIX
    # socket.SOCK_STREAM - TCP, conection-based, socket.SOCK_DGRAM - UDP, connectionless, datagrams, socket.SOCK_RAW - raw IP packets
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # SO_ - socket option
    # SOL_ - socket option level
    # Sets REUSEADDR (as a socket option) to 1 on socket
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind, so server informs operating system that it's going to use given IP and port
    # For a server using 0.0.0.0 means to listen on all available interfaces, useful to connect locally to 127.0.0.1 and remotely to LAN interface IP
    server_socket.bind((IP, PORT))

    # This makes server listen to new connections
    server_socket.listen()

    # List of sockets for select.select()
    sockets_list = [server_socket]

    print(f'Listening for connections on {IP}:{PORT}...')

    while True:

        # Calls Unix select() system call or Windows select() WinSock call with three parameters:
        #   - rlist - sockets to be monitored for incoming data
        #   - wlist - sockets for data to be send to (checks if for example buffers are not full and socket is ready to send some data)
        #   - xlist - sockets to be monitored for exceptions (we want to monitor all sockets for errors, so we can use rlist)
        # Returns lists:
        #   - reading - sockets we received some data on (that way we don't have to check sockets manually)
        #   - writing - sockets ready for data to be send thru them
        #   - errors  - sockets with some exceptions
        # This is a blocking call, code execution will "wait" here and "get" notified in case any action should be taken
        read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)


        # Iterate over notified sockets
        for notified_socket in read_sockets:

            # If notified socket is a server socket - new connection, accept it
            if notified_socket == server_socket:

                # Accept new connection
                # That gives us new socket - client socket, connected to this given client only, it's unique for that client
                # The other returned object is ip/port set
                tmp_client_socket, client_address = server_socket.accept()
                client_socket = context.wrap_socket(tmp_client_socket, server_side=True)
                #print("SSL established. Peer: {}".format(client_socket.getpeercert()))

                # Client should send his name right away, receive it
                connect_message = receive_message(client_socket)

                # Check for nothing first
                if connect_message is False:
                    continue

                # check for dictonary type
                if not isinstance(connect_message, dict):
                    continue

                # Check for user in the dictionary
                if 'name' not in connect_message:
                    continue

                # Check for uuid in the dictionary
                if 'my_uuid' not in connect_message:
                    continue

                # Add accepted socket to select.select() list
                sockets_list.append(client_socket)

                my_uuid = connect_message['my_uuid']

                if my_uuid in clients:
                    # This user is already connected from another computer (or the same computer)
                    #  just add the new socket to the user
                    clients[my_uuid].add_socket(client_socket)
                    print('Accepted secondary connection from {}:{}, username: {}'.format(*client_address, connect_message['name']))
                else:
                    # This user is not already connected, create new user and save in clients dict
                    # Also save user information, uuid is the dictionary key
                    clients[my_uuid] = User(connect_message['name'], my_uuid, client_socket)

                    print('Accepted new connection from {}:{}, username: {}'.format(*client_address, connect_message['name']))

                # Send updated client list to all of the clients
                send_updated_client_list(clients)

                print_room_summary()

            # Else existing socket is sending a message
            else:

                # Receive message
                message = receive_message(notified_socket)

                # If False, client disconnected, cleanup
                if message is False:
                    user_exit_cleanup(notified_socket)
                    send_updated_client_list(clients)
                    print_room_summary()
                    continue

                # Get user by notified socket, so we will know who sent the message
                user = None
                for _, cl_class in clients.items():
                    if notified_socket in cl_class.get_sockets():
                        user = cl_class
                        break

                if user == None:
                    continue

                if 'recipients' in message and message['recipients'] == 'all':
                    print(f"Recipients of ALL from {user.get_name()}, not allowed anymore")
                    notified_socket.send(send_pickle({'error': 'Recipient ALL not allowed, connect with a user with @user', 'sender': 'server'}))
                    continue

                if 'recipients' not in message and 'new_uuid' not in message:
                    print(f"No recipients specified from {user.get_name()}, not allowed anymore")
                    notified_socket.send(send_pickle({'error': 'Recipient ALL not allowed, connect with a user with @user', 'sender': 'server'}))
                    continue

                print(f'Received message from {user.get_name()}: {message["message"]}')

                # uuid in the message is the im/room/conversation uuid
                if 'uuid' in message:

                    # Check to see if this is a new one, rooms is a dict with im_uuid as the room name
                    room_uuid = message['uuid']
                    if room_uuid not in master_room_dict:
                        
                        if len(message['recipients']) == 0:
                            message = {'sender': 'system', 'cmd': 'error', 'room_uuid': room_uuid, 'message': 'Bad recipient list, no chat started' }
                            continue

                        # # check to see if recipients are already talking to someone
                        # busy = False
                        # for r_uuid, room in master_room_dict.items():
                        #     for rec_uuid in message['recipients_uuids']:
                        #         if room.check_for_user(rec_uuid):
                        #             busy = True

                        # if busy == True:
                        #     # send msg back sayings recipients busy
                        #     o_message = {'sender': 'system', 'cmd': 'busy', 'message': 'Recipients busy. They have been notified that you want to chat'}
                        #     user.send_msg(o_message)
                        #     # send msg to recipients saying sender wants to talk to them
                        #     o_message = {'sender': 'system', 'cmd': 'notice', 'message': f'{user.get_name()} wants to chat, but you are busy. End current chat ans tart new one with them'}

                        #     for _, usr in clients.items():
                        #         if usr.get_uuid() in message['recipients_uuids']:
                        #             usr.send_msg(o_message)

                        #     continue

                        print(f"new chat started between {user.get_name()} and {message['recipients']}")

                        master_room_dict[room_uuid] = Room([user], 'New Chat', room_uuid)

                        if isinstance(message['recipients_uuids'], list):
                            room_members = message['recipients_uuids']
                        else:
                            room_members = [message['recipients_uuids']]

                        for _, usr in clients.items():
                            for room_mem_uuid in room_members:
                                if room_mem_uuid == usr.get_uuid():
                                    master_room_dict[room_uuid].add_user(usr)

                        master_room_dict[room_uuid].send_room_update("Notice: This chat window will be deleted if either participant clicks the \"End Chat\" button")

                        print_room_summary()

                    else:
                        if 'cmd' in message:
                            if message['cmd'] == 'exit_chat':
                                # remove user from the room
                                room_del_key_list = []
                                if len(master_room_dict[room_uuid].user_names_list()) < 3:
                                    # if less than two users in room after this user exits, 
                                    #   send a closing room and remove the room
                                    master_room_dict[room_uuid].room_closing()
                                    room_del_key_list.append(room_uuid)

                                else:
                                    # now remove user from room
                                    master_room_dict[room_uuid].remove_user(user)

                                # if any rooms were tagged for deletion, remove them.
                                for u in room_del_key_list:
                                    del master_room_dict[u]

                                print_room_summary()
                                continue

                    if 'message' in message and message['message'] != '':
                        master_room_dict[room_uuid].send_broadcast(user, message['message'])

        # It's not really necessary to have this, but will handle some socket exceptions just in case
        for notified_socket in exception_sockets:

            user_exit_cleanup(notified_socket)
            send_updated_client_list(clients)
            print_room_summary()

