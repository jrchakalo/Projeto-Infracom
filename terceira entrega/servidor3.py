import re
import socket
import random

# Função para enviar mensagem com rdt3.0
def send_message_rdt(message_str, client_socket,client_address):
    seq_num = 0
    while True:
        # Adiciona o número de sequência à mensagem
        message = f"ACK:{message_str}"
        # Envia a mensagem para o servidor
        if random.random() > 0.2:
            client_socket.sendto(message.encode(), client_address)
            # Espera pelo ACK
            try:
                client_socket.settimeout(2)
                ack, _ = client_socket.recvfrom(2048)
                if ack.decode() == f"ACK":
                    break
            except socket.timeout:
                pass
        # Verifica se o número máximo de tentativas foi atingido
        seq_num += 1
        if seq_num > 3:
            print("Nao foi possivel enviar a mensagem.")
            break

# Função para receber mensagem com rdt3.0
def receive_message_rdt(client_socket):
    while True:
        # Recebe a mensagem do servidor
        try:
            client_socket.settimeout(2)
            message, client_address = client_socket.recvfrom(2048)
            message_str = message.decode()
            # Verifica se a mensagem é um ACK
            if message_str.startswith("ACK"):
                # Envia o ACK de volta para o servidor
                ack = f"ACK"
                client_socket.sendto(ack.encode(), client_address)
                break
        except socket.timeout:
            pass

    part = message_str.split(":")
    if len(part) >= 2 and part[1] != "":
        return part[1][2:-1], client_address
    else:
        return None,None

# Define as informações do servidor
server_address = ('localhost', 5000)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(server_address)

# Define as variáveis do servidor
clients = {}
ban_list = {}

# Função para enviar mensagem para todos os clientes
def send_to_all(message, sender_address):
    for client_address in clients:
        if client_address != sender_address:
            client_socket, client_username, friend_list = clients[client_address]
            if clients[sender_address][1] in friend_list:
                message = re.sub(r'(/~)', r'/[amigo] ~', message)  # Adicione [amigo] à mensagem
            send_message_rdt(message.encode(),client_socket, client_address)

def conectaCliente(message, client_address, client_socket):
    # Verifica se o nome do usuário já está sendo usado
    username = message.split(" ")[0]
    if username in [client[1] for client in clients.values()]:
        print(f"Nome de usuario '{username}' ja esta em uso.")
        # Envie uma mensagem de erro de nome de usuário para o cliente
        error_message = "Nome de usuario ja esta em uso. Escolha outro nome."
        send_message_rdt(error_message.encode(), client_socket, client_address)
    else:
        # Adiciona o cliente à lista de clientes
        clients[client_address] = (client_socket, username, [])
        print(f"Cliente {client_address} conectado como {username}.")
        # Envia mensagem de alerta da nova presença
        alert_message = f"{username} entrou na sala."
        send_to_all(alert_message, client_address)
       

# Função para lidar com as mensagens recebidas
def handle_message(message, client_address):
    global clients, ban_list
    if message == "bye":
        # Remove o cliente da lista de clientes
        del clients[client_address]
        print(f"Cliente {client_address} desconectado.")
        # Envia mensagem de alerta da saída do cliente
        alert_message = f"{client_address} saiu da sala."
        send_to_all(alert_message, client_address)

    elif message.startswith("list"):
        user_list = ", ".join([clients[addr][1] for addr in clients])
        client_socket = clients[client_address][0]
        send_message_rdt(user_list.encode(), client_socket,client_address)

    elif message.startswith("mylist"):
        friend_list = clients[client_address][2]
        if friend_list:
            friend_list_str = ", ".join(friend_list)
            client_socket = clients[client_address][0]
            send_message_rdt( ("Lista de amizade - " + friend_list_str).encode(), client_socket, client_address)
        else:
            client_socket = clients[client_address][0]
            send_message_rdt("Voce nao possui amigos na lista.".encode(), client_socket, client_address)


    elif message.startswith("addtomylist"):
        parts = message.split()
        if len(parts) > 1:
            friend_username = parts[1]
            if friend_username in [clients[addr][1] for addr in clients]:
                client_socket = clients[client_address][0]
                if friend_username not in clients[client_address][2]:  
                    clients[client_address][2].append(friend_username)
                    send_message_rdt(f"[amigo adicionado] {friend_username}".encode(), client_socket, client_address)
                else:
                    send_message_rdt(f"{friend_username} ja esta na sua lista de amizade.".encode(), client_socket, client_address)
            else:
                client_socket = clients[client_address][0]
                send_message_rdt(f"{friend_username} nao esta na sala.".encode(), client_socket, client_address)

    elif message.startswith("rmvfrommylist"):
        parts = message.split()
        if len(parts) > 1:
            friend_username = parts[1]
            friend_list = clients[client_address][2]
            if friend_username in friend_list:
                friend_list.remove(friend_username)  # Remove o amigo da lista
                client_socket = clients[client_address][0]
                send_message_rdt(f"[amigo removido] {friend_username}".encode(), client_socket, client_address)
            else:
                client_socket = clients[client_address][0]
                send_message_rdt(f"{friend_username} nao esta na sua lista de amizade.".encode(), client_socket, client_address)


    elif message.startswith("ban"):
        parts = message.split()
        if len(parts) > 1:
            user_to_ban = parts[1]
            if user_to_ban in [clients[addr][1] for addr in clients]:
                if user_to_ban not in ban_list:
                    ban_list[user_to_ban] = {'votes': 1, 'threshold': len(clients) // 2 + 1}
                else:
                    ban_list[user_to_ban]['votes'] += 1

                total_votes = ban_list[user_to_ban]['votes']
                threshold = ban_list[user_to_ban]['threshold']

                send_to_all(f"[ {user_to_ban} ] ban {total_votes}/{threshold}", client_address)

                if total_votes >= threshold:
                    clients_to_remove = []
                    for addr in clients:
                        if clients[addr][1] == user_to_ban:
                            clients_to_remove.append(addr)

                    for addr in clients_to_remove:
                        del clients[addr]

                    del ban_list[user_to_ban]
                    send_to_all(f"[ {user_to_ban} ] foi banido da sala.", client_address)

    else:
        # Envia a mensagem para todos os clientes
        send_to_all(message, client_address)

# Loop principal do servidor
while True:
    # Recebe uma mensagem de um cliente
    message, client_address = receive_message_rdt(server_socket)

    if message is None and client_address is None:
        continue
    
    elif(message.__contains__("entrou na sala.")):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.connect(client_address)
        conectaCliente(message,client_address,client_socket)
    else:
        # Verifica se o cliente está na lista de clientes
        if client_address in clients:
            handle_message(message, client_address)
