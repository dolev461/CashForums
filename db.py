import time
import pymongo
from config import config

# Example: +972521231234
PHONE_LENGTH = 13


dbclient = pymongo.MongoClient(config['MONGODB_URL'])
fdb = dbclient.forums


class GroupNotExistError(Exception):
    pass


class UserNotExistError(Exception):
    pass


class UserNameMissingError(Exception):
    pass


class PhoneMissingError(Exception):
    pass


class InvalidPhoneError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


class CreateUserNotAllowedError(Exception):
    pass


class UserNotInGroupError(Exception):
    pass


class UserAlreadyInGroupError(Exception):
    pass


class GroupAlreadyExistsError(Exception):
    pass


class DBUser(object):
    @staticmethod
    def all_users():
        users = [DBUser(x['id']) for x in fdb.users.find({}) if (x['id'])]
        return users

    @staticmethod
    def create_pending_user(phone, name):
        phone = DBUser.format_il_phone_number(phone)
        user = fdb.users.find_one({'phone': phone})
        if (user):
            raise UserAlreadyExistsError()

        fdb.users.insert_one({
            'phone': phone,
            'name': name,
            'admin': False,
        })

    @staticmethod
    def from_phone(phone):
        user = fdb.users.find_one(
            {'phone': DBUser.format_il_phone_number(phone)})

        if not user:
            raise UserNotExistError()

        return user

    @staticmethod
    def format_il_phone_number(phone):
        phone = phone.replace("-", "")

        if phone.startswith('972'):
            phone = '+{}'.format(phone)
        elif phone.startswith('0'):
            phone = '+972{}'.format(phone.lstrip('0'))

        if not phone.startswith('+972'):
            phone = '+972{}'.format(phone)

        if len(phone) != PHONE_LENGTH:
            raise InvalidPhoneError()

        if not phone.replace("+", "").isdigit():
            raise InvalidPhoneError()

        return phone

    def __init__(self, id, create=False, phone=None):
        self._id = id
        self._selector = {'id': id}

        if create:
            self._initialize_pending_user(
                id,
                DBUser.format_il_phone_number(phone))
        if not self.exists():
            raise UserNotExistError()

    def _initialize_pending_user(self, id, phone):
        if not phone:
            raise PhoneMissingError()

        phone = DBUser.format_il_phone_number(phone)
        user = fdb.users.find_one({'phone': phone})
        if not user:
            raise UserNotExistError()

        if 'id' in user:
            raise UserAlreadyExistsError()

        fdb.users.update({'phone': phone}, {'$set': {
            'id': self._id,
        }})

    def delete(self):
        fdb.users.delete_one(self._selector)

    def exists(self):
        user = fdb.users.find_one(self._selector)
        if user:
            return True
        return False

    def data(self):
        user = fdb.users.find_one(self._selector)
        if not user:
            raise UserNotExistError()
        return user

    def groups(self):
        phone = DBUser.format_il_phone_number(self.data()['phone'])
        results = fdb.groups.find({'users': {'$all': [phone]}})
        return [x for x in results]


class Group(object):
    @staticmethod
    def all_groups():
        groups = [Group(x['name']) for x in fdb.groups.find({})]
        return groups

    def __init__(self, name, create=False, admin=None):
        self._name = name
        self._admin = admin
        self._selector = {'name': self._name}

        if create:
            self._create_group()
        if not self.exists():
            raise GroupNotExistError()

    def _create_group(self):
        group = fdb.groups.find_one(self._selector)
        if group:
            raise GroupAlreadyExistsError()
        fdb.groups.insert_one({
            'name': self._name,
            'users': [],
            'admin': self._admin,
        })
        return group

    def exists(self):
        group = fdb.groups.find_one(self._selector)
        if not group:
            return False
        return True

    def data(self):
        group = fdb.groups.find_one(self._selector)
        if not group:
            raise GroupNotExistError()
        return group

    def add_user(self, id):
        user = DBUser(id)
        phone = DBUser.format_il_phone_number(user.data()['phone'])
        self.add_user_by_phone(phone)

    def add_user_by_phone(self, phone):
        phone = DBUser.format_il_phone_number(phone)
        if self.has_user(phone):
            raise UserAlreadyInGroupError('Cannot add the same user twice.')

        fdb.groups.update(self._selector, {'$push': {'users': phone}})

    def remove_user(self, id):
        user = DBUser(id)
        phone = user.data()['phone']
        self.remove_user_by_phone(phone)

    def remove_user_by_phone(self, phone):
        phone = DBUser.format_il_phone_number(phone)
        if not self.has_user(phone):
            raise UserNotInGroupError()

        fdb.groups.update(self._selector, {'$pull': {'users': phone}})

    def has_user(self, phone):
        return DBUser.format_il_phone_number(phone) in self.data()['users']

    def get_users(self):
        return [DBUser.from_phone(phone) for phone in self.data()['users']]

    def bill_user(self, id, amount):
        user = DBUser(id)
        phone = user.data()['phone']

        if not self.has_user(phone):
            raise UserNotInGroupError()

        fdb.bills.insert_one({
            'user': id,
            'group': self._name,
            'amount': amount,
            'time': time.time()
        })

    def get_user_bill_history(self, id):
        return [x for x in fdb.bills.find({'user': id, 'group': self._name})]

    def get_user_balance(self, id):
        return sum([b['amount'] for b in self.get_user_bill_history(id)])
