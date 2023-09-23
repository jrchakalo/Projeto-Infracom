import socket
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
expected_seq_num = 0

def recebeArquivo(novoNomeArquivo, nomeArquivo, tamanhoBuffer, udpSocket, enderecoCliente, diretorio_destino):
    global expected_seq_num
    try:
        with open(novoNomeArquivo, 'wb') as file:
            print(f"Recebendo arquivo de nome {nomeArquivo} de {enderecoCliente}...")

            while True:
                packet, _ = udpSocket.recvfrom(tamanhoBuffer + 1)
                if packet == b"FINAL":
                    break

                seq_num = int(packet[0:1].decode())
                data = packet[1:]

                if seq_num == expected_seq_num:
                    print(f"Recebido pacote {seq_num}, enviando ACK")
                    file.write(data)
                    udpSocket.sendto(str(seq_num).encode(), enderecoCliente)
                    expected_seq_num ^= 1
                else:
                    print(f"Pacote fora de ordem {seq_num}, descartando e enviando ACK para {expected_seq_num ^ 1}")
                    udpSocket.sendto(str(expected_seq_num ^ 1).encode(), enderecoCliente)

        print(f"{novoNomeArquivo} salvo em {diretorio_destino} com sucesso")
    except FileNotFoundError as e:
        print(f"Erro ao receber: Arquivo {novoNomeArquivo} não encontrado.")
    except socket.error as e:
        print(f"Erro de socket ao receber: {str(e)}")
    except Exception as e:
        print(f"Erro ao receber arquivo: {str(e)}")

def main():
    host = 'localhost'
    port = 12345
    tamanhoBuffer = 1024
    diretorio_destino = f"{current_dir}/destino"

    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udpSocket.bind((host, port))

    print("Server UDP está pronto para receber arquivos.")

    while True:
        data, enderecoCliente = udpSocket.recvfrom(tamanhoBuffer)
        nomeArquivo = data.decode()
        novoNomeArquivo = os.path.join(diretorio_destino, "recebido_" + nomeArquivo)
        recebeArquivo(novoNomeArquivo, nomeArquivo, tamanhoBuffer, udpSocket, enderecoCliente, diretorio_destino)

if __name__ == "__main__":
    main()
