import socket
import threading
import select

class TriviaClient:
    UDP_PORT = 13117
    BUFFER_SIZE = 1024

    def __init__(self, player_name):
        self.player_name = player_name
        self.tcp_socket = None

    def listen_udp(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # Add this line
        udp_socket.bind(('', self.UDP_PORT))

        while True:
            data, addr = udp_socket.recvfrom(self.BUFFER_SIZE)
            if data.startswith(b'\xab\xcd\xdc\xba\x02'):
                server_name = data[5:37].strip().decode()
                server_port = int.from_bytes(data[37:39], 'big')
                print(f'Received offer from server "{server_name}" at address {addr[0]}, attempting to connect...')
                self.connect_tcp(addr[0], server_port)

    def connect_tcp(self, server_ip, server_port):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.tcp_socket.connect((server_ip, server_port))
            self.tcp_socket.sendall(f"{self.player_name}\n".encode())
            self.game_loop()
        except Exception as e:
            print(f'Error connecting to server: {e}')
        finally:
            self.tcp_socket.close()

    def game_loop(self):
        while True:
            ready = select.select([self.tcp_socket], [], [], 0.1)
            if ready[0]:
                data = self.tcp_socket.recv(self.BUFFER_SIZE).decode()
                if data:
                    print(data, end='')
                    if 'True or false' in data:  # Assuming the question format includes this string
                        answer = input()  # Get user input for the answer
                        self.tcp_socket.sendall(f"{answer}\n".encode())


def main():
    player_name = input("Enter your player name: ")
    client = TriviaClient(player_name)
    threading.Thread(target=client.listen_udp).start()

if __name__ == '__main__':
    main()
