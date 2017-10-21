import os
import websockets
import json
import logging
import threading
import asyncio


SCHWIFTY_URL = os.getenv('SCHWIFTY_URL', 'ws://127.0.0.1:8080')

log = logging.getLogger(__name__)

@asyncio.coroutine
def _ensure_coroutine_connect(url, klass, loop):
    ws = yield from websockets.connect(url, klass=klass, loop=loop)
    return ws

class KeepAliveHandler(threading.Thread):
    def __init__(self, ws, interval):
        threading.Thread.__init__(self)
        self.ws = ws
        self.interval = interval / 1000.0
        self.daemon = True
        self._stop_ev = threading.Event()

    def run(self):
        while not self._stop_ev.wait(self.interval):
            coro = self.ws.send(self.ws.OPCODE_HEARTBEAT, d=1337)
            f = asyncio.run_coroutine_threadsafe(coro, loop=self.ws.loop)
            try:
                f.result()
                self.ws.heartbeat_ack = False
            except Exception:
                self.stop()

    def stop(self):
        self._stop_ev.set()


class SchwiftyWebsocket(websockets.client.WebSocketClientProtocol):

    OPCODE_HELLO            = 0
    OPCODE_IDENTIFY         = 1
    OPCODE_HEARTBEAT        = 2
    OPCODE_HEARTBEAT_ACK    = 3
    OPCODE_DISPATCH         = 4
    OPCODE_VOICE_CONNECT    = 5
    OPCODE_VOICE_DISCONNECT = 6
    OPCODE_VOICE_UPDATE     = 7
    OPCODE_PLAY             = 8
    OPCODE_STOP             = 9

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.timeout = 5
        self.heartbeat_ack = True
        self.heartbeat     = None
        self.shard = self.mee6.shard

    async def received_message(self, msg):
        msg = msg.decode('utf-8')
        log.info(">> " + msg)
        msg = json.loads(msg)

        op = msg.get('op')
        d  = msg.get('d')
        t  = msg.get('t')


        if op == self.OPCODE_HELLO:
            await self.send(
                self.OPCODE_IDENTIFY,
                d=dict(shard=self.shard)
            )
            self.heartbeat = KeepAliveHandler(self, d)
            self.heartbeat.start()
            return

        if op == self.OPCODE_HEARTBEAT_ACK:
            self.heartbeat_ack = True
            return

        if op == self.OPCODE_DISPATCH:
            coro = self.mee6.dispatch_schwifty_event(t, d)
            self.loop.create_task(coro)
            return

    async def poll_event(self):
        try:
            msg = await self.recv()
            await self.received_message(msg)
        except websockets.exceptions.ConnectionClosed as e:
            log.info('Websocket closed with {0.code} ({0.reason}), attempting a reconnect.'.format(e))
            self.heartbeat.stop()
            self.heartbeat = None
            raise e

    async def send(self, op, t=None, d=None):
        payload = {'op': op}

        if t is not None:
            payload['t'] = t

        if d is not None:
            payload['d'] = d

        try:
            frame = json.dumps(payload)
            log.info("<< " + frame)
            await super().send(frame.encode('utf-8'))
        except websockets.exceptions.ConnectionClosed as e:
            log.info('Websocket closed. Cannot send message.')

    @classmethod
    @asyncio.coroutine
    def create(cls, shard, mee6):
        cls.mee6 = mee6
        try:
            coro = websockets.connect(SCHWIFTY_URL, klass=cls,
                                      loop=mee6.loop,
                                      timeout=5)
            ws = yield from coro
            return ws
        except (websockets.exceptions.InvalidHandshake, asyncio.TimeoutError,
                ConnectionRefusedError, OSError) as e:
            log.warn('{} Cannot connect to schwifty. Retrying.'.format(e))
            yield from asyncio.sleep(3)
            return (yield from cls.create(shard, mee6))

    async def voice_connect(self, guild_id):
        await self.send(self.OPCODE_VOICE_CONNECT, d=int(guild_id))

    async def voice_disconnect(self, guild_id):
        await self.send(self.OPCODE_VOICE_DISCONNECT, d=int(guild_id))

    async def play(self, guild_id, url):
        await self.send(
            self.OPCODE_PLAY,
            d=dict(guild_id=int(guild_id), url=url)
        )

    async def stop(self, guild_id):
        await self.send(
            self.OPCODE_STOP,
            d=int(guild_id)
        )

    async def voice_update(self, payload):
        await self.send(
            self.OPCODE_VOICE_UPDATE,
            d=payload
        )
