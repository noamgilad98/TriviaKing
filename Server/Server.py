import socket
import struct
import threading
import random
import time

import TriviaQuestions

class TriviaServer:
    UDP_PORT = 13117
    SERVER_NAME = 'Mystic'
    MAGIC_COOKIE = 0xabcddcba
    OFFER_MESSAGE_TYPE = 0x02
    GAME_START_DELAY = 4

    def __init__(self):
        self.mode_waiting_for_client = True
        self.clients = []
        self.tcp_port = random.randint(1025, 65535)
        self.game_start_timer = None
        self.player_count = 0
        self.mode_game_in_progress = False
        self.lock = threading.Lock()
        self.disqualified_players = set()
        self.trivia = TriviaQuestions.TriviaQuestions()
        self.udp_socket = self.create_udp_socket()
        self.tcp_socket = self.create_tcp_socket()

    def create_udp_socket(self):
        try:
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            return udp_socket
        except socket.error as e:
            print("Failed to create UDP socket:", e)
            exit(1)

    def create_tcp_socket(self):
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.bind(('', self.tcp_port))
            tcp_socket.listen()
            return tcp_socket
        except socket.error as e:
            print("Failed to create or bind TCP socket:", e)
            exit(1)

    def broadcast_offers(self):
        message = struct.pack('!Ib32sH', self.MAGIC_COOKIE, self.OFFER_MESSAGE_TYPE,
                              self.SERVER_NAME.encode().ljust(32), self.tcp_port)
        while  self.mode_waiting_for_client:
            try:
                self.udp_socket.sendto(message, ('<broadcast>', self.UDP_PORT))
                time.sleep(1)
            except Exception as e:
                print("Error broadcasting UDP offer:", e)
                break




    def handle_client(self, client_socket, addr):
        try:
            player_name = client_socket.recv(1024).decode().strip()
            print(f"Player {player_name} connected from {addr}")
            with self.lock:
                self.clients.append({'socket': client_socket, 'name': player_name, 'active': True})
            while True:
                answer = client_socket.recv(1024).decode().strip()
                if player_name in self.disqualified_players:
                    continue
                correct = self.trivia.check_answer(answer) # TODO nee to make is syncronize
                if correct:
                    self.declare_winner(player_name)
                    self.reset_game()
                    break
                else:
                    self.disqualify_player(client_socket, player_name)
                    if len(self.disqualified_players) == len(self.clients):
                        self.reset_game()
        except Exception as e:
            print(f"Error receiving data from {addr}: {e}")
        finally:
            print("finalyyyyy, something wrong")

    def declare_winner(self, winner_name):
        message = f"Game over! Congratulations to the winner: {winner_name}\n"
        self.broadcast_message(message)
        

    def disqualify_player(self, client_socket, player_name):
        message = f"{player_name} is incorrect and disqualified!"
        client_socket.send(message.encode())
        with self.lock:
            self.disqualified_players.add(player_name)
            print(f"Player {player_name} has been disqualified.")
            

    def remove_client(self, player_name, client_socket):
        with self.lock:
            self.clients = [client for client in self.clients if client['socket'] != client_socket]
            self.disqualified_players.discard(player_name)
        client_socket.close()

    def broadcast_message(self, message):

        with self.lock:
            for client in self.clients:
                try:
                    client['socket'].sendall(message.encode())
                except Exception as e:
                    print(f"Error sending to client {client['name']}: {e}")

    def reset_game(self):
        print("Resetting game and preparing a new round...")
        print("Game over, sending out offer requests...")
        self.mode_waiting_for_client = True
        with self.lock:
            for client in self.clients:
                client['socket'].close()
            self.clients.clear()
            self.disqualified_players.clear()
        self.mode_waiting_for_client = True
        self.mode_game_in_progress = False
        self.run_server()

    def start_game(self):
        if not self.clients or self.mode_game_in_progress:
            return
        self.mode_game_in_progress = True
        self.mode_waiting_for_client = False
        self.current_question = self.trivia.get_random_question()
        print("Starting the game!")
        for client in self.clients:
            try:
                client['socket'].sendall(f"{self.current_question['question']}\n".encode())
            except Exception as e:
                print(f"Error sending to client {client['name']}: {e}")

    def start_or_restart_timer(self):
        if self.game_start_timer is not None:
            self.game_start_timer.cancel()
        self.game_start_timer = threading.Timer(self.GAME_START_DELAY, self.start_game)
        self.game_start_timer.start()

    def run_server(self):
        # Start UDP broadcasting in a separate thread
        threading.Thread(target=self.broadcast_offers).start()
        # Start handling TCP connections
        self.accept_tcp_connections()

    def accept_tcp_connections(self):
        print(f"Server started, listening on IP address {self.tcp_socket.getsockname()[0]} and port {self.tcp_port}")
        while True:
            client_socket, addr = self.tcp_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket, addr)).start()
            self.start_or_restart_timer()


def main():
    server = TriviaServer()
    server.run_server()

if __name__ == '__main__':
    main()
