import socket
import threading
import time
import random

UDP_PORT = 13117
TCP_PORT = random.randint(1025, 65535)
SERVER_NAME = 'TriviaMaster'
MAGIC_COOKIE = b'\xab\xcd\xdc\xba'
OFFER_MESSAGE_TYPE = b'\x02'

def broadcast_udp():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        message = MAGIC_COOKIE + OFFER_MESSAGE_TYPE + SERVER_NAME.encode().ljust(32) + TCP_PORT.to_bytes(2, 'big')
        udp_socket.sendto(message, ('<broadcast>', UDP_PORT))
        time.sleep(1)

def handle_client(conn, addr):
    try:
        print(f'Connection established with {addr}')
        # Send welcome message
        conn.sendall(b'Welcome to the TriviaMaster server!\n')
        # Game logic here
        # For simplicity, we end after one interaction
        conn.close()
    except Exception as e:
        print(f'Error handling client {addr}: {e}')

def tcp_server():
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(('', TCP_PORT))
    tcp_socket.listen()
    print(f'Server started, listening on IP address {tcp_socket.getsockname()[0]} and port {TCP_PORT}')
    while True:
        conn, addr = tcp_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()

def main():
    threading.Thread(target=broadcast_udp).start()
    tcp_server()

if __name__ == '__main__':
    main()
