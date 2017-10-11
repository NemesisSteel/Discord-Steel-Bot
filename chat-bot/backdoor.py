import asyncio

def make_console(bot):
    class Console(asyncio.Protocol):
        def connection_made(self, transport):
            self.transport = transport
            self.transport.write(b'>>> ')
            self.bot = bot

        def data_received(self, data):
            """
            Called when some data is received.
            The argument is a bytes object.
            """
            if data == b'\xff\xf4\xff\xfd\x06':
                self.transport.close()
                return
            message = data.decode()
            resp = str(eval(message)) + "\n>>> "
            self.transport.write(resp.encode('utf-8'))
    return Console

