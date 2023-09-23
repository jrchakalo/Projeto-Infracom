import socket
import os
import time

seq_num = 0  # número de sequência para pacotes
timeout = 4.0  # tempo limite para retransmissão

def enviaArquivo(nomeArquivo, tamanhoBuffer, udpSocket, enderecoServidor):
    global seq_num
    try:
        udpSocket.sendto(os.path.basename(nomeArquivo).encode(), enderecoServidor)

        with open(nomeArquivo, 'rb') as file:
            print(f"Enviando {nomeArquivo} para o servidor...")

            while True:
                data = file.read(tamanhoBuffer)
                if not data:
                    break

                packet = str(seq_num).encode() + data
                udpSocket.sendto(packet, enderecoServidor)
                print(f"Enviado pacote com número de sequência {seq_num}")

                start = time.time()
                while True:
                    try:
                        udpSocket.settimeout(timeout - (time.time() - start))
                        ack, _ = udpSocket.recvfrom(2)
                        ack = int(ack.decode())
                        if ack == seq_num:
                            print(f"Recebido ACK para {seq_num}")
                            seq_num ^= 1
                            break
                    except socket.timeout:
                        print("Timeout. Reenviando...")
                        udpSocket.sendto(packet, enderecoServidor)

        udpSocket.sendto(b"FINAL", enderecoServidor)
        print(f"{nomeArquivo} enviado com sucesso!")
    except FileNotFoundError as e:
        print(f"Erro: Arquivo {nomeArquivo} não encontrado.")
    except socket.error as e:
        print(f"Erro de socket: {str(e)}")
    except Exception as e:
        print(f"Erro ao enviar/receber arquivo: {str(e)}")

def main():
    host = 'localhost'
    port = 12345
    tamanhoBuffer = 1024

    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        nomeArquivo = input("Digite o path completo do arquivo que deseja enviar: ")
        enderecoServidor = (host, port)
        enviaArquivo(nomeArquivo, tamanhoBuffer, udpSocket, enderecoServidor)


if __name__ == "__main__":
    main()
