import telebot
import config
import db
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


class UserAlreadyExistsError(Exception):
    pass


class UserAlreadyInGroupError(Exception):
    pass


class UserNotInGroupError(Exception):
    pass


class UserNotExistError(Exception):
    pass


class UserNotInvitedError(Exception):
    pass


class GroupAlreadyExistsError(Exception):
    pass


class GroupNotExistError(Exception):
    pass


class InvalidPhoneError(Exception):
    pass


class InvalidAmountError(Exception):
    pass


class BotManager(object):
    SAVE_NEXT_STEP_DELAY = 2  # Seconds
    CB_INFO = "cmd_info_"
    CB_ADD = "cmd_add_"
    CB_REMOVE = "cmd_remove_"
    CB_DISABLE = "cmd_disable_"
    CB_INFO = "cmd_info_"
    CB_BILL = "cmd_bill_"
    CB_REFUND = "cmd_refund_"
    CB_GROUP_INFO = "cmd_group_info_"
    CB_GROUP_ADD = "cmd_group_add_"
    CB_GROUP_RM = "cmd_group_RM_"

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
        # "/start": "Start - Register your telegram account to the bot",
        # "/help": "Help - Show this help section",
        self._commands = {
            InlineKeyboardButton(
                "ℹ מידע",
                callback_data=self.CB_INFO
            ): "Info - Get your balance in your associated groups",
        }
        self._group_admin_commands = {
            InlineKeyboardButton(
                "➕ הוספת חבר\ת קבוצה",
                callback_data=self.CB_ADD
            ): "Add - Group admin command to add members",
            InlineKeyboardButton(
                "➖ הסרת חבר\ת קבוצה",
                callback_data=self.CB_REMOVE
            ): "Rm - Group admin command to remove members",
            InlineKeyboardButton(
                "❄ הקפאה\החזר חבר\ת קבוצה",
                callback_data=self.CB_DISABLE
            ): "Rm - Group admin command to disable members",
            InlineKeyboardButton(
                "⁉ מידע על הקבוצה",
                callback_data=self.CB_GROUP_INFO
            ): "Group admin command to display all group members info",
            InlineKeyboardButton(
                "💸 חיוב",
                callback_data=self.CB_BILL
            ): "Group admin command to bill a user",
            InlineKeyboardButton(
                "🙇‍♂️ זיכוי כספי",
                callback_data=self.CB_REFUND
            ): "Group admin command to refund a user",
        }
        self._admin_commands = {
            InlineKeyboardButton(
                "⭕ הוספת קבוצה",
                callback_data=self.CB_GROUP_ADD
            ): "Admin command to create a new group",
            InlineKeyboardButton(
                "❌ הסרת קבוצה",
                callback_data=self.CB_GROUP_RM
            ): "Admin command to remove a group"
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
        except db.InvalidPhoneError:
            raise InvalidPhoneError()

    def is_user_exists(self, chat_id):
        try:
            self.get_user(chat_id)
        except UserNotExistError:
            return False

        return True

    def create_group(self, name, admin):
        try:
            db.Group(name, create=True, admin=admin)
        except db.GroupAlreadyExistsError:
            raise GroupAlreadyExistsError()

    def add_user(self, chat_id, phone_number):
        try:
            db.DBUser(
                chat_id,
                phone=phone_number,
                create=True)
        except db.UserNotExistError:
            raise UserNotInvitedError()
        except db.InvalidPhoneError:
            raise InvalidPhoneError()

    def add_user_by_phone(self, phone_number, name):
        try:
            db.DBUser.create_pending_user(phone_number, name)
        except db.UserAlreadyExistsError:
            raise UserAlreadyExistsError()
        except db.InvalidPhoneError:
            raise InvalidPhoneError()

    def add_member(self, group_name, phone):
        group = self.get_group(group_name)

        try:
            group.add_user_by_phone(phone)
        except db.UserAlreadyInGroupError:
            raise UserAlreadyExistsError()
        except db.InvalidPhoneError:
            raise InvalidPhoneError()

    def remove_member(self, group_name, phone):
        group = self.get_group(group_name)

        try:
            group.remove_user_by_phone(phone)
        except db.UserNotInGroupError:
            raise UserNotInGroupError()
        except db.InvalidPhoneError:
            raise InvalidPhoneError()

    def toggle_disable_member(self, group_name, phone):
        group = self.get_group(group_name)
        data = group.data()

        try:
            if 'disabled' in data and phone in data['disabled']:
                group.active_user_by_phone(phone)
            else:
                group.disable_user_by_phone(phone)
        except db.UserNotInGroupError:
            raise UserNotInGroupError()
        except db.InvalidPhoneError:
            raise InvalidPhoneError()

    def bill_member(self, group_name, phone, amount):
        group = self.get_group(group_name)

        try:
            group.bill_user_by_phone(phone, int(amount))
        except db.UserNotInGroupError:
            raise UserNotInGroupError()
        except db.InvalidPhoneError:
            raise InvalidPhoneError()
        except ValueError:
            raise InvalidAmountError()

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
        markup = InlineKeyboardMarkup(row_width=1)
        commands = self._commands.copy()

        try:
            user = self.get_user(chat_id)
            if self.get_admin_groups(chat_id):
                commands.update(self._group_admin_commands)

            if user.data()['admin']:
                commands.update(self._admin_commands)

        except UserNotExistError:
            pass

        markup.add(*commands)

        return markup

    def get_disabled_users(self, group_name):
        return self.get_group(group_name).get_disabled_users()

    def get_user_balances(self, chat_id):
        user = self.get_user(chat_id)
        groups = user.groups()

        balances = {}
        for group_dict in groups:
            group_name = group_dict["name"]
            group = db.Group(group_name)
            balance = group.get_user_balance(chat_id)
            balances[group_name] = -balance

        return balances

    def get_all_users_balances(self, group_name):
        group = self.get_group(group_name)

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

        self.bot.remove_webhook()
        self.bot.set_webhook(
            "https://cash-forum.herokuapp.com/" + config.config["API_TOKEN"])
        self.bot.polling()
