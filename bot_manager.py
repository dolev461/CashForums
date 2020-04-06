import telebot
import config
import db


class UserNotExistError(Exception):
    pass


class UserNotInvited(Exception):
    pass


class BotManager(object):
    SAVE_NEXT_STEP_DELAY = 2  # Seconds
    WELCOME_MSG = ("שלום, אני בוט.\n"
                   "אני אעזור לך להתמודד עם הלחץ הנפשי של הפורומים.\n\n"
                   "שנייה סורק אותך...")
    PLUS_MSG = "כל הכבוד! יש לך עודף של {}"
    MINUS_MSG = "קודם כל.. בלי פאניקה! החוב שלך הוא {}"
    NEUTRAL_MSG = "הכל טוב והמאזן מושלם"

    def __init__(self):
        self.bot = telebot.TeleBot(config.config['API_TOKEN'])
        self._user_dict = {}
        self._commands = {
            "/start": "Help",
            "/help": "Help",
            "/info": "Help"
        }
        self._admin_commands = {
            "/add": "Help",
            "/del": "Help"
        }

    @staticmethod
    def format_il_phone_number(phone):
        if phone.startswith('+972'):
            return phone
        if phone.startswith('972'):
            return '+{}'.format(phone)
        if phone.startswith('0'):
            return '+972{}'.format(phone.lstrip('0'))
        return '+972{}'.format(phone)

    # Error handling if user isn't known yet
    # Had to use the /start command and are therefore known to the bot
    def get_user(self, chat_id):
        try:
            return db.DBUser(chat_id)
        except db.UserNotExistError:
            raise UserNotExistError()

    def add_user(self, chat_id, phone_number):
        try:
            db.DBUser(chat_id, phone=BotManager.format_il_phone_number(phone_number), create=True)
        except db.UserNotExistError:
            raise UserNotInvited()

    def get_help(self, chat_id):
        commands = self._commands

        try:
            user = self.get_user(chat_id)
            print("Users: {}".format(user.groups()))
        except UserNotExistError:
            pass

        return "\n".join(
            ["{}: {}".format(cmd, desc)
             for cmd, desc in commands.items()])

    def run(self):
        self.bot.enable_save_next_step_handlers(
            delay=self.SAVE_NEXT_STEP_DELAY)
        self.bot.load_next_step_handlers()
        self.bot.polling()
