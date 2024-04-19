import socket
import threading
import select
import sys
import uuid
import random


# Import platform-specific libraries for capturing key presses
if sys.platform == 'win32':
    import msvcrt
else:
    import tty
    import termios


def get_keypress():
    valid_keys = {'T', 'Y', '1', 'F', 'N', '0'}
    while True:
        if sys.platform == 'win32':
            key = msvcrt.getch().decode().upper()
        else:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                key = sys.stdin.read(1).upper()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        if key in valid_keys:
            return key


class TriviaClient:
    UDP_PORT = 13117
    BUFFER_SIZE = 1024
    PLAYER_NAMES = ['QuizzicalQuokka', 'BrainyBison', 'AstuteAlpaca', 'SavvySeahorse', 'CleverCobra']

    def __init__(self):
        base_name = random.choice(self.PLAYER_NAMES)
        unique_id = str(uuid.uuid4())[:8]  # Increase length for more uniqueness
        self.player_name = f"{base_name}_{unique_id}"
        self.tcp_socket = None

    def listen_udp(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
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
        # This flag controls the loop and is set to False when the game should end.
        self.game_running = True

        # Thread for handling keypresses
        keypress_thread = threading.Thread(target=self.handle_keypress)
        keypress_thread.start()

        # Main loop for handling incoming messages
        try:
            while self.game_running:
                ready = select.select([self.tcp_socket], [], [], 0.1)
                if ready[0]:
                    data = self.tcp_socket.recv(self.BUFFER_SIZE).decode()
                    if data:
                        print(data, end='')
                        if "Game over!" in data:
                            print("Server disconnected, listening for offer requests...")
                            self.game_running = False  # Stop the game loop
        finally:
            self.tcp_socket.close()
            keypress_thread.join()  # Wait for the keypress thread to finish

    def handle_keypress(self):
        while self.game_running:
            answer = get_keypress()
            if self.game_running:  # Check again in case the game ended while waiting for a key press
                self.tcp_socket.sendall(f"{answer}\n".encode())


def main():
    client = TriviaClient()
    threading.Thread(target=client.listen_udp).start()


if __name__ == '__main__':
    main()