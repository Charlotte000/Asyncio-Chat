import asyncio
import os
import tkinter as tk
import tkinter.filedialog as tkfd
from typing import IO, Any


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Chat')
        self.resizable(True, True)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.is_open = True
        self.client: Any = None

        self.__init_chat_rooms()

    def __init_chat_rooms(self):
        def __join_room(room_name: str) -> None:
            if not room_name:
                return

            self.client.username = username.get()
            asyncio.create_task(self.client.send(
                {'username': self.client.username, 'room': room_name}))

            for widget in self.grid_slaves():
                widget.grid_forget()
                widget.destroy()

            self.__init_room()

        tk.Label(self, text='Username').grid(row=0, column=0)
        username = tk.Entry(self)
        username.insert(0, 'User')
        username.grid(row=0, column=1)

        tk.Label(self, text='Join room').grid(row=1, column=0, columnspan=2)
        self.available_rooms = tk.Listbox(self)
        self.available_rooms.bind(
            '<<ListboxSelect>>', lambda event: __join_room(event.widget.get(0)))
        self.available_rooms.grid(row=2, column=0, columnspan=2)

        tk.Label(self, text='Create new room').grid(
            row=3, column=0, columnspan=2)
        new_room = tk.Entry(self)
        new_room.bind(
            '<Return>', lambda event: __join_room(event.widget.get()))
        new_room.grid(row=4, column=0, columnspan=2)

    def __init_room(self):
        def __send(message: str) -> None:
            if not message:
                return

            asyncio.create_task(self.client.send({'text': message}))
            input_text.delete(0, 'end')
            self.history.insert(0, f'You > {message}')

        def __send_file(file: IO | None) -> None:
            if not file:
                return

            if file.readable():
                asyncio.create_task(self.client.send(
                    {'file_name': os.path.basename(file.name), 'file_content': file.read()}))

            file.close()

        self.history = tk.Listbox(self)
        self.history.grid(row=0, column=0)

        input_text = tk.Entry(self)
        input_text.bind('<Return>', lambda event: __send(event.widget.get()))
        input_text.grid(row=1, column=0)

        tk.Button(self, text='Send a file', command=lambda: __send_file(
            tkfd.askopenfile())).grid(row=2, column=0)

    def destroy(self) -> None:
        super().destroy()
        self.is_open = False

    async def start_event_loop(self):
        while self.is_open:
            self.update()
            await asyncio.sleep(0.05)
