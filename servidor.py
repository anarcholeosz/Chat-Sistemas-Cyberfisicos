import socket as sock
import threading

# Envia a lista de usuários para todos os clientes conectados
def enviar_lista_usuarios():
    lista = "\n".join(nomes_clientes)  # Agrega os nomes dos usuários em uma única string
    mensagem = f"LISTA USUARIOS:\n{lista}"
    for cliente in lista_clientes:  # Itera pelos clientes conectados
        try:
            cliente.send(mensagem.encode())  # Envia a mensagem para o cliente
        except:
            # Se der erro ao enviar, remove o cliente
            remover(cliente, nomes_clientes[lista_clientes.index(cliente)])  # Ativa o protocolo de remoção

# Função para recebimento de mensagem do cliente
def recebe_dados(sock_cliente, endereco):
    nome = sock_cliente.recv(50).decode()  # Todo nome é menor que 50 bytes
    lista_clientes.append(sock_cliente)
    nomes_clientes.append(nome)
    print(f"Conexão bem sucedida com {nome} via endereço: {endereco}")
    broadcast(f"SISTEMA: {nome} entrou no chat.")  # Notifica todos que o cliente entrou
    enviar_lista_usuarios()  # Atualiza a lista de usuários para todos

    while True:
        try:
            mensagem = sock_cliente.recv(1024).decode()  # Recebe mensagens do cliente
            if mensagem:
                processar_mensagem(mensagem, sock_cliente, nome)  # Processa a mensagem recebida
            else:
                remover(sock_cliente, nome)  # O unico jeito de mandar uma mensagem sem conteudo é estando desconectado ou hacker strats
                break
        except:
            remover(sock_cliente, nome)  # Pior dos casos tira o dono da meia 
            break


def broadcast(mensagem, sock_remetente=None):
    for cliente in lista_clientes:
        if cliente != sock_remetente:  # Não envia para o remetente. Causava duplicatas, pois as mensagens eram tratadas no cliente
            try:
                cliente.send(mensagem.encode())  # Faz o broadcast de mensagens
            except:
                remover(cliente, nomes_clientes[lista_clientes.index(cliente)])


def unicast(mensagem, destinatario_nome, remetente_nome):#Funcao que trata as DMs. 
    if destinatario_nome in nomes_clientes: #Faz a verificacao do nome na lista de clientes
        indice = nomes_clientes.index(destinatario_nome) #Puxa qual o ID do nome atraves do tratamento de mensagem
        cliente_destinatario = lista_clientes[indice] #Cria uma variavem para armazenar
        try:
            cliente_destinatario.send(f"DMs De {remetente_nome}: {mensagem}".encode())  # Formata e envia ao usuario
        except:
            remover(cliente_destinatario, destinatario_nome)  # Remove o destinatário se der erro
    else:
        indice_remetente = nomes_clientes.index(remetente_nome)
        cliente_remetente = lista_clientes[indice_remetente]
        cliente_remetente.send(f"SISTEMA: Usuário {destinatario_nome} não encontrado.".encode()) #A verificacao de quais usuarios estao
        #no chat sempre é feita pelo server. Isso é a extensao da logica do cliente

def remover(cliente, nome):
    if cliente in lista_clientes:
        indice = lista_clientes.index(cliente)
        lista_clientes.remove(cliente)
        nomes_clientes.pop(indice)#pop => Remove o ultimo indice da pilha, reduzindo o valor total
        cliente.close()
        broadcast(f"SISTEMA: {nome} saiu do chat.")  # Avisa como mensagem de sistema. 
        enviar_lista_usuarios()  # Atualiza a lista de usuários

# A principal funcao do server
def processar_mensagem(mensagem, sock_cliente, nome):
    #Aqui sao feitas as verificacoes dos prefixos
    #Sempre é removido o prefixo logo após a verificacao
    if mensagem.startswith("CHAT:"):
        conteudo = mensagem[5:].strip()
        broadcast(f"CHAT {nome}>> {conteudo}", sock_cliente)  
    elif mensagem.startswith("DMs:"):
        try:
            #Esse é mais complexo devido a funcionalidade de DM envolver mais lógica
            partes = mensagem[4:].strip().split(" ", 1)  # Separa o destinatário e o conteúdo
            destinatario_nome = partes[0] #O primeiro indice da lista é sempre o nome do destinatario
            conteudo = partes[1] #E o segundo indice da lista é o conteúdo da mensagem
            unicast(conteudo, destinatario_nome, nome)  # Chama o unicast com o conteudo da mensagem, quem mandou e quem vai ler
        except IndexError:
            sock_cliente.send("SISTEMA: Comando de DM inválido.".encode())
    elif mensagem == "LISTA USUARIOS":
        lista = "\n".join(nomes_clientes)
        #Puxa a lista e envia. 
        sock_cliente.send(f"LISTA USUARIOS:\n{lista}".encode())  # Envia a lista de usuários para quem pediu
    elif mensagem == "SAIR":
        remover(sock_cliente, nome)  # Remove o cliente
    else:
        sock_cliente.send("SISTEMA: Comando não reconhecido.".encode())  # Informa comando inválido


HOST = '192.168.15.95'
PORTA = 9999


#Listas locais do servidor para armazenamentos e prints diversos
lista_clientes = []
nomes_clientes = []
sock_servidor = sock.socket(sock.AF_INET, sock.SOCK_STREAM)#Cria um socket novo. 
#AF_INET -> Usa IPV4
#SOCK_STREAM -> Usa TCP. O tal do TCP/IPV4 que vimos o semestre todo

# Fazemos o bind -> LINK do IP:PORTA
sock_servidor.bind((HOST, PORTA))
# Abrimos o servidor para o modo de escuta
sock_servidor.listen()
print(f"O servidor {HOST}:{PORTA} está aguardando conexões...")

#Funcionalidade de aceitar conexoes
while True:
    sock_conn, endereco = sock_servidor.accept()#Retorna um socket, o IP e a porta do cliente. Assim é aceita a conexao
    thread_cliente = threading.Thread(target=recebe_dados, args=[sock_conn, endereco])#Especifica o que a thread necessita para funcionar
    thread_cliente.start()#Inicializa o cliente no servidor
