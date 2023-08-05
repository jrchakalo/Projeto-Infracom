import socket
import os

#funcao em que o servidor recebe o arquivo
def recebeArquivo(nomeArquivo, tamanhoBuffer, udpSocket, enderecoCliente):
    try:
        #o programa cria uma pasta no diretorio para os arquivos recebidos pelo servidor 
        #se ela ja existir coloca os arquivos na existente
        pasta_recebidos_servidor = "arquivos_recebidos_servidor"
        if not os.path.exists(pasta_recebidos_servidor):
            os.makedirs(pasta_recebidos_servidor)

        arquivo_destino = os.path.join(pasta_recebidos_servidor, nomeArquivo)

        with open(arquivo_destino, 'wb') as file:
            print(f"Recebendo arquivo {nomeArquivo} do cliente {enderecoCliente}...")
            while True:
                data, _ = udpSocket.recvfrom(tamanhoBuffer)
                #espera receber o final que sinaliza que a mensagem do cliente terminou
                #nesse caso a mensagem eh um arquivo
                if data == b"FINAL":
                    break
                file.write(data)

        #quando a mensagem cliente termina de enviar, reenvia pra ele
        reenviaArquivo(arquivo_destino, tamanhoBuffer, udpSocket, enderecoCliente)

    #tratamento para se der algum erro no recebimento do arquivo
    except FileNotFoundError as e:
        print(f"Erro ao receber: Arquivo {nomeArquivo} não encontrado.")
    except socket.error as e:
        print(f"Erro de socket ao receber: {str(e)}")
    except Exception as e:
        print(f"Erro ao receber arquivo: {str(e)}")

    #mensagem de recebimento com sucesso
    print(f"{nomeArquivo} recebido do cliente {enderecoCliente} com sucesso.")

#funcao para reenviar o aquivo pro cliente
def reenviaArquivo(nomeArquivo, tamanhoBuffer, udpSocket, enderecoCliente):
    try:
        with open(nomeArquivo, 'rb') as file:
            print(f"Enviando {nomeArquivo} de volta para {enderecoCliente}...")

            #codifica o novo nome do arquivo
            nomeArquivo_bytes = os.path.basename(nomeArquivo).encode()

            udpSocket.sendto(nomeArquivo_bytes, enderecoCliente)
            while True:
                data = file.read(tamanhoBuffer)              
                if not data:
                    break
                udpSocket.sendto(data, enderecoCliente)
            #espera o final para saber que acabou o reenvio
            udpSocket.sendto(b"FINAL", enderecoCliente)  

    #tratamento para erros no reenvio      
    except FileNotFoundError as e:
        print(f"Erro no reenvio: Arquivo {nomeArquivo} não encontrado.")
    except socket.error as e:
        print(f"Erro de socket no reenvio: {str(e)}")
    except Exception as e:
        print(f"Erro ao reenviar arquivo: {str(e)}")

    #mensagem de reevio com sucesso
    print(f"{nomeArquivo} enviado para {enderecoCliente} com sucesso.")

def main():
    host = 'localhost'
    port = 12345
    tamanhoBuffer = 1024

    udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udpSocket.bind((host, port))

    print("Server UDP está pronto para receber arquivos.")

    while True:

        #espera o nome do arquivo enviado pelo cliente
        data, enderecoCliente = udpSocket.recvfrom(tamanhoBuffer)
        #decodifica pra string
        nomeArquivo = data.decode()  

        #se o nome do arquivo recebido for SAIR significa que o cliente fechou a conexao e fecha a conexao tbm
        #isso eh so para os teste, esse trecho nao eh necessario no codigo
        if nomeArquivo == "SAIR":
            print("Cliente encerrou a conexão.")
            break

        #recebe o arquivo do cliente e reenvia
        recebeArquivo(nomeArquivo, tamanhoBuffer, udpSocket, enderecoCliente)

    #encerra o socket
    udpSocket.close()

if __name__ == "__main__":
    main()