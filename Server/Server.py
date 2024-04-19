import socket
import threading
import random
import time

class TriviaServer:
    UDP_PORT = 13117
    SERVER_NAME = 'MysticTrivia'
    MAGIC_COOKIE = b'\xab\xcd\xdc\xba'
    OFFER_MESSAGE_TYPE = b'\x02'
    GAME_START_DELAY = 10

    def __init__(self):
        self.clients = []
        self.tcp_port = random.randint(1025, 65535)
        self.game_start_timer = None
        self.game_in_progress = False
        self.player_count = 0  # Initialize player count
        self.trivia_questions = [
            {"question": "True or false: The sun rises in the west.", "answer": False},
            {"question": "True or false: Python is a type of snake.", "answer": True},
            {"question": "True or false: Gold is heavier than silver.", "answer": True},
            # Add more questions
        ]
        self.current_question = None
        self.broadcast_thread = None

    def broadcast_udp(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as udp_socket:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            while True:
                message = self.MAGIC_COOKIE + self.OFFER_MESSAGE_TYPE + self.SERVER_NAME.encode().ljust(
                    32) + self.tcp_port.to_bytes(2, 'big')
                udp_socket.sendto(message, ('<broadcast>', self.UDP_PORT))
                time.sleep(1)

    def handle_client(self, conn, addr):
        try:
            player_name = conn.recv(1024).decode().strip()
            self.player_count += 1
            self.clients.append((player_name, conn))
            print(f"\033[92mPlayer {self.player_count}: {player_name}\033[0m")

            if self.game_start_timer:
                self.game_start_timer.cancel()
            self.game_start_timer = threading.Timer(self.GAME_START_DELAY, self.start_game)
            self.game_start_timer.start()

            while True:
                answer = conn.recv(1024).decode().strip()
                if answer:
                    correct = self.check_answer(answer)
                    if correct:
                        message = f"Game over!\nCongratulations to the winner: {player_name}\n"
                        self.broadcast_message(message)
                        self.reset_game()
                        break
                    else:
                        conn.sendall("Wrong answer, try again next round!\n".encode())
        except Exception as e:
            print(f'\033[91mError handling client {addr}: {e}\033[0m')
        finally:
            if (player_name, conn) in self.clients:
                self.clients.remove((player_name, conn))

    def check_answer(self, answer):
        if answer.upper() not in ['T', 'Y', '1', 'F', 'N', '0']:
            return False
        is_true_answer = answer.upper() in ['T', 'Y', '1']
        correct_answer = self.current_question["answer"]
        return is_true_answer == correct_answer

    def broadcast_message(self, message):
        for _, conn in self.clients:
            try:
                conn.sendall(message.encode())
            except Exception as e:
                print(f"\033[91mError sending to client: {e}\033[0m")

    def reset_game(self):
        print("\033[93mGame over, sending out offer requests...\033[0m")
        for _, conn in self.clients:
            conn.close()
        self.clients = []
        self.game_in_progress = False
        self.ensure_single_broadcast_thread()

    def start_game(self):
        if not self.clients or self.game_in_progress:
            return
        self.game_in_progress = True
        self.current_question = random.choice(self.trivia_questions)
        question = self.current_question["question"]
        print("\033[96mStarting the game!\033[0m")
        for player_name, conn in self.clients:
            try:
                conn.sendall(f"{question}\n".encode())
            except Exception as e:
                print(f"\033[91mError sending to client {player_name}: {e}\033[0m")

    def tcp_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
            tcp_socket.bind(('', self.tcp_port))
            tcp_socket.listen()
            print(f"\033[94mServer started, listening on IP address {tcp_socket.getsockname()[0]} and port {self.tcp_port}\033[0m")

            while True:
                conn, addr = tcp_socket.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr)).start()

    def ensure_single_broadcast_thread(self):
        if self.broadcast_thread is not None and self.broadcast_thread.is_alive():
            return
        self.broadcast_thread = threading.Thread(target=self.broadcast_udp)
        self.broadcast_thread.start()

def main():
    server = TriviaServer()
    server.ensure_single_broadcast_thread()
    server.tcp_server()

if __name__ == '__main__':
    main()
