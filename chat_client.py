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

room_existe = []

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass


class FirstScreen(tk.Tk):
    def __init__(self):
        super().__init__()

        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()

        self.x_co = int((screen_width / 2) - (550 / 2))
        self.y_co = int((screen_height / 2) - (400 / 2)) - 80
        self.geometry(f"550x400+{self.x_co}+{self.y_co}")
        self.title("Chat TCP")

        self.user = None
        self.image_extension = None
        self.image_path = None
        self.room = None

        self.first_frame = tk.Frame(self, bg="#595656")
        self.first_frame.pack(fill="both", expand=True)

        self.user_image = 'images/user.png'

        head = tk.Label(self.first_frame, text="Chat TCP", font="lucida 17 bold", bg="white")
        head.place(relwidth=1, y=24)

        self.username = tk.Label(self.first_frame, text="Nome de Usuário", font="lucida 12 bold", bg="white")
        self.username.place(x=100, y=150)

        self.username_entry = tk.Entry(self.first_frame,  font="lucida 12 bold", width=10,
                                       highlightcolor="blue", highlightthickness=1)
        self.username_entry.place(x=250, y=150)

        self.username_entry.focus_set()

        self.room = tk.Label(self.first_frame, text="Nome da Sala", font="lucida 12 bold", bg="white")
        self.room.place(x=100, y=200)

        self.room_entry = tk.Entry(self.first_frame,  font="lucida 12 bold", width=10,
                                       highlightcolor="blue", highlightthickness=1)
        self.room_entry.place(x=250, y=200)

        self.room_entry.focus_set()

        submit_button = tk.Button(self.first_frame, text="Entrar no Chat", font="lucida 12 bold", padx=30, cursor="hand2",
                                  command=self.process_data, bg="white", relief="solid", bd=2)

        submit_button.place(x=170, y=275)

        self.mainloop()

    def process_data(self):
        global room_existe

        if self.username_entry.get():

            if len((self.username_entry.get()).strip()) > 6:
                self.user = self.username_entry.get()[:6]+"."
            else:
                self.user = self.username_entry.get()

            if len((self.room_entry.get()).strip()) > 6:
                self.room = self.room_entry.get()[:6]+"."
            else:
                self.room = self.room_entry.get()

            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                client_socket.connect(("localhost", 12345))
                status = client_socket.recv(1024).decode()
                if status == 'not_allowed':
                    client_socket.close()
                    messagebox.showinfo(title="Não foi possível se conectar!", message='Desculpe, o servidor está completamente ocupado.'
                                                                         'Tente mais tarde')
                    return

            except ConnectionRefusedError:
                messagebox.showinfo(title="Não foi possível se conectar!", message="O servidor está offline, tente novamente mais tarde.")
                print("O servidor está offline, tente novamente mais tarde.")
                return

            client_socket.send(self.user.encode('utf-8'))

            if not self.image_path:
                self.image_path = self.user_image
            with open(self.image_path, 'rb') as image_data:
                image_bytes = image_data.read()

            image_len = len(image_bytes)
            image_len_bytes = struct.pack('i', image_len)
            client_socket.send(image_len_bytes)

            if client_socket.recv(1024).decode() == 'received':
                client_socket.send(str(self.image_extension).strip().encode())

            client_socket.send(image_bytes)

            clients_data_size_bytes = client_socket.recv(1024)
            clients_data_size_int = struct.unpack('i', clients_data_size_bytes)[0]
            b = b''
            while True:
                clients_data_bytes = client_socket.recv(1024)
                b += clients_data_bytes
                if len(b) == clients_data_size_int:
                    break

            clients_connected = pickle.loads(b)

            client_socket.send('image_received'.encode())

            user_id = struct.unpack('i', client_socket.recv(1024))[0]
            print()
            print(f"{self.user} is user no. {user_id}")
            ChatScreen(self, self.first_frame, client_socket, clients_connected, user_id)


