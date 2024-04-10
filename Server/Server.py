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
        self.player_count = 0  # Initialize player count
        self.trivia_questions = [
            {"question": "True or false: Mount Hermon is the highest point in Israel.", "answer": True},
            {"question": "True or false: The Jordan River is the longest river in Israel.", "answer": True},
            {"question": "True or false: The Negev Desert covers more than half of Israel's land area.", "answer": True},
            {"question": "True or false: Israel has no access to the Red Sea.", "answer": False},
            {"question": "True or false: The Dead Sea is the lowest point on Earth's surface.", "answer": True},
            {"question": "True or false: Mount Carmel is located in the southern part of Israel.", "answer": False},
            {"question": "True or false: The Sea of Galilee is a freshwater lake.", "answer": True},
            {"question": "True or false: The Yarkon River is in Jerusalem.", "answer": False},
            {"question": "True or false: Israel shares a border with Lebanon.", "answer": True},
            {"question": "True or false: The Golan Heights is a mountain range in eastern Israel.", "answer": False}
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
            self.player_count += 1  # Increment player count for each connection
            self.clients.append((player_name, conn))

            print(f"Player {self.player_count}: {player_name}")  # Display player number and name

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
            if (player_name, conn) in self.clients:
                self.clients.remove((player_name, conn))

    def check_answer(self, answer):
        # Check if the answer is one of the allowed keys
        if answer.upper() not in ['T', 'Y', '1', 'F', 'N', '0']:
            return False  # Automatically wrong if the key is not allowed

        # Assuming 'T', 'Y', '1' are considered true, and 'F', 'N', '0' are false
        is_true_answer = answer.upper() in ['T', 'Y', '1']
        correct_answer = self.current_question["answer"]
        return is_true_answer == correct_answer

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
