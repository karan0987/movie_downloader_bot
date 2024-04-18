from pyrogram import Client, __version__
from info import SESSION , API_ID , API_HASH , BOT_TOKEN
from functions import temp



class Bot(Client):

    def __init__(self):
        super().__init__(
            name=SESSION,
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=500,
            plugins={"root": "plugins"},
            sleep_threshold=5,
        )

    async def start(self):
        await super().start()
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        self.username = '@' + me.username
        print(f"Bot started!!!!!")
        print(
            f"""Bot Information:
Username: @{me.username}"""
              )

    async def stop(self, *args):
        await super().stop()
    
    async def iter_messages(self,chat_id: int,limit: int,offset: int = 0):
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current+new_diff+1)))
            for message in messages:
                yield message
                current += 1


app = Bot()
app.run()