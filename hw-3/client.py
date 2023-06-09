"""
HW 3
"""
import time
import threading
from threading import Thread
import socket
import struct
import atexit

# Colors
RED_COLOR = "\033[0;31m"
GREEN_COLOR = "\033[0;32m"
YELLOW_COLOR = "\033[0;33m"
BLUE_COLOR = "\033[0;34m"
PURPLE_COLOR = "\033[0;35m"
CYAN_COLOR = "\033[0;36m"
RESET_COLOR = "\033[0;0m"

# Message types
DEFINE_USERNAME = 2
SEND_MESSAGE = 3

# Message subtypes
USER_RELATED = 1
SERVER_RELATED = 0

disconnect_client = False
server_addresses = [('127.0.0.1', 12345), ('127.0.0.1', 12346), ('127.0.0.1', 12347), ('127.0.0.1', 12348),
                    ('127.0.0.1', 12349)]  # Predefined addresses for the servers

messages = []  # List of messages received.
sockets = []  # List of sockets

stop_event = threading.Event()


def create_socket():
    """
    Creates a socket
    :return:
    """
    # Create a socket and connect to the server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sockets.append(sock)
    return sock


@atexit.register
def close_sockets():
    for s in sockets:
        s.close()


def send_message(sock, subtype=1):
    # TODO subtype may change in the next assignment
    """
    Sends a message to (type=3)
    :param subtype:
    :param sock: socket
    :return:
    """

    target_username = input('Enter the username of the recipient:').strip()
    message = input('Enter your message:').strip()

    sublen = len(target_username)
    length = len(message) + sublen

    # Create the message type = 3
    header = struct.pack('>BBHH', SEND_MESSAGE, subtype, length, sublen)
    packed_message = header + f"{target_username}{message}".encode()
    sock.sendall(packed_message)


def receive_message(sock):
    while not stop_event.is_set():
        # Receive the header
        try:
            header = sock.recv(6)

            # Unpack the header
            if len(header):
                msg_type, subtype, length, sublen = struct.unpack('>BBHH', header)

                # Receive the data
                data = sock.recv(length).decode()
                msg_from = data[sublen:]
                sender_username, msg = msg_from.split('\0')

                messages.append(f"{GREEN_COLOR}{sender_username}: {RESET_COLOR}{msg}")
        except ConnectionAbortedError:
            print('Connection aborted.')
            break
        except Exception as e:
            print(e)
            break


def create_username(sock, username):
    """
    Creates a username for the client
    :param sock: socket
    :param username: username
    :return:
    """
    length = len(username)
    sublen = 0  # Just for now sublen is 0 (it's related to the next assignment)

    # Create the message type = 2
    header = struct.pack('>BBHH', DEFINE_USERNAME, USER_RELATED, length, sublen)
    message = header + username.encode()
    sock.send(message)


def main():
    # Choose a server to connect to
    server_addr_index = input("Enter the index of the server to connect to (0-4):").strip()

    # Create a socket and connect to the server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    sockets.append(sock)
    sock.connect(server_addresses[int(server_addr_index)])

    # Create a username
    username = input('Enter your username:').strip()
    create_username(sock, username)

    # Start a thread to receive messages
    receive_thread = Thread(target=receive_message, args=(sock,))
    receive_thread.start()

    while True:
        read_or_write = input(
            CYAN_COLOR + '1. Enter 1 - to send a message.\n2. Enter 2 - to read new messages. \n3. Enter 3 - to exit.\n' + RESET_COLOR).strip()
        if read_or_write == '1':
            # Start a thread to send messages
            send_thread = Thread(target=send_message, args=(sock,))
            send_thread.start()
            send_thread.join()
        elif read_or_write == '2':
            if len(messages) == 0:
                print('\033[0;32mYou have no messages.\033[0;0m')
            else:
                # Print the messages
                for msg in messages:
                    print(msg)
                    messages.pop()
        elif read_or_write == '3':
            sock.close()
            break

    receive_thread.join()


def exit_handler():
    """
    Closes the sockets
    :return:
    """
    print('Closing the sockets...')
    for s in sockets:
        s.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted.')
    except ConnectionRefusedError:
        print('Connection refused.')
    except Exception as e:
        print('Exception occurred.', e)
    finally:
        stop_event.set()
        exit_handler()
