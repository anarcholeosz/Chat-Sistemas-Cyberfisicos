import socket as sock
import threading
import os

# IP e PORTA do servidor que queremos nos conectar
HOST = '192.168.15.95'
PORTA = 9999
sock_cliente = sock.socket(sock.AF_INET, sock.SOCK_STREAM)

try:
    # Pede a conexao do HOST utilizando a PORTA especifica
    sock_cliente.connect((HOST, PORTA))
except ConnectionRefusedError:
    print("SISTEMA: Não foi possível conectar ao servidor.")
    exit()
#Gerador de cabeçalho, aparece muito aqui
print(5*"-" + "CHAT INICIADO" + 5*"-")


nome = input("Informe seu nome para entrar no chat: ")
sock_cliente.sendall(nome.encode())

# Todo tipo de mensagem é armazenado em listas dedicadas. Essas listas sao atualizadas dinamicamente 
# e chamadas toda vez que a tela é atualizada. Cada lista corresponde a uma fileira no chat
lista_usuarios = []
mensagens_sistema = []
mensagens_privadas = []
mensagens_chat = []

lock = threading.Lock()#?


def receber_mensagens(sock_cliente):
    while True:
        try:
            mensagem = sock_cliente.recv(1024).decode()#?
            if mensagem:
                with lock:
                    processar_mensagem(mensagem)
                    atualizar_tela()
            else:
                break
        except:
            print("SISTEMA: Conexão perdida com o servidor.")
            sock_cliente.close()
            break


def processar_mensagem(mensagem):
    #A ideia aqui é simples: Toda mensagem do server vem com um prefixo que indica qual a funcionalidade da mensagem
    #A funcao detecta qual tipo de mensagem e atualiza sua respectiva lista. Desse modo, quando a funcao atualizartela
    #for chamada ela sempre terá os valores atualizados da lista
    if mensagem.startswith("LISTA USUARIOS:"):

        lista = mensagem[len("LISTA USUARIOS:"):].strip().split('\n')
        #Essa é um pouco diferente: Ela puxa a lista completa e atualiza como lista ao inves de adicionar a uma lista
        #Isso é porque a lista de usuarios é uma lista unica e nao uma lista de mensagens continuas sendo adicionadas]

        global lista_usuarios        #listalistalistalista
        lista_usuarios = lista
    elif mensagem.startswith("SISTEMA:"):
        #Todas elas seguem o mesmo formato: Se o prefixo for X entao ele extrai o conteúdo depois do prefixo
        mensagens_sistema.append(mensagem[len("SISTEMA:"):].strip())
    elif mensagem.startswith("DMs De") or mensagem.startswith("DMs Para"):#Os dois tipos de DM
        mensagens_privadas.append(mensagem.strip())
    elif mensagem.startswith("CHAT"):
        mensagens_chat.append(mensagem[len("CHAT"):].strip())
    else:
        #Nunca consegui fazer esse funcionar
        mensagens_sistema.append(f"Mensagem desconhecida: {mensagem}")

#pqq linux nao tem a mesma nomenclatura?
def limpar_tela():
    if os.name == 'nt':
        os.system('cls')  # Para Windows
    else:
        os.system('clear')  # Para Linux/OS X



#Essa funcao é constantemente chamada, nao descobrimos maneira melhor de fazer isso. 
def atualizar_tela():
    limpar_tela()
    # Pra exibir a lista dos usuarios foi feito um loop de for. 
    print("=========== Lista de Usuários ===========")
    for idx, user in enumerate(lista_usuarios, start=1):#Enumerate imprime assim: 1. 2. 3.
        print(f"{idx}. {user}") #Numero do user e o nome dele
    print("========================================\n")


    print("=========== Sistema =====================")
    print("Digite /sair para sair do chat; Digite /dm [nome] [mensagem] para mensagens diretas; Digite /lista para listar usuários")
    for msg in mensagens_sistema[-5:]:  # Limite de 5 mensagens de sistema, com as mais novas abaixo.
        print(msg)
    print("========================================\n")

    print("=========== Mensagens Privadas =========")
    for msg in mensagens_privadas[-5:]:  
        print(msg)
    print("========================================\n")

    print("============== Chat ===================")
    for msg in mensagens_chat[-16:]:  # Chat com limite maior
        print(msg)
    print("========================================\n")


thread_receber = threading.Thread(target=receber_mensagens, args=(sock_cliente,)) #É necessário uma thread para receber mensagens e
thread_receber.daemon = True
thread_receber.start()

#Esse é o main loop do cliente: fica rodando esperando mensagens recebidas ou mandadas
try:
    while True:
        mensagem = input("Digite sua mensagem (ou comando): ")
        #O tratamento de DM é mais fácil no lado do cliente. Sao feitas verificacoes para ver se as resticoes se mantém
        if mensagem.startswith("/dm "):
            partes = mensagem[4:].split(' ', 1) #Procura o primeiro espaço
            if len(partes) == 2:#Se tiver mais do que o comando
                nome_destinatario, conteudo = partes #Separa a mensagem em dois: Nome e Conteúdo
                #Esse é o tratamento para mensagens ENVIADAS: entao vai ser feito o armazenamento aqui mesmo
                try:
                    sock_cliente.sendall(f"DMs: {nome_destinatario} {conteudo}".encode())
                    with lock:#Lock sendo usado para mandar mensagem sem problemas de processamento
                        mensagens_privadas.append(f"DMs Para {nome_destinatario}: {conteudo}") #Mensagem que vai ser recebida pelo server
                        atualizar_tela()#Sempre chamado dps de atualizar alguma lista
                except Exception as e:
                    print(f"SISTEMA: Erro ao enviar mensagem privada: {e}")
                    sock_cliente.close()
                    break
            else:
                print("Uso correto: /dm [destinatario] [mensagem]") #Xinga a pessoa q usou errado
        elif mensagem == "/lista":
            sock_cliente.sendall("LISTA USUARIOS".encode())
        elif mensagem == "/sair":
            sock_cliente.sendall("SAIR".encode())
            print("SISTEMA: Você saiu do chat.")
            sock_cliente.close()
            break
        else:#Se nao for nenhum comando entao é só mensagem de chat
            try:
                sock_cliente.sendall(f"CHAT: {mensagem}".encode())
                # Também adicionar às mensagens de chat
                with lock:
                    mensagens_chat.append(f"{nome}>> {mensagem}")#Formatacao padrao
                    atualizar_tela()
            except Exception as e:
                print(f"SISTEMA: Erro ao enviar mensagem: {e}")
                sock_cliente.close()
                break

except KeyboardInterrupt:
    sock_cliente.sendall("SAIR".encode())
    print("\nSISTEMA: Você saiu do chat.")
    sock_cliente.close()
