from aiohttp import web
import time

class StatusServer:
    def __init__(self):
        self.start_time = time.time() # 記錄伺服器啟動時間

    async def status(self, request):
        return web.Response(text="Bot Online!")

    async def run(self):
        app = web.Application()
        app.router.add_get('/status', self.status)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 41760)
        await site.start()