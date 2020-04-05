import telebot
import user_details


class BotManager(object):
    API_TOKEN = '1187013257:AAGkU0Md05rHtEkBJ465AARklivI7nfDG1Q'
    WELCOME_MSG = ("שלום, אני בוט.\n"
                   "אני אעזור לך להתמודד עם הלחץ הנפשי של הפורומים.")

    def __init__(self):
        self.bot = telebot.TeleBot(self.API_TOKEN)
        self._user_dict = {}

    # error handling if user isn't known yet
    # had to use the /start command and are therefore known to the bot
    def get_user(self, chat_id):
        if chat_id in self._user_dict:
            return self._user_dict[chat_id]

        self.add_user(chat_id, user_details.UNKNOWN)

        return user_details.UNKNOWN

    def add_user(self, chat_id, phone_number):
        self.bot.send_message(chat_id, "שנייה סורק אותך...")
        self._user_dict[chat_id] = user_details.User(phone_number)

    def run(self):
        self.bot.enable_save_next_step_handlers(delay=2)
        self.bot.load_next_step_handlers()
        self.bot.polling()
