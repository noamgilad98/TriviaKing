import socket
import threading
import random
import time


class TriviaServer:
    UDP_PORT = 13117
    SERVER_NAME = 'Mystic'
    MAGIC_COOKIE = b'\xab\xcd\xdc\xba'
    OFFER_MESSAGE_TYPE = b'\x02'
    GAME_START_DELAY = 10  # 10 seconds delay before the game starts

    def __init__(self):
        self.clients = []
        self.tcp_port = random.randint(1025, 65535)
        self.game_start_timer = None
        self.trivia_questions = [
            {"question": "True or false: Python is a type of snake.", "answer": False},
            {"question": "True or false: The capital of France is Paris.", "answer": True},
            # Add more trivia questions here
        ]
        self.current_question = None

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
            self.clients.append((player_name, conn))
            print(f"{player_name} connected from {addr}")

            if self.game_start_timer:
                self.game_start_timer.cancel()

            self.game_start_timer = threading.Timer(self.GAME_START_DELAY, self.start_game)
            self.game_start_timer.start()

            while True:  # Listen for answers from this client
                answer = conn.recv(1024).decode().strip()
                if answer:
                    correct = self.check_answer(answer)
                    if correct:
                        message = f"{player_name} is correct! {player_name} wins!\n"
                        self.broadcast_message(message)
                        self.reset_game()
                        break
                    else:
                        conn.sendall("Wrong answer! You are disqualified.\n".encode())
                        self.clients.remove((player_name, conn))
                        conn.close()
                        break

        except Exception as e:
            print(f'Error handling client {addr}: {e}')
            self.clients.remove((player_name, conn))

    def check_answer(self, answer):
        correct_answer = self.current_question["answer"]
        return (answer.lower() in ['t', '1']) == correct_answer

    def broadcast_message(self, message):
        for _, conn in self.clients:
            try:
                conn.sendall(message.encode())
            except Exception as e:
                print(f"Error sending to client: {e}")

    def reset_game(self):
        self.clients = []
        # Code to reset the game and start broadcasting offers again
        threading.Thread(target=self.broadcast_udp).start()

    def start_game(self):
        if not self.clients:
            return

        self.current_question = random.choice(self.trivia_questions)
        question = self.current_question["question"]
        print("Starting the game!")
        for player_name, conn in self.clients:
            try:
                conn.sendall(f"{question}\n".encode())
            except Exception as e:
                print(f"Error sending to client {player_name}: {e}")



    def tcp_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
            tcp_socket.bind(('', self.tcp_port))
            tcp_socket.listen()
            print(f"Server started, listening on IP address {tcp_socket.getsockname()[0]} and port {self.tcp_port}")

            while True:
                conn, addr = tcp_socket.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr)).start()
                # Here you can also start a new thread to listen for client answers


def main():
    server = TriviaServer()
    threading.Thread(target=server.broadcast_udp).start()
    server.tcp_server()


if __name__ == '__main__':
    main()
