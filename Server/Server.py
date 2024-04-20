import socket
import struct
import threading
import random
import time

import TriviaQuestions

class TriviaServer:
    # ANSI Color Codes for console output formatting
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    # Configuration constants
    UDP_PORT = 13117  # UDP port used for broadcasting offers
    SERVER_NAME = 'Mystic'  # Name of the server
    MAGIC_COOKIE = 0xabcddcba  # Magic cookie for message validation
    OFFER_MESSAGE_TYPE = 0x02  # Message type indicating an offer message
    GAME_START_DELAY = 10  # Delay before starting the game after receiving clients

    def __init__(self):
        # Initializing server state
        self.mode_waiting_for_client = True  # Server is initially waiting for clients
        self.clients = []  # List of connected clients
        self.tcp_port = random.randint(1025, 65535)  # Random TCP port for client connections
        self.game_start_timer = None  # Timer object for game start delay
        self.player_count = 0  # Count of connected players
        self.mode_game_in_progress = False  # Flag to indicate if the game is currently being played
        self.lock = threading.Lock()  # Thread lock for client handling
        self.disqualified_players = set()  # Set of disqualified player names
        self.trivia = TriviaQuestions.TriviaQuestions()  # Trivia questions object
        self.udp_socket = self.create_udp_socket()  # UDP socket for broadcasting offers
        self.tcp_socket = self.create_tcp_socket()  # TCP socket for client communication

    def create_udp_socket(self):
        """Create a UDP socket configured to broadcast."""
        try:
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            return udp_socket
        except socket.error as e:
            print(f"{self.FAIL}Failed to create UDP socket: {e}{self.ENDC}")
            exit(1)

    def create_tcp_socket(self):
        """Create a TCP socket and bind it to the selected port."""
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.bind(('', self.tcp_port))
            tcp_socket.listen()
            return tcp_socket
        except socket.error as e:
            print(f"{self.FAIL}Failed to create or bind TCP socket: {e}{self.ENDC}")
            exit(1)

    def broadcast_offers(self):
        """Broadcast offer messages over UDP to potential clients."""
        message = struct.pack('!Ib32sH', self.MAGIC_COOKIE, self.OFFER_MESSAGE_TYPE,
                              self.SERVER_NAME.encode().ljust(32), self.tcp_port)
        while self.mode_waiting_for_client:
            try:
                self.udp_socket.sendto(message, ('<broadcast>', self.UDP_PORT))
                time.sleep(1)
            except Exception as e:
                print(f"{self.WARNING}Error broadcasting UDP offer: {e}{self.ENDC}")
                break

    def handle_client(self, client_socket, addr):
        """Handle each connected client in a separate thread."""
        try:
            player_name = client_socket.recv(1024).decode().strip()
            print(f"{self.OKBLUE}Player {player_name} connected{self.ENDC}")
            with self.lock:
                self.clients.append({'socket': client_socket, 'name': player_name, 'active': True, 'running': True})
            while self.clients[-1]['running']:
                answer = client_socket.recv(1024).decode().strip()
                if player_name in self.disqualified_players or not self.mode_game_in_progress:
                    continue
                correct = self.trivia.check_answer(answer)
                if correct:
                    self.declare_winner(player_name)
                    self.reset_game()
                    break
                else:
                    self.disqualify_player(client_socket, player_name)
                    if len(self.disqualified_players) == len(self.clients):
                        self.declare_no_winner()
                        self.reset_game()
                    break
        except Exception as e:
            print()

    def declare_winner(self, winner_name):
        """Declare a player as the winner and broadcast the message."""
        message = f"{self.OKGREEN}Game over! Congratulations to the winner: {winner_name}\n{self.ENDC}"
        self.broadcast_message(message)
        print(f"{self.OKGREEN}Game over! Congratulations to the winner: {winner_name}{self.ENDC}")
        
    def declare_no_winner(self):
        """Declare no winner if no correct answers are received."""
        message = f"{self.OKGREEN}Game over! no one answered correctly in time\n{self.ENDC}"
        self.broadcast_message(message)
        print(f"{self.OKGREEN}Game over! no one answered correctly in time{self.ENDC}")

    def disqualify_player(self, client_socket, player_name):
        """Disqualify a player and send a notification."""
        self.disqualified_players.add(player_name)
        message = f"{self.FAIL}{player_name} is incorrect and disqualified!{self.ENDC}\n"
        
        client_socket.send(message.encode())
        print(f"{self.FAIL}Player {player_name} has been disqualified.{self.ENDC}")

    def broadcast_message(self, message):
        """Broadcast a message to all connected clients."""
        with self.lock:
            for client in self.clients:
                try:
                    client['socket'].sendall(message.encode())
                except Exception as e:
                    print(f"{self.FAIL}Error sending to client {client['name']}: {e}{self.ENDC}")

    def reset_game(self):
        """Reset the game state and prepare for a new round."""
        print(f"{self.WARNING}Resetting game and preparing a new round...{self.ENDC}")
        print(f"{self.WARNING}Game over, sending out offer requests...{self.ENDC}")
        with self.lock:
            for client in self.clients:
                client['running'] = False
                client['socket'].close()
            self.clients.clear()
            self.disqualified_players.clear()
        self.mode_waiting_for_client = True
        self.mode_game_in_progress = False
        self.run_server()

    def start_game(self):
        """Start the trivia game and broadcast the question."""
        if not self.clients or self.mode_game_in_progress:
            return
        self.mode_game_in_progress = True
        self.mode_waiting_for_client = False
        self.current_question = self.trivia.get_random_question()
        
        welcome_message = f"{self.OKGREEN}Welcome to the Mystic server, where we are answering trivia questions about Israel!\n{self.ENDC}"
        player_list = "\n".join([f"Player {idx + 1}: {client['name']}" for idx, client in enumerate(self.clients)])
        welcome_message += player_list + "\n==\n"
        welcome_message = f"{self.WARNING}{welcome_message}{self.ENDC}"
        
        print(f"{self.OKGREEN}Starting the game!{self.ENDC}")
        client_message = welcome_message + self.current_question['question'] + "\n"
        self.broadcast_message(client_message)
        
        threading.Timer(10, self.check_answers).start()
        
    def check_answers(self):
        """Check for answers after the timer ends and declare results."""
        if not self.mode_game_in_progress:
            return
        self.declare_no_winner()
        self.reset_game()
    
    def start_or_restart_timer(self):
        """Restart the game timer for new connections."""
        if self.game_start_timer is not None:
            self.game_start_timer.cancel()
        self.game_start_timer = threading.Timer(self.GAME_START_DELAY, self.start_game)
        self.game_start_timer.start()

    def run_server(self):
        """Start the server operations, accept connections, and manage games."""
        threading.Thread(target=self.broadcast_offers, daemon=True).start()
        self.accept_tcp_connections()

    def accept_tcp_connections(self):
        """Accept incoming TCP connections and handle each client."""
        print(f"{self.OKBLUE}Server started, listening on IP address {self.tcp_socket.getsockname()[0]} and port {self.tcp_port}{self.ENDC}")
        while True:
            client_socket, addr = self.tcp_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()
            self.start_or_restart_timer()

def main():
    server = TriviaServer()
    server.run_server()

if __name__ == '__main__':
    main()
