import socket
import threading
import datetime
import random

# Função para enviar mensagem com rdt3.0
def send_message_rdt(message_str, client_socket, server_address):
    seq_num = 0
    while True:
        # Adiciona o número de sequência à mensagem
        message = f"ACK:{message_str}"
        # Envia a mensagem para o servidor
        if random.random() > 0.2:
            client_socket.sendto(message.encode(), server_address)
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
            message, server_address = client_socket.recvfrom(2048)
            message_str = message.decode()
            # Verifica se a mensagem é um ACK
            if message_str.startswith("ACK"):
                # Envia o ACK de volta para o servidor
                ack = f"ACK"
                client_socket.sendto(ack.encode(), server_address)
                break
        except socket.timeout:
            pass
    
    part = message_str.split(":")
    if len(part) >= 2 and part[1] != "":
        return part[1][2:-1]
    else:
        return None


# Define as informações do servidor
server_address = ('localhost', 5000)

# Define as informações do cliente
client_address = ('localhost', 0)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client_socket.bind(client_address)

# Define as variáveis do cliente
username = ''
connected = False

# Função para receber mensagens do servidor
def receive_messages():
    while True:
        message_str = receive_message_rdt(client_socket)
        if message_str is not None:
            print(message_str)

# Função para enviar mensagens para o servidor
def send_message(message_str):
    global connected
    global username 
    if not connected:
        if message_str.startswith("hi, meu nome eh "):
            # Conecta o usuário ao servidor
            username = message_str.split(" ")[4]
            connected = True
            print("Conectado ao servidor.")
            # Envia mensagem de alerta da nova presença
            alert_message = f"{username} entrou na sala."
            send_message_rdt(alert_message.encode(), client_socket, server_address)
        else:
            print("Voce precisa se conectar a sala primeiro.")
    else:
        # Envia mensagem para o servidor
        message = f"{client_address[0]}:{client_address[1]}/~{username}: {message_str} {datetime.datetime.now().strftime('%H:%M:%S %d/%m/%Y')}"
        send_message_rdt(message.encode(),client_socket, server_address)

# Função para exibir a lista de usuários
def list_users():
    send_message_rdt("list".encode(),client_socket, server_address)

# Função para exibir a lista de amigos
def my_list():
    send_message_rdt("mylist".encode(),client_socket, server_address)

# Função para adicionar usuário à lista de amigos
def add_to_my_list(user):
    send_message_rdt(f"addtomylist {user}".encode(),client_socket, server_address)

# Função para remover usuário da lista de amigos
def remove_from_my_list(user):
    send_message_rdt(f"rmvfrommylist {user}".encode(),client_socket, server_address)


# Função para banir usuário da sala
def ban_user(user):
    send_message_rdt(f"ban {user}".encode(),client_socket, server_address)

# Inicia a thread para receber mensagens do servidor
receive_thread = threading.Thread(target=receive_messages)
receive_thread.start()

# Loop principal do cliente
while True:
    # Lê uma mensagem do usuário
    message_str = input()

    # Verifica se o usuário está conectado
    if not connected:
        # Se não estiver, verifica se a mensagem é um comando de conexão
        send_message(message_str)
    else:
        # Verifica se a mensagem é um comando
        if message_str.startswith("list"):
            list_users()
        elif message_str.startswith("mylist"):
            my_list()
        elif message_str.startswith("addtomylist"):
            if(message_str.split(" ")[1] == ""):
                print("Voce precisa informar o nome de um usuario para adiciona-lo na sua lista de amigos.")
            elif(message_str.split(" ")[1] == username):
                print("Voca não pode adicionar voce mesmo na sua lista de amigos.")
            else:
                add_to_my_list(message_str.split(" ")[1])
        elif message_str.startswith("rmvfrommylist"):
            if(message_str.split(" ")[1] == ""):
                print("Voce precisa informar o nome de um usuario para remove-lo da sua lista de amigos.")
            elif(message_str.split(" ")[1] == username):
                print("Voce não pode remover você mesmo da sua lista de amigos.")
            else:
                remove_from_my_list(message_str.split(" ")[1])
        elif message_str.startswith("ban"):
            ban_user(message_str.split(" ")[1])
        elif message_str.startswith("bye"):
            # Sai da sala
            connected = False
            send_message_rdt("bye".encode(),client_socket, server_address)
            print("Desconectado do servidor.")
        else:
            # Envia mensagem para o servidor
            send_message(message_str)
