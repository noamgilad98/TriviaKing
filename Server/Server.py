import socket
import threading
import time
import random

UDP_PORT = 13117
TCP_PORT = random.randint(1025, 65535)
SERVER_NAME = 'Mystic'
MAGIC_COOKIE = b'\xab\xcd\xdc\xba'
OFFER_MESSAGE_TYPE = b'\x02'
clients = []
game_start_timer = None  # Timer for starting the game

def broadcast_udp():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while True:
            message = MAGIC_COOKIE + OFFER_MESSAGE_TYPE + SERVER_NAME.encode().ljust(32) + TCP_PORT.to_bytes(2, 'big')
            udp_socket.sendto(message, ('<broadcast>', UDP_PORT))
            time.sleep(1)

def handle_client(conn, addr):
    global game_start_timer

    try:
        player_name = conn.recv(1024).decode().strip()
        clients.append((player_name, conn))
        print(f"{player_name} connected from {addr}")

        # Reset the game start timer every time a new player connects
        if game_start_timer is not None:
            game_start_timer.cancel()
        game_start_timer = threading.Timer(10.0, start_game)
        game_start_timer.start()

    except Exception as e:
        print(f'Error handling client {addr}: {e}')

def start_game():
    global game_start_timer
    game_start_timer = None  # Clear the timer once the game starts

    welcome_message = "Welcome to the Mystic server, where we are answering trivia questions about Aston Villa FC.\n"
    player_list = '\n'.join(f"Player {index + 1}: {name}" for index, (name, _) in enumerate(clients))
    question = "True or false: Aston Villa's current manager is Pep Guardiola"

    full_message = f"{welcome_message}{player_list}\n==\n{question}\n"

    for _, conn in clients:
        try:
            conn.sendall(full_message.encode())
        except Exception as e:
            print(f"Error sending to client: {e}")

def tcp_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
        tcp_socket.bind(('', TCP_PORT))
        tcp_socket.listen()
        print(f"Server started, listening on IP address {tcp_socket.getsockname()[0]} and port {TCP_PORT}")

        while True:
            conn, addr = tcp_socket.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()

def main():
    threading.Thread(target=broadcast_udp).start()
    tcp_server()

if __name__ == '__main__':
    main()
