import socket
import struct
import pickle
import threading

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 12345))
server_socket.listen(4)

clients_connected = {} # Dicionário que armazena os clientes conectados
clients_data = {}
count = 1


def server():
    """Função que inicia o servidor e aguarda conexões de clientes, sendo que cada cliente conectado é tratado por uma thread separada."""

    global count
    while True: # loop infinito para aguardar conexões de clientes
        print("Aguardando conexão...")
        client_socket, address = server_socket.accept()

        print(f"As conexões de {address} foram estabelecidas")
        print(len(clients_connected))
        if len(clients_connected) == 4: # Se o número de clientes conectados for igual a 4, exibe uma mensagem de erro
            client_socket.send('nao_permitido'.encode())

            client_socket.close()
            continue
        else: # Se o número de clientes conectados for menor que 4, inicia uma thread para tratar o cliente
            client_socket.send('permitido'.encode())

        try:
            client_name = client_socket.recv(1024).decode('utf-8') # Recebe o nome do cliente
        except:
            print(f"{endereço} desconectado") # Se o cliente desconectar, exibe uma mensagem
            client_socket.close() # Fecha a conexão com o cliente
            continue

        print(f"{address} identificou-se como {client_name}") # Exibe uma mensagem de identificação do cliente

        clients_connected[client_socket] = (client_name, count) # Adiciona o cliente ao dicionário de clientes conectados

        image_size_bytes = client_socket.recv(1024)
        image_size_int = struct.unpack('i', image_size_bytes)[0]

        client_socket.send('recebido'.encode())
        file_extension = client_socket.recv(1024).decode()

        b = b''
        while True: 
            file_bytes = client_socket.recv(1024)
            b += file_bytes
            if len(b) == image_size_int:
                break

        clients_data[count] = (client_name, b, file_extension) # Adiciona o cliente ao dicionário de dados dos clientes

        clients_data_bytes = pickle.dumps(clients_data)
        clients_data_length = struct.pack('i', len(clients_data_bytes))

        client_socket.send(clients_data_length)
        client_socket.send(clients_data_bytes)

        if client_socket.recv(1024).decode() == 'arquivo_recebido':
            client_socket.send(struct.pack('i', count))

            for client in clients_connected: # Envia uma notificação para todos os clientes conectados
                if client != client_socket:
                    client.send('notificacao'.encode()) 
                    data = pickle.dumps(
                        {'message': f"{clients_connected[client_socket][0]} entrou na sala", 'extension': file_extension,
                         'file_bytes': b, 'name': clients_connected[client_socket][0], 'n_type': 'entrou', 'id': count}) # Notificação mostrada para os clientes conectados
                    data_length_bytes = struct.pack('i', len(data))
                    client.send(data_length_bytes)

                    client.send(data) # Envia a notificação para o cliente
        count += 1
        t = threading.Thread(target=server_data, args=(client_socket,)) # Define uma thread para tratar o cliente
        t.start() # Inicia a thread


def server_data(client_socket):
    """Função que recebe dados de um cliente e envia para todos os outros clientes conectados."""

    while True: # loop infinito para receber dados do cliente
        try: 
            data_bytes = client_socket.recv(1024) # Recebe os dados do cliente
        except ConnectionResetError: # Caso o cliente seja desconectado
            print(f"{clients_connected[client_socket][0]} desconectado") # Se o cliente desconectar, exibe uma mensagem de erro

            for client in clients_connected:
                if client != client_socket:
                    client.send('notificacao'.encode())

                    data = pickle.dumps({'message': f"{clients_connected[client_socket][0]} deixou a conversa",
                                         'id': clients_connected[client_socket][1], 'n_type': 'saiu'}) # Notificação mostrada para os clientes conectados

                    data_length_bytes = struct.pack('i', len(data))
                    client.send(data_length_bytes)

                    client.send(data) # Envia a notificação para todos os clientes

            del clients_data[clients_connected[client_socket][1]] # Remove o cliente do dicionário de dados dos clientes
            del clients_connected[client_socket] # Remove o cliente do dicionário de clientes conectados
            client_socket.close() # Fecha a conexão com o cliente
            break
        except ConnectionAbortedError: 
            print(f"{clients_connected[client_socket][0]} desconectado inesperadamente.") # Se o cliente desconectar inesperadamente, exibe uma mensagem de erro

            for client in clients_connected:
                if client != client_socket:
                    client.send('notificacao'.encode())
                    data = pickle.dumps({'message': f"{clients_connected[client_socket][0]} deixou a conversa",
                                         'id': clients_connected[client_socket][1], 'n_type': 'saiu'}) # Notificação mostrada para os clientes conectados
                    data_length_bytes = struct.pack('i', len(data))
                    client.send(data_length_bytes)
                    client.send(data) # Envia a notificação para todos os clientes

            del clients_data[clients_connected[client_socket][1]] # Remove o cliente do dicionário de dados dos clientes
            del clients_connected[client_socket] # Remove o cliente do dicionário de clientes conectados
            client_socket.close() # Fecha a conexão com o cliente
            break

        for client in clients_connected: # Envia os dados para todos os clientes conectados
            if client != client_socket: # Se o cliente não for o que enviou os dados
                client.send('message'.encode()) # Envia uma mensagem para o cliente
                client.send(data_bytes) # Envia os dados para o cliente


server() # Inicia o servidor
