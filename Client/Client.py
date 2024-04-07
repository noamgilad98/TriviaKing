import socket
import threading
import sys

UDP_PORT = 13117  # The UDP port the client listens on for server announcements

def listen_udp(player_name):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind(('', UDP_PORT))

    while True:
        try:
            data, addr = udp_socket.recvfrom(1024)  # Buffer size of 1024 bytes
            if data.startswith(b'\xab\xcd\xdc\xba\x02'):  # Check for magic cookie and message type
                server_name = data[5:37].strip().decode()
                server_port = int.from_bytes(data[37:39], 'big')
                print(f'Received offer from server "{server_name}" at address {addr[0]}, attempting to connect...')
                tcp_client(addr[0], server_port, player_name)
        except Exception as e:
            print(f'Error in UDP communication: {e}')

def tcp_client(server_ip, server_port, player_name):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
            tcp_socket.connect((server_ip, server_port))
            tcp_socket.sendall(f"{player_name}\n".encode())  # Send player name followed by a newline

            while True:
                data = tcp_socket.recv(1024).decode()
                if not data:
                    break
                print(data, end='')

                if 'True or false' in data:  # Assuming the client needs to answer trivia questions
                    answer = input()  # Get user input for the answer
                    tcp_socket.sendall(f"{answer}\n".encode())

    except Exception as e:
        print(f'Error connecting to server: {e}')
    finally:
        print('Server disconnected, listening for offer requests...')

def main():
    player_name = input("Enter your player name: ")
    threading.Thread(target=listen_udp, args=(player_name,)).start()

if __name__ == '__main__':
    main()