class ChatScreen(tk.Canvas):
    def __init__(self, parent, first_frame, client_socket, clients_connected, user_id):
        super().__init__(parent, bg="#2b2b2b")

        self.window = 'ChatScreen'

        self.first_frame = first_frame
        self.first_frame.pack_forget()

        self.parent = parent
        self.parent.bind('<Return>', lambda e: self.sent_message_format(e))

        self.all_user_image = {}
        self.user_id = user_id
        self.clients_connected = clients_connected
        self.parent.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.client_socket = client_socket
        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()

        x_co = int((screen_width / 2) - (680 / 2))
        y_co = int((screen_height / 2) - (750 / 2)) - 80
        self.parent.geometry(f"680x750+{x_co}+{y_co}")

        user_image = Image.open(self.parent.image_path)
        user_image = user_image.resize((40, 40), Image.ANTIALIAS)
        self.user_image = ImageTk.PhotoImage(user_image)

        self.y = 140
        self.clients_online_labels = {}

        self.create_text(570, 120, text="Usúarios ativos", font="lucida 12 bold", fill="white")

        tk.Label(self, text=f"Chat {self.parent.room}", font="lucida 15 bold", bg="white").place(x=0, y=29, relwidth=1)

        container = tk.Frame(self)

        container.place(x=40, y=120, width=450, height=550)
        self.canvas = tk.Canvas(container, bg="#595656")
        self.scrollable_frame = tk.Frame(self.canvas, bg="#595656")

        scrollable_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        def configure_scroll_region(e):
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))

        def resize_frame(e):
            self.canvas.itemconfig(scrollable_window, width=e.width)

        self.scrollable_frame.bind("<Configure>", configure_scroll_region)

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.yview_moveto(1.0)

        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", resize_frame)
        self.canvas.pack(fill="both", expand=True)

        send_button = tk.Button(self, text="Enviar", fg="black", font="lucida 11 bold", bg="white", padx=10,
                                relief="solid", bd=2, command=self.sent_message_format)
        send_button.place(x=400, y=680)

        self.entry = tk.Text(self, font="lucida 10 bold", width=38, height=2,
                             highlightcolor="blue", highlightthickness=1)
        self.entry.place(x=40, y=681)

        self.entry.focus_set()

        m_frame = tk.Frame(self.scrollable_frame, bg="#d9d5d4")

        t_label = tk.Label(m_frame, bg="#d9d5d4", text=datetime.now().strftime('%H:%M'), font="lucida 9 bold")
        t_label.pack()

        m_label = tk.Label(m_frame, wraplength=250, text=f"Bem-vindo ao Chat, {self.parent.user }!",
                           font="lucida 10 bold", bg="white")
        m_label.pack(fill="x")

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.pack(fill="both", expand=True)

        self.clients_online([])

        t = threading.Thread(target=self.receive_data)
        t.setDaemon(True)
        t.start()

    def receive_data(self):
        while True:
            try:
                data_type = self.client_socket.recv(1024).decode()

                if data_type == 'notification':
                    data_size = self.client_socket.recv(2048)
                    data_size_int = struct.unpack('i', data_size)[0]

                    b = b''
                    while True:
                        data_bytes = self.client_socket.recv(1024)
                        b += data_bytes
                        if len(b) == data_size_int:
                            break
                    data = pickle.loads(b)
                    self.notification_format(data)

                else:
                    data_bytes = self.client_socket.recv(1024)
                    data = pickle.loads(data_bytes)
                    self.received_message_format(data)

            except ConnectionAbortedError:
                print("você saiu...")
                self.client_socket.close()
                break
            except ConnectionResetError:
                messagebox.showinfo(title='Sem conexão!', message="Servidor offline..tente conectar novamente mais tarde")
                self.client_socket.close()
                self.first_screen()
                break

    def on_closing(self):
        if self.window == 'ChatScreen':
            res = messagebox.askyesno(title='Aviso!',message="Você realmente quer se desconectar?")
            if res:
                import os
                os.remove(self.all_user_image[self.user_id])
                self.client_socket.close()
                self.first_screen()
        else:
            self.parent.destroy()

    def received_message_format(self, data):

        message = data['message']
        from_ = data['from']

        sender_image = self.clients_connected[from_][1]
        sender_image_extension = self.clients_connected[from_][2]

        with open(f"{from_}.{sender_image_extension}", 'wb') as f:
            f.write(sender_image)

        m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

        m_frame.columnconfigure(1, weight=1)

        t_label = tk.Label(m_frame, bg="#595656",fg="white", text=datetime.now().strftime('%H:%M'), font="lucida 7 bold",
                           justify="left", anchor="w")
        t_label.grid(row=0, column=1, padx=2, sticky="w")

        m_label = tk.Label(m_frame, wraplength=250,fg="black", bg="#c5c7c9", text=message, font="lucida 9 bold", justify="left",
                           anchor="w")
        m_label.grid(row=1, column=1, padx=2, pady=2, sticky="w")

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def sent_message_format(self, event=None):

        message = self.entry.get('1.0', 'end-1c')

        if message:
            if event:
                message = message.strip()
            self.entry.delete("1.0", "end-1c")

            from_ = self.user_id

            data = {'from': from_, 'message': message}
            data_bytes = pickle.dumps(data)

            self.client_socket.send(data_bytes)

            m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

            m_frame.columnconfigure(0, weight=1)

            t_label = tk.Label(m_frame, bg="#595656", fg="white", text=datetime.now().strftime('%H:%M'),
                               font="lucida 7 bold", justify="right", anchor="e")
            t_label.grid(row=0, column=0, padx=2, sticky="e")

            m_label = tk.Label(m_frame, wraplength=250, text=message, fg="black", bg="white",
                               font="lucida 9 bold", justify="left",
                               anchor="e")
            m_label.grid(row=1, column=0, padx=2, pady=2, sticky="e")

            i_label = tk.Label(m_frame, bg="#595656", text=self.parent.user, font="lucida 9 bold", fg="white")
            i_label.grid(row=1, column=1, rowspan=2, sticky="e")

            m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

            self.canvas.update_idletasks()
            self.canvas.yview_moveto(1.0)

    def notification_format(self, data):
        if data['n_type'] == 'joined':

            name = data['name']
            image = data['image_bytes']
            extension = data['extension']
            message = data['message']
            client_id = data['id']
            self.clients_connected[client_id] = (name, image, extension)
            self.clients_online([client_id, name, image, extension])

        elif data['n_type'] == 'left':
            client_id = data['id']
            message = data['message']
            self.remove_labels(client_id)
            del self.clients_connected[client_id]

        m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

        t_label = tk.Label(m_frame, fg="white", bg="#595656", text=datetime.now().strftime('%H:%M'),
                           font="lucida 9 bold")
        t_label.pack()

        m_label = tk.Label(m_frame, wraplength=250, text=message, font="lucida 10 bold", justify="left", bg="sky blue")
        m_label.pack()

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.canvas.yview_moveto(1.0)

    def clients_online(self, new_added):
        if not new_added:
            pass
            for user_id in self.clients_connected:
                name = self.clients_connected[user_id][0]
                image_bytes = self.clients_connected[user_id][1]
                extension = self.clients_connected[user_id][2]

                with open(f"{user_id}.{extension}", 'wb') as f:
                    f.write(image_bytes)

                self.all_user_image[user_id] = f"{user_id}.{extension}"

                b = tk.Label(self, text=name, compound="left",fg="white", bg="#2b2b2b", font="lucida 10 bold", padx=15)

                self.clients_online_labels[user_id] = (b, self.y)

                b.place(x=500, y=self.y)
                self.y += 60
        else:
            user_id = new_added[0]
            name = new_added[1]
            image_bytes = new_added[2]
            extension = new_added[3]

            with open(f"{user_id}.{extension}", 'wb') as f:
                f.write(image_bytes)

            self.all_user_image[user_id] = f"{user_id}.{extension}"

            b = tk.Label(self, text=name, compound="left", fg="white", bg="#2b2b2b",
                         font="lucida 10 bold", padx=15)
            self.clients_online_labels[user_id] = (b, self.y)

            b.place(x=500, y=self.y)
            self.y += 60

    def remove_labels(self, client_id):
        for user_id in self.clients_online_labels.copy():
            b = self.clients_online_labels[user_id][0]
            y_co = self.clients_online_labels[user_id][1]
            if user_id == client_id:
                print("yes")
                b.destroy()
                del self.clients_online_labels[client_id]
                import os

            elif user_id > client_id:
                y_co -= 60
                b.place(x=510, y=y_co)
                self.clients_online_labels[user_id] = (b, y_co)
                self.y -= 60

    def first_screen(self):
        self.destroy()
        self.parent.geometry(f"550x400+{self.parent.x_co}+{self.parent.y_co}")
        self.parent.first_frame.pack(fill="both", expand=True)
        self.window = None


FirstScreen()