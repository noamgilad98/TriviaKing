import socket
import threading
import select
import sys
import uuid
import random

# ANSI Color Codes for styling output
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

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
    PLAYER_NAMES = ['Avi', 'Bar', 'Chen', 'Dana', 'Eli', 'Fadi', 'Gadi', 'Hadar', 'Ido', 'Jonathan', 'Kobi', 'Lior', 'Miri', 'Nir', 'Oren', 'Pini', 'Roni', 'Shai', 'Tal', 'Uri', 'Vlad', 'Yael', 'Ziv']
    PLAYER_SECONDARY_NAMES = ['Avraham', 'Ben-David', 'Cohen', 'Dahan', 'Eliyahu', 'Friedman', 'Golan', 'Haim', 'Ivri', 'Katz', 'Levi', 'Mizrahi', 'Nahari', 'Ovadia', 'Peretz', 'Rosenberg', 'Shalom', 'Tal', 'Uziel', 'Vaknin', 'Weiss', 'Xavier', 'Yosef', 'Zohar']

    def __init__(self):
        base_name = random.choice(self.PLAYER_NAMES)
        secondary_name = random.choice(self.PLAYER_SECONDARY_NAMES)
        unique_id = str(uuid.uuid4())[:8]  # Ensure uniqueness
        self.player_name = f"{base_name} {secondary_name} {unique_id}"
        self.tcp_socket = None

    def listen_udp(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        udp_socket.bind(('', self.UDP_PORT))
        print(f"{OKBLUE}Client started, listening for offer requests...{ENDC}")

        while True:
            try:
                data, addr = udp_socket.recvfrom(self.BUFFER_SIZE)
                if data.startswith(b'\xab\xcd\xdc\xba\x02'):
                    server_name = data[5:37].strip().decode()
                    server_port = int.from_bytes(data[37:39], 'big')
                    print(f'{OKGREEN}Received offer from server "{server_name}" at address {addr[0]}, attempting to connect...{ENDC}')
                    self.connect_tcp(addr[0], server_port)
            except Exception as e:
                print(f'{FAIL}Error receiving UDP broadcast: {e}{ENDC}')

    def connect_tcp(self, server_ip, server_port):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.tcp_socket.connect((server_ip, server_port))
            self.tcp_socket.sendall(f"{self.player_name}\n".encode())
            self.game_loop()
        except Exception as e:
            print(f'{FAIL}Error connecting to server: {e}{ENDC}')
        finally:
            self.tcp_socket.close()

    def game_loop(self):
        self.game_running = True
        keypress_thread = threading.Thread(target=self.handle_keypress)
        keypress_thread.start()

        try:
            while self.game_running:
                ready = select.select([self.tcp_socket], [], [], 0.1)
                if ready[0]:
                    data = self.tcp_socket.recv(self.BUFFER_SIZE).decode().strip()
                    if data:
                        print_from_server(data)
                        if "Game over!" in data:
                            print(f"{WARNING}Server disconnected, listening for offer requests...{ENDC}")
                            self.game_running = False
        finally:
            self.tcp_socket.close()

    def handle_keypress(self):
        while self.game_running:
            answer = get_keypress()
            if self.game_running:
                self.tcp_socket.sendall(f"{answer}\n".encode())
                
    

def main():
    client = TriviaClient()
    threading.Thread(target=client.listen_udp).start()

if __name__ == '__main__':
    main()

def print_from_server(text):
   #remove all two or more spaces and replace with one space
    text = ' '.join(text.split())
    print(text)
    