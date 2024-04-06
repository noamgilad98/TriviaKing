import socket
import threading
import sys

UDP_PORT = 13117

def listen_udp():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    udp_socket.bind(('', UDP_PORT))
    while True:
        data, addr = udp_socket.recvfrom(1024)
        # Process UDP packet
        if data.startswith(b'\xab\xcd\xdc\xba\x02'):
            server_name = data[5:37].strip().decode()
            server_port = int.from_bytes(data[37:39], 'big')
            print(f'Received offer from server "{server_name}" at address {addr[0]}, attempting to connect...')
            tcp_client(addr[0], server_port)

def tcp_client(server_ip, server_port):
    try:
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((server_ip, server_port))
        while True:
            data = tcp_socket.recv(1024)
            if not data:
                break
            print(data.decode(), end='')
    except Exception as e:
        print(f'Error connecting to server: {e}')
    finally:
        print('Server disconnected, listening for offer requests...')
        listen_udp()

def main():
    threading.Thread(target=listen_udp).start()

if __name__ == '__main__':
    main()
