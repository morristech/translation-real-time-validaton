import asyncio
import notifier

app = notifier.main({})
f = app.loop.create_server(app.make_handler(), '0.0.0.0', 5001)
srv = app.loop.run_until_complete(f)
print('serving on', srv.sockets[0].getsockname())
try:
    app.loop.run_forever()
except KeyboardInterrupt:
    pass
