import telebot
import config
import db


class UserNotExistError(Exception):
    pass


class BotManager(object):
    SAVE_NEXT_STEP_DELAY = 2  # Seconds
    WELCOME_MSG = ("שלום, אני בוט.\n"
                   "אני אעזור לך להתמודד עם הלחץ הנפשי של הפורומים.")
    PLUS_MSG = "כל הכבוד! יש לך עודף של {}"
    MINUS_MSG = "קודם כל.. בלי פאניקה! החוב שלך הוא {}"
    NEUTRAL_MSG = "הכל טוב והמאזן מושלם"

    def __init__(self):
        self.bot = telebot.TeleBot(config.config['API_TOKEN'])
        self._user_dict = {}

    # Error handling if user isn't known yet
    # Had to use the /start command and are therefore known to the bot
    def get_user(self, chat_id):
        try:
            user = db.DBUser(chat_id)
        except db.UserNotExistError:
            raise UserNotExistError()

        return user.data()

    def add_user(self, chat_id, phone_number):
        self.bot.send_message(chat_id, "שנייה סורק אותך...")
        db.DBUser(chat_id, phone=phone_number, create=True)

    def run(self):
        self.bot.enable_save_next_step_handlers(
            delay=self.SAVE_NEXT_STEP_DELAY)
        self.bot.load_next_step_handlers()
        self.bot.polling()
