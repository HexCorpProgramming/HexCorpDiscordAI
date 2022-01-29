from discord.ext.tasks import Loop


async def start_and_await_loop(loop: Loop):
    '''
    Changes the interval time for the given loop to 1 second, starts the loop,
    stops it immediately and then waits until the one scheduled execution has terminated.
    '''
    loop.change_interval(seconds=1, minutes=0, hours=0)
    loop.start()
    loop.stop()
    await loop.get_task()
