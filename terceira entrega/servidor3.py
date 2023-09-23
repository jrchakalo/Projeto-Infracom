import socket
import threading
import datetime

# Dicionário para armazenar informações dos clientes conectados
clients = {}
friends_lists = {}
ban_votes = {}
banned_clients = []

# Função para verificar se a maioria votou para banir um usuário
def check_ban_vote(username):
    connected_clients = len(clients)
    required_votes = (connected_clients // 2) 
    if ban_votes.get(username, 0) >= required_votes:
        return True
    return False

# Função para lidar com as mensagens recebidas de um cliente
def handle_client(client_socket, client_address):
    try:
        while True:
            # Pega o nome do usuario que foi informado pelo cliente
            username = client_socket.recv(1024).decode().strip()

            # Verifica se o nome de usuário já está em uso
            if username in clients:
                client_socket.send("Nome de usuário já está em uso. Escolha outro nome. ".encode())
                client_socket.send("Digite seu nome de usuário: ".encode())
            else:
                break
                
        # Adiciona o cliente à lista de clientes
        clients[username] = {
            "socket": client_socket,
            "address": client_address,
        }

        # Inicializa a lista de amigos do cliente
        friends_lists[username] = []

        print(f"Cliente {username} conectado desde {client_address[0]}:{client_address[1]}")

        # Notifica os outros clientes sobre a nova conexão
        alert_message = f"{username} entrou na sala."
        for client, info in clients.items():
                if client != username:
                    info["socket"].send(alert_message.encode())
  

        # Loop para receber e transmitir mensagens
        while True:
            message = client_socket.recv(1024).decode()
            if not message:
                break

            # Verifica se o cliente enviou uma solicitação de amizade
            if message.lower().startswith("addtomylist "):
                friend_username = message[12:].strip()
                if friend_username in clients and friend_username != username:
                    friends_lists[username].append(friend_username)
                    client_socket.send(f"Você adicionou {friend_username} à sua lista de amigos.".encode())
                    continue
                else:
                    client_socket.send(f"O usuário {friend_username} não foi encontrado ou é você mesmo.".encode())
                    continue
            # Verifica se o cliente quer remover uma amizade
            elif message.lower().startswith("rmvfrommylist "):
                friend_to_remove = message[14:].strip()
                if friend_to_remove in friends_lists[username]:
                    friends_lists[username].remove(friend_to_remove)
                    client_socket.send(f"Você removeu {friend_to_remove} da sua lista de amigos.".encode())
                    continue
                else:
                    client_socket.send(f"{friend_to_remove} não está na sua lista de amigos.".encode())
                    continue
            
            # Verifica se o cliente enviou o comando "list" e informa os usuarios online
            if message.lower() == "list":
                online_users = ", ".join(clients.keys())
                client_socket.send(f"Usuários online: {online_users}".encode())
                continue
            # Verifica se o cliente enviou o comando "mylist"
            elif message.lower() == "mylist":
                friends = ", ".join(friends_lists[username])
                client_socket.send(f"Sua lista de amigos: {friends}".encode())
                continue
            # Verifica se o cliente enviou o comando "ban"
            elif message.lower().startswith("ban "):
                # Define a quantidade de votos necessarios para banir
                connected_clients = len(clients)
                required_votes = (connected_clients // 2) + 1
                user_to_ban = message[4:].strip()
                if user_to_ban in clients:
                    if user_to_ban != username:  # Verifica se o cliente está tentando se banir
                        if check_ban_vote(user_to_ban):
                            banned_clients.append(user_to_ban)
                            # Banindo o cliente
                            clients[user_to_ban]["socket"].send("Você foi banido do chat.".encode())
                            clients[user_to_ban]["socket"].close()
                            # Notifica todos os clientes sobre o resultado da votação
                            for client in clients.values():
                                if client != clients[user_to_ban]:
                                    vote_message = f"O usuário [{user_to_ban}] foi banido"
                                    client["socket"].send(vote_message.encode())
                            # Limpa os votos para este usuário
                            del ban_votes[user_to_ban]
                            continue
                        else:
                            # Registra o voto do cliente
                            if user_to_ban not in ban_votes:
                                ban_votes[user_to_ban] = 1
                            else:
                                ban_votes[user_to_ban] += 1
                            client_socket.send(f"Você votou para banir o usuário {user_to_ban}.".encode())
                            continue
                    else:
                        client_socket.send("Você não pode se banir.".encode())
                        continue
                else:
                    client_socket.send(f"O usuário {user_to_ban} não foi encontrado.".encode())
                    continue

            # Obtém a hora e data atual do servidor
            current_time = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")

            # Verifica todos os clientes exceto a si mesmo
            for client, info in clients.items():
                if client != username:
                    # Verifica se o remetente é amigo do receptor
                    friend_tag = "[amigo] " if username in friends_lists[client] else ""

                    # Mensagem que vai pro usuario
                    personal_message = f"{client_address[0]}:{client_address[1]}/~{friend_tag}{username}: {message} {current_time}"
    
            # Mensagem que fica no chat geral
            formatted_message = f"{client_address[0]}:{client_address[1]}/~{username}: {message} {current_time}"

            # Exibe a mensagem no servidor
            print(formatted_message)

            # Transmite a mensagem para todos os outros clientes
            for client, info in clients.items():
                if client != username:
                    info["socket"].send(personal_message.encode())

    except Exception as e:
        print(f"Erro na conexão com {client_address}: {e}")
    finally:
        # Remove o cliente da lista de clientes e fecha o socket
        del clients[username]
        client_socket.close()
        print(f"Cliente {username} desconectado")
        alert_message = f"{username} se desconectou."
        for client, info in clients.items():
                if client != username:
                    info["socket"].send(alert_message.encode())

# Configurações do servidor
host = '0.0.0.0'  # Escuta em todas as interfaces de rede
port = 12345  # Porta para conexões

# Criação do socket do servidor
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(5)  # Permitir até 5 conexões pendentes

print(f"Servidor ouvindo em {host}:{port}")

# Loop principal para aceitar conexões de clientes
while True:
    client_socket, client_address = server_socket.accept()
    client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
    client_handler.start()
