import socket
import threading

def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode()
            print(message)
        except Exception as e:
            print(f"Erro na recepção de mensagens: {e}")
            break

def main():
    host = '127.0.0.1'  # Endereço IP do servidor
    server_port = 12345  # Porta do servidor (a mesma do código do servidor)

    username = input("Digite seu nome de usuário: ")  # Nome de usuário do cliente

    # Criação do socket do cliente
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Conecta-se ao servidor na porta especificada
        client_socket.connect((host, server_port))

        # Envia o nome de usuário para o servidor
        client_socket.send(username.encode())

        # Cria uma thread para receber mensagens do servidor
        receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
        receive_thread.start()

        # Loop para enviar mensagens para o servidor
        while True:
            mensage = input()
            if mensage.lower() == "list":
                client_socket.send("list".encode())
            elif mensage.lower() == "mylist":
                client_socket.send("mylist".encode())
            elif mensage.lower().startswith("addtomylist "):
                client_socket.send(mensage.encode())
            elif mensage.lower().startswith("rmvfrommylist "):
                client_socket.send(mensage.encode())
            elif mensage.lower().startswith("ban "):
                client_socket.send(mensage.encode())
            elif mensage.lower() == "bye":
                break
            else:
                client_socket.send(mensage.encode())

        # Fecha o socket e encerra a thread de recepção
        client_socket.close()
        receive_thread.join()

    except Exception as e:
        print(f"Erro na conexão com o servidor: {e}")

if __name__ == "__main__":
    main()
