import asyncio
import json
from asyncio import CancelledError, StreamReader, StreamWriter
from typing import Optional

from app import App


class Client:
    def __init__(self) -> None:
        self.reader: Optional[StreamReader] = None
        self.writer: Optional[StreamWriter] = None
        self.app: Optional[App] = None
        self.available_rooms: list[str] = []
        self.username: str = ''

    async def connect(self, host: str, port: int) -> None:
        # Connect to the server
        self.reader, self.writer = await asyncio.open_connection(host, port)

        # Recieve available rooms
        self.available_rooms = (await self.reader.read(100)).decode().strip().split('\n')
        if self.app:
            self.app.available_rooms.insert(0, *self.available_rooms)

        # Start recieving
        await self.__recieve()

    async def send(self, data: dict) -> None:
        if not self.writer:
            return

        self.writer.write(json.dumps(data).encode())
        await self.writer.drain()

    async def close(self) -> None:
        if not self.writer:
            return

        self.writer.close()
        await self.writer.wait_closed()

    async def __recieve(self) -> None:
        try:
            while True:
                if not self.reader:
                    continue

                # Get data
                data = json.loads(await self.reader.read(100))
                if 'data' not in data or 'user' not in data:
                    continue

                if 'text' in data['data']:
                    # Text data
                    if self.app:
                        self.app.history.insert(0, f'{data['user']} > {data['data']['text']}')
                    else:
                        print(f'\n{data['user']} > {data['data']['text']}\n> ', end='')
                elif 'file_name' in data['data'] and 'file_content' in data['data']:
                    # File data
                    with open(data['data']['file_name'], 'w') as file:
                        file.write(data['data']['file_content'])

                    if self.app:
                        self.app.history.insert(0, f'{data['user']} send a file {data['data']['file_name']}')
                    else:
                        print(f'\n{data['user']} send a file {data['data']['file_name']}\n> ', end='')

        except CancelledError:
            pass


async def main():
    app = App()
    client = Client()
    
    app.client = client
    client.app = app

    client_task = asyncio.create_task(client.connect('127.0.0.1', 8800))
    await asyncio.gather(asyncio.create_task(app.start_event_loop()))
    client_task.cancel()
    await client.close()

if __name__ == '__main__':
    asyncio.run(main())