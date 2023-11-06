import asyncio
import json
from asyncio import CancelledError, Queue, StreamReader, StreamWriter
from dataclasses import dataclass


@dataclass
class User:
    writer: StreamWriter
    room: 'Room'
    name: str


@dataclass
class Message:
    user: User
    data: dict[str, str]


@dataclass
class Room:
    users: list[User]


class Server:
    def __init__(self) -> None:
        self.messages: Queue[Message] = Queue()
        self.rooms: dict[str, Room] = {'admin': Room([])}

    async def start(self, host: str, port: int) -> None:
        # Start server
        self.server = await asyncio.start_server(self.accept_connection, host, port)
        print(f'Started server at {host}: {port}')

        async with self.server:
            asyncio.create_task(self.process_messages())
            await self.server.serve_forever()

    async def accept_connection(self, reader: StreamReader, writer: StreamWriter) -> None:
        username: str = 'Undefined'
        try:
            # Send available rooms
            writer.write(('\n'.join(self.rooms.keys()) + '\n').encode())
            await writer.drain()

            # Recieve user info
            info = json.loads((await reader.read(100)))
            if 'username' not in info or 'room' not in info:
                raise ConnectionError

            username, room_name = info['username'], info['room']
            print(f'Connected {username}')

            # Create new room
            if room_name not in self.rooms:
                self.rooms[room_name] = Room([])

            # Connect to the room
            user = User(writer, self.rooms[room_name], username)
            self.rooms[room_name].users.append(user)
            print(f'User {username} joined {room_name} room')
        except ConnectionResetError:
            print(f'Disconnected {username}')
            return

        try:
            while True:
                data = await reader.read(100)
                if not data:
                    break

                await self.messages.put(Message(user, json.loads(data)))
        except CancelledError:
            pass
        except ConnectionResetError:
            pass
        finally:
            # Remove user from the room and clear empty rooms
            user.room.users.remove(user)
            # self.rooms = {
            #     name: room
            #     for name, room in self.rooms.items()
            #     if len(room.users) > 0
            # }

            print(f'Disconnected {username}')

    async def process_messages(self) -> None:
        while True:
            # Recieve message
            message = await self.messages.get()

            # Send message to the room members
            for room_user in message.user.room.users:
                if room_user == message.user:
                    continue

                room_user.writer.write(json.dumps(
                    {'user': message.user.name, 'data': message.data}).encode())
                await room_user.writer.drain()


if __name__ == '__main__':
    server = Server()
    asyncio.run(server.start('0.0.0.0', 8800))
