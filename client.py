import socket
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import pickle
from datetime import datetime
import os
import threading
import struct

# cor do fundo #1B3FA2
# cor do chat #3C63CC
# cor da informacao entrou no chat #04C6CF


class Client(tk.Canvas):
    def __init__(self, client_online, first_frame, client_socket, clients_connected, user_id):
        """Função que inicializa o cliente, seus componentes tkinter e o socket do cliente para comunicação com o servidor."""

        super().__init__(client_online, bg="#1B3FA2")

        self.window = 'Client'

        self.first_frame = first_frame 
        self.first_frame.pack_forget() 

        self.client_online = client_online
        self.client_online.bind('<Return>', lambda e: self.sent_message(e))

        self.all_user_image = {}
        self.user_id = user_id
        self.clients_connected = clients_connected
        self.client_online.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.client_socket = client_socket
        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()

        x_co = int((screen_width / 2) - (550 / 2))
        y_co = int((screen_height / 2) - (400 / 2)) - 80
        self.client_online.geometry(f"550x400+{x_co}+{y_co}")

        user_image = Image.open(self.client_online.image_path)
        user_image = user_image.resize((40, 40), Image.ANTIALIAS)
        self.user_image = ImageTk.PhotoImage(user_image)

        self.y = 140
        self.clients_online_labels = {}

        self.create_text(470, 90, text="Usúarios ativos", font="lucida 12 bold", fill="white")

        tk.Label(self, text=f"Chat {self.client_online.room}", font="lucida 15 bold", bg="white").place(x=0, y=29, relwidth=1)

        container = tk.Frame(self)

        container.place(x=40, y=80, width=350, height=250)
        self.canvas = tk.Canvas(container, bg="#3C63CC")
        self.scrollable_frame = tk.Frame(self.canvas, bg="#3C63CC")

        scrollable_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        def configure_scroll_region(e):
            """Função que configura o scroll da janela."""

            self.canvas.configure(scrollregion=self.canvas.bbox('all'))


        def resize_frame(e):
            """Função que redimensiona o frame."""

            self.canvas.itemconfig(scrollable_window, width=e.width)


        self.scrollable_frame.bind("<Configure>", configure_scroll_region)

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.yview_moveto(1.0)

        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", resize_frame)
        self.canvas.pack(fill="both", expand=True)

        send_button = tk.Button(self, text="Enviar", fg="black", font="lucida 11 bold", bg="white", padx=10,
                                relief="solid", bd=2, command=self.sent_message)
        send_button.place(x=315, y=350)

        self.entry = tk.Text(self, font="lucida 10 bold", width=38, height=2,
                             highlightcolor="blue", highlightthickness=1)
        self.entry.place(x=40, y=345)

        self.entry.focus_set()

        m_frame = tk.Frame(self.scrollable_frame, bg="#04C6CF")

        t_label = tk.Label(m_frame, bg="#04C6CF", text=datetime.now().strftime('%H:%M'), font="lucida 9 bold")
        t_label.pack()

        m_label = tk.Label(m_frame, wraplength=250, text=f"Bem-vindo ao Chat, {self.client_online.user }!",
                           font="lucida 10 bold", bg="white")
        m_label.pack(fill="x")

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.pack(fill="both", expand=True)

        self.clients_online([]) # chama a função que cria os labels dos usuarios online

        t = threading.Thread(target=self.receive_data) # cria a thread que recebe os dados do servidor
        t.setDaemon(True) # define que a thread é uma daemon thread
        t.start() # inicia a thread


    def receive_data(self):
        """Função que recebe os dados do servidor e os trata para exibir na tela do cliente."""

        while True: 
            try: # tenta receber os dados do servidor
                data_type = self.client_socket.recv(1024).decode() 

                if data_type == 'notificacao':
                    data_size = self.client_socket.recv(2048)
                    data_size_int = struct.unpack('i', data_size)[0]

                    b = b''
                    while True:
                        data_bytes = self.client_socket.recv(1024)
                        b += data_bytes
                        if len(b) == data_size_int:
                            break
                    data = pickle.loads(b)
                    self.notification(data)

                else:
                    data_bytes = self.client_socket.recv(1024)
                    data = pickle.loads(data_bytes)
                    self.received_message(data)

            except ConnectionAbortedError: # caso o servidor seja desconectado
                print("você saiu...")
                self.client_socket.close()
                break
            except ConnectionResetError: # caso o servidor esteja desconectado
                messagebox.showinfo(title='Sem conexão!', message="Servidor offline..tente conectar novamente mais tarde")
                self.client_socket.close()
                self.login()
                break

    def on_closing(self):
        """Função que fecha a janela do cliente e envia a mensagem para o servidor que o usuário saiu."""

        if self.window == 'Client': 
            res = messagebox.askyesno(title='Aviso!',message="Você realmente quer se desconectar?")
            if res:
                import os
                os.remove(self.all_user_image[self.user_id])
                self.client_socket.close()
                self.login()
        else:
            self.client_online.destroy()

    def received_message(self, data):
        """Função que trata os dados recebidos do servidor e os exibe na tela do cliente como uma mensagem recebida."""

        message = data['message'] # pega a mensagem
        from_ = data['from'] # pega o nome do usuário que enviou a mensagem

        sender_image = self.clients_connected[from_][1]
        sender_image_extension = self.clients_connected[from_][2]

        with open(f"{from_}.{sender_image_extension}", 'wb') as f:
            f.write(sender_image) 

        m_frame = tk.Frame(self.scrollable_frame, bg="#3C63CC")

        m_frame.columnconfigure(1, weight=1)

        t_label = tk.Label(m_frame, bg="#3C63CC",fg="white", text=datetime.now().strftime('%H:%M'), font="lucida 7 bold",
                           justify="left", anchor="w")
        t_label.grid(row=0, column=1, padx=2, sticky="w")

        m_label = tk.Label(m_frame, wraplength=250,fg="black", bg="#c5c7c9", text=message, font="lucida 9 bold", justify="left",
                           anchor="w")
        m_label.grid(row=1, column=1, padx=2, pady=2, sticky="w")

        i_label = tk.Label(m_frame, bg="#3C63CC", text=self.clients_connected.get(from_)[0], font="lucida 9 bold", fg="white")
        i_label.grid(row=1, column=0, rowspan=2, sticky="e")

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def sent_message(self, event=None):
        """Função que envia a mensagem para o servidor e exibe na tela do cliente como uma mensagem enviada."""

        message = self.entry.get('1.0', 'end-1c') # pega a mensagem digitada

        if message: # caso a mensagem não seja vazia
            if event:
                message = message.strip() 
            self.entry.delete("1.0", "end-1c") 

            from_ = self.user_id

            data = {'from': from_, 'message': message} # cria um dicionário com os dados da mensagem
            data_bytes = pickle.dumps(data) # converte o dicionário em bytes

            self.client_socket.send(data_bytes) # envia os dados para o servidor

            m_frame = tk.Frame(self.scrollable_frame, bg="#3C63CC")

            m_frame.columnconfigure(0, weight=1)

            t_label = tk.Label(m_frame, bg="#3C63CC", fg="white", text=datetime.now().strftime('%H:%M'),
                               font="lucida 7 bold", justify="right", anchor="e")
            t_label.grid(row=0, column=0, padx=2, sticky="e")

            m_label = tk.Label(m_frame, wraplength=250, text=message, fg="black", bg="white",
                               font="lucida 9 bold", justify="left",
                               anchor="e")
            m_label.grid(row=1, column=0, padx=2, pady=2, sticky="e")

            i_label = tk.Label(m_frame, bg="#3C63CC", text=self.client_online.user, font="lucida 9 bold", fg="white")
            i_label.grid(row=1, column=1, rowspan=2, sticky="e")

            m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

            self.canvas.update_idletasks() # atualiza a tela
            self.canvas.yview_moveto(1.0) # move a tela para baixo

    def notification(self, data):
        """Função que trata os dados recebidos do servidor e os exibe na tela do cliente como uma notificação."""

        if data['n_type'] == 'entrou': # caso o usuário tenha entrado no chat

            name = data['name']
            image = data['image_bytes']
            extension = data['extension']
            message = data['message']
            client_id = data['id']
            self.clients_connected[client_id] = (name, image, extension)
            self.clients_online([client_id, name, image, extension])

        elif data['n_type'] == 'saiu': # caso o usuário tenha saído do chat
            client_id = data['id']
            message = data['message']
            self.remove_labels(client_id)
            del self.clients_connected[client_id]

        m_frame = tk.Frame(self.scrollable_frame, bg="#3C63CC") 

        t_label = tk.Label(m_frame, fg="white", bg="#3C63CC", text=datetime.now().strftime('%H:%M'),
                           font="lucida 9 bold")
        t_label.pack()

        m_label = tk.Label(m_frame, wraplength=250, text=message, font="lucida 10 bold", justify="left", bg="sky blue")
        m_label.pack()

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e") # exibe a notificação na tela

        self.canvas.yview_moveto(1.0) 

    def clients_online(self, new_added):
        """Função que adiciona os usuários que entraram no chat na tela do cliente."""

        if not new_added: # caso não tenha nenhum usuário novo
            pass
            for user_id in self.clients_connected:
                name = self.clients_connected[user_id][0]
                image_bytes = self.clients_connected[user_id][1]
                extension = self.clients_connected[user_id][2]

                with open(f"{user_id}.{extension}", 'wb') as f:
                    f.write(image_bytes)

                self.all_user_image[user_id] = f"{user_id}.{extension}"

                b = tk.Label(self, text=f'- {name}', compound="left",fg="white", bg="#1B3FA2", font="lucida 10 bold", padx=15)

                self.clients_online_labels[user_id] = (b, self.y)

                b.place(x=400, y=self.y)
                self.y += 30
        else: # caso tenha usuários novos
            user_id = new_added[0]
            name = new_added[1]
            image_bytes = new_added[2]
            extension = new_added[3]

            with open(f"{user_id}.{extension}", 'wb') as f:
                f.write(image_bytes)

            self.all_user_image[user_id] = f"{user_id}.{extension}"

            b = tk.Label(self, text=f'- {name}', compound="left", fg="white", bg="#1B3FA2",
                         font="lucida 10 bold", padx=15)
            self.clients_online_labels[user_id] = (b, self.y)

            b.place(x=400, y=self.y)
            self.y += 30

    def remove_labels(self, client_id):
        """Função que remove os usuários que saíram do chat da tela do cliente."""

        for user_id in self.clients_online_labels.copy(): # percorre todos os usuários que estão online
            b = self.clients_online_labels[user_id][0]
            y_co = self.clients_online_labels[user_id][1]
            if user_id == client_id: # caso o usuário que saiu seja o mesmo que estava na tela
                print("yes")
                b.destroy()
                del self.clients_online_labels[client_id]
                import os

            elif user_id > client_id: # caso o usuário que saiu seja um usuário que estava na tela e que foi removido
                y_co -= 60
                b.place(x=510, y=y_co)
                self.clients_online_labels[user_id] = (b, y_co)
                self.y -= 60

    def login(self):
        """Função que faz o login do usuário no chat."""

        self.destroy()
        self.client_online.geometry(f"550x400+{self.client_online.x_co}+{self.client_online.y_co}")
        self.client_online.first_frame.pack(fill="both", expand=True)
        self.window = None

