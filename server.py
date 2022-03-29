import pickle
import threading
import socket


host = "127.0.0.1"  # localhost
port = 55555

clients = []


def handle(client):
    while True:
        try:
            message = pickle.loads(client.recv(16384))

            # Receive score from client and update highest score
            if "Score" in message:
                update_score(int(message.split(',')[1].strip()))

            # Pass grid to another player
            else:
                clients[clients.index(client) - 1].send(pickle.dumps(message))
        except:
            clients.remove(client)
            client.close()
            break


def receive():
    while len(clients) < 2:

        client, address = server.accept()
        print("Player {0} with address {1} connected".format(len(clients) + 1, address))

        clients.append(client)
        client.send("Connected to the server".encode())

        thread = threading.Thread(target=handle, args=(client,))
        thread.start()

        if len(clients) == 2:
            for client in clients:
                client.send("Game start, {0}".format(max_score()).encode())


def max_score():
    with open("scores.txt", "r") as f:
        lines = f.readlines()
        score = lines[0].strip()

    return score


def update_score(new_score):
    score = max_score()

    if new_score > int(score):
        with open("scores.txt", "w") as f:
            f.write(str(new_score))


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()
print("Server is listening...")
receive()
