import telebot
import user_details


class BotManager(object):
    API_TOKEN = '1187013257:AAGkU0Md05rHtEkBJ465AARklivI7nfDG1Q'
    WELCOME_MSG = ("שלום, אני בוט.\n"
                   "אני אעזור לך להתמודד עם הלחץ הנפשי של הפורומים.\n"
                   "\nמה השם שלך?")

    def __init__(self):
        self.bot = telebot.TeleBot(self.API_TOKEN)
        self._user_dict = {}

    def get_user(self, chat_id):
        return self._user_dict[chat_id]

    def add_user(self, chat_id, name):
        self._user_dict[chat_id] = user_details.User(name)

    def run(self):
        self.bot.enable_save_next_step_handlers(delay=2)
        self.bot.load_next_step_handlers()
        self.bot.polling()
