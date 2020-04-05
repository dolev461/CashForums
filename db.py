import pymongo
from config import config

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

class UserAlreadyExists(Exception):
    pass

class CreateUserNotAllowed(Exception):
    pass

class DBUser(object):
    @staticmethod
    def create_pending_user(phone, name):
        user = fdb.users.find_one({'phone': phone})
        if (user):
            raise UserAlreadyExists()

        fdb.users.insert_one({
            'phone': phone,
            'name': name,
            'admin': False,
        })

    @staticmethod
    def from_phone(phone):
        user = fdb.users.find_one({'phone': phone})
        return user 

    def __init__(self, id, create=False, phone=None):
        self._id = id
        self._selector = {'id': id}

        if create:
            self._initialize_pending_user(id, phone)
        if not self.exists():
            raise UserNotExistError()

    def _initialize_pending_user(self, id, phone):
        if not phone:
            raise PhoneMissingError()

        user = fdb.users.find_one({'phone': phone})
        if not user:
            raise UserNotExistError()

        fdb.users.update({'phone': phone}, {
            'id': self._id,
        })

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

class Group(object):
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
        if not group:
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
        phone = user.data()['phone']
        self.add_user_by_phone(phone)
    
    def add_user_by_phone(self, phone):
        if not self.has_user(phone):
            fdb.groups.update(self._selector, {'$push': {'users': phone}})
    
    def remove_user(self, id):
        user = DBUser(id)
        phone = user.data()['phone']

        if self.has_user(phone):
            fdb.groups.update(self._selector, {'$pull': {'users': phone}})
    
    def has_user(self, id):
        user = DBUser(id)
        phone = user.data()['phone']

        return phone in self.data()['users']

    def get_users(self):
        return [DBUser.from_phone(phone) for phone in self.data()['users']]

