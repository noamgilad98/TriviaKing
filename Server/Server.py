import socket
import threading
import time
import random
from Questions import questions

UDP_PORT = 13117
TCP_PORT = random.randint(1025, 65535)
SERVER_NAME = 'Mystic'
MAGIC_COOKIE = b'\xab\xcd\xdc\xba'
OFFER_MESSAGE_TYPE = b'\x02'
clients = []
answers = {}
game_start_timer = None
current_question = None
disqualified_players = set()

def broadcast_udp():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while True:
            message = MAGIC_COOKIE + OFFER_MESSAGE_TYPE + SERVER_NAME.encode().ljust(32) + TCP_PORT.to_bytes(2, 'big')
            udp_socket.sendto(message, ('<broadcast>', UDP_PORT))
            time.sleep(1)

def reset_game():
    global clients, answers, game_start_timer, current_question, disqualified_players
    clients.clear()
    answers.clear()
    disqualified_players.clear()
    current_question = None
    game_start_timer = None
    print("Game over, sending out offer requests...")

def handle_client(conn, addr, player_name):
    global answers, disqualified_players

    try:
        answer = conn.recv(1024).decode().strip().upper()
        print(f"{player_name} answered {answer}")
        if answer in ['Y', 'T', '1']:
            answers[player_name] = True
        elif answer in ['N', 'F', '0']:
            answers[player_name] = False
        else:
            disqualified_players.add(player_name)
            conn.sendall("Invalid answer, you are disqualified!".encode())
            conn.close()
            return

        check_answers(player_name)
    except Exception as e:
        print(f'Error handling client {addr}: {e}')
        conn.close()

def check_answers(player_name):
    global clients, answers, current_question, disqualified_players

    correct_answer = current_question['is_true'] if current_question else None

    if player_name in disqualified_players:
        return

    if answers.get(player_name) == correct_answer:
        end_game(winner=player_name)
        return

    if len(disqualified_players) == len(clients):
        end_game()

def end_game(winner=None):
    global clients, game_start_timer

    message = f"Game over!\nCongratulations to the winner: {winner}" if winner else "Game over!\nNo correct answers."
    print(message)

    for _, player_conn in clients:
        try:
            player_conn.sendall(message.encode())
        finally:
            player_conn.close()

    reset_game()

def start_game():
    global game_start_timer, clients, answers, current_question, disqualified_players

    current_question = random.choice(questions)
    question_text = current_question['question']

    welcome_message = "Welcome to the Mystic server. Let's answer a trivia question.\n"
    player_list = '\n'.join(f"Player {index + 1}: {name}" for index, (name, _) in enumerate(clients))
    full_message = f"{welcome_message}{player_list}\n==\n{question_text}\nTrue or False?"

    print(full_message)
    for _, conn in clients:
        try:
            conn.sendall(full_message.encode())
        except Exception as e:
            print(f"Error sending to client: {e}")

def tcp_server():
    global clients, game_start_timer
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
        tcp_socket.bind(('', TCP_PORT))
        tcp_socket.listen()
        print(f"Server started, listening on IP address {tcp_socket.getsockname()[0]} and port {TCP_PORT}")

        while True:
            conn, addr = tcp_socket.accept()
            player_name = conn.recv(1024).decode().strip()
            clients.append((player_name, conn))
            print(f"{player_name} connected from {addr}")

            if not game_start_timer:
                game_start_timer = threading.Timer(10.0, start_game)
                game_start_timer.start()
            else:
                game_start_timer.cancel()
                game_start_timer = threading.Timer(10.0, start_game)
                game_start_timer.start()

def main():
    threading.Thread(target=broadcast_udp).start()
    tcp_server()

if __name__ == '__main__':
    main()
