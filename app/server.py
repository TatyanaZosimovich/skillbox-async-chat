#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")

                for client in self.server.clients:
                    if client != self and client.login == self.login:
                        self.transport.write(
                            f"Логин {self.login} занят!\n".encode()
                        )
                        self.server.clients.remove(self)

                self.transport.write(
                    f"Привет, {self.login}! Вот 10 последних сообщений:\n".encode()
                )
                self.server.history_send(self)
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"

        for user in self.server.clients:
            user.transport.write(message.encode())


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []

    def history_add(self, message):
        self.history.append(message)
        if len(self.history) > 10:
            self.history.pop(0)

    def history_send(self, client):
        for message in self.history:
            client.transport.write(
                message.encode()
            )

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
