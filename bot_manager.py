import telebot
import config
import db


class UserAlreadyExistsError(Exception):
    pass


class UserAlreadyInGroupError(Exception):
    pass


class UserNotInGroupError(Exception):
    pass


class UserNotExistError(Exception):
    pass


class UserNotInvited(Exception):
    pass


class GroupAlreadyExists(Exception):
    pass


class GroupNotExistError(Exception):
    pass


class BotManager(object):
    SAVE_NEXT_STEP_DELAY = 2  # Seconds

    def __init__(self):
        self.bot = telebot.TeleBot(config.config['API_TOKEN'])
        # Save user details before adding it for external use
        self.pending_user = {
            "name": None,
            "phone": None,
            "group": None
        }
        self.pending_group = {
            "name": None,
            "admin": None,
        }
        self._commands = {
            "/start": "Register your telegram account to the bot",
            "/help": "Show this help section",
            "/info": "Get your balance in your associated groups"
        }
        self._group_admin_commands = {
            "/add": "Group admin command to add members",
            "/rm": "Group admin command to remove members",
            "/members": "Group admin command to display all group members",
            "/bill": "Group admin command to bill a user",
            "/groupinfo": "Group admin command to see all members info"
        }
        self._admin_commands = {
            "/groupadd": "Admin command to create a new group",
            "/grouprm": "Admin command to remove a group"
        }

    def clear_pending_user(self):
        self.pending_user = {
            "name": None,
            "phone": None,
            "group": None
        }

    # Error handling if user isn't known yet
    # Had to use the /start command and are therefore known to the bot
    def get_user(self, chat_id):
        try:
            return db.DBUser(chat_id)
        except db.UserNotExistError:
            raise UserNotExistError()

    def get_group(self, name):
        try:
            return db.Group(name)
        except db.GroupNotExistError:
            raise GroupNotExistError()

    def get_user_from_phone(self, phone):
        try:
            return db.DBUser.from_phone(phone)
        except db.UserNotExistError:
            raise UserNotExistError()

    def is_user_exists(self, chat_id):
        try:
            self.get_user(chat_id)
        except UserNotExistError:
            return False

        return True

    def create_group(self, name, admin):
        try:
            g = db.Group(name, create=True, admin=admin)
        except db.GroupAlreadyExistsError:
            raise GroupAlreadyExists()

    def add_user(self, chat_id, phone_number):
        try:
            db.DBUser(
                chat_id,
                phone=phone_number,
                create=True)
        except db.UserNotExistError:
            raise UserNotInvited()

    def add_user_by_phone(self, phone_number, name):
        try:
            db.DBUser.create_pending_user(phone_number, name)
        except db.UserAlreadyExistsError:
            raise UserAlreadyExistsError()

    def add_member(self, group_name, phone):
        group = db.Group(group_name)
        try:
            group.add_user_by_phone(phone)
        except db.UserAlreadyInGroupError:
            raise UserAlreadyExistsError()

    def remove_member(self, group_name, phone):
        group = db.Group(group_name)
        try:
            group.remove_user_by_phone(phone)
        except db.UserNotInGroupError:
            raise UserNotInGroupError()

    def get_admin_groups(self, chat_id):
        user = self.get_user(chat_id)
        admin_groups = []
        for group in user.groups():
            user_phone = user.data()['phone']
            group_admin_phone = group['admin']
            if user_phone == group_admin_phone:
                admin_groups.append(group['name'])

        return admin_groups

    def is_group_admin(self, chat_id, group_name):
        return group_name in self.get_admin_groups(chat_id)

    def get_help(self, chat_id):
        commands = self._commands.copy()

        try:
            user = self.get_user(chat_id)
            if self.get_admin_groups(chat_id):
                commands.update(self._group_admin_commands)

            if user.data()['admin']:
                commands.update(self._admin_commands)

        except UserNotExistError:
            pass

        return "\n".join(
            ["{}: {}".format(cmd, desc)
             for cmd, desc in commands.items()])

    def get_user_balances(self, chat_id):
        user = self.get_user(chat_id)
        groups = user.groups()

        balances = {}
        for group_name in groups:
            group = db.Group(group_name)
            balance = group.get_user_balance(chat_id)
            balances[group_name] = -balance

        return balances

    def get_all_users_balances(self, group_name):
        try:
            group = db.Group(group_name)
        except db.GroupNotExistError:
            raise GroupNotExistError

        balances = {}
        for user in group.get_users():
            name = user["name"]
            balance = 0
            if "id" in user:
                user_id = user["id"]
                balance = -group.get_user_balance(user_id)

            balances[name] = balance

        return balances

    def run(self):
        self.bot.enable_save_next_step_handlers(
            delay=self.SAVE_NEXT_STEP_DELAY)
        self.bot.load_next_step_handlers()
        self.bot.polling()
