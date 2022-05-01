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
from client import Client

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

            if len((self.username_entry.get()).strip()) > 10:
                self.user = self.username_entry.get()[:10]+"."
            else:
                self.user = self.username_entry.get()

            if len((self.room_entry.get()).strip()) > 10:
                self.room = self.room_entry.get()[:10]+"."
            else:
                self.room = self.room_entry.get()

            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                client_socket.connect(("localhost", 12345))
                status = client_socket.recv(1024).decode()
                if status == 'nao_permitido':
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

            if client_socket.recv(1024).decode() == 'recebido':
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

            client_socket.send('imagem_recebida'.encode())

            user_id = struct.unpack('i', client_socket.recv(1024))[0]
            print()
            print(f"{self.user} is user no. {user_id}")
            Client(self, self.first_frame, client_socket, clients_connected, user_id)

FirstScreen()