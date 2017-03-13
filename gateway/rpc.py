from aiohttp import web
from logger import Logger


def rpc(method):
    method.is_rpc = True
    return method


class RPCException(Exception):
    pass


class RPCServer(Logger):
    def __init__(self, bot):
        self.bot = bot
        self.loop = bot.loop

        self.rpc_app = web.Application()
        self.rpc_app.router.add_get('/', self.rpc_hello)
        self.rpc_app.router.add_get('/rpc', self.rpc_handler)

    def __str__(self):
        return 'RPC-{b.shard_id}-{b.shard_count}'.format(b=self.bot)

    def _get_rpc_methods(self):
        bot = self.bot
        attrs = map(lambda attr_name: getattr(bot, attr_name), dir(bot))
        methods = filter(inspect.ismethod, attrs)
        rpc_methods = filter(lambda m: hasattr(m, 'is_rpc'), methods)
        return rpc_methods

    async def rpc_handler(self, request):
        body = await request.json()
        rpc_method_name = body.get('method')
        params = body.get('params', [])

        rpc_methods = self._get_rpc_methods()
        rpc_method = find(lambda m: m.__name__ == rpc_method_name,
                                rpc_methods)

        if rpc_method is None:
            return web.json_response({'error': 'method_not_found'})

        args = list(inspect.signature(method).parameters)[1:]
        if len(args) > len(params):
            return web.json_response({'error': 'missing_params'})
        if len(args) < len(params):
            return web.json_response({'error': 'too_many_params'})


        try:
            if inspect.iscoroutinefunction(rpc_method):
                resp = await rpc_method(*params)
            else:
                resp = rpc_method(*params)
        except RPCException as e:
            return web.json_response({'error': str(e)})

        return web.json_response({'response': dump(resp)})

    def run(self):
        handler = self.rpc_app.make_handler()
        srv = self.loop.create_server(handler, '0.0.0.0', 8080)
        self.loop.create_task(srv)
        self.log('RPC serving on 0.0.0.0:8080')

    def rpc_hello(self, request):
        bot = self.bot
        rsp = {'id': str(bot),
               'guilds_count': len(bot.guilds)}
        return web.json_response(rsp)

