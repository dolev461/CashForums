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

class DBUser(object):
    def __init__(self, phone, create=False, name=None):
        self._phone = phone
        self._selector = {'phone': self._phone}

        if create:
            self._create_user(name)
        self.data() # validate existence

    @staticmethod
    def exists(**args):
        user = fdb.users.find_one(args)
        return user

    def _create_user(self, name):
        if not name:
            raise UserNameMissingError()
        user = fdb.users.find_one(self._selector)
        if not user:
            fdb.users.insert_one({
                'name': name,
                'phone': self._phone,
                'admin': False,
            })
        return user

    def data(self):
        user = fdb.users.find_one(self._selector)
        if not user:
            raise UserNotExistError()
        return user

    def add_to_group(self, group):
        group = fdb.groups.find_one({'name': group})
        if not group:
            raise GroupNotExistError()
        
        fdb.groups.update({'name': group}, {'$push': {'users': self._phone}})

class Group(object):
    def __init__(self, name, create=False, admin=None):
        self._name = name
        self._admin = admin
        self._selector = {'name': self._name}

        if create:
            self._create_group()
        self.data() # A way to validate existence

    def _create_group(self): 
        group = fdb.groups.find_one(self._selector)
        if not group:
            fdb.groups.insert_one({
                'name': self._name,
                'users': [],
                'admin': self._admin,
            })
        return group
    
    def data(self):
        group = fdb.groups.find_one(self._selector)
        if not group:
            raise GroupNotExistError()
        return group
    
    def add_user(self, phone, create=False, name=None):
        user = DBUser(phone, create, name)

        if not self.has_user(phone):
            fdb.groups.update(self._selector, {'$push': {'users': phone}})
    
    def remove_user(self, phone):
        user = DBUser(phone)

        if self.has_user(phone):
            fdb.groups.update(self._selector, {'$pull': {'users': phone}})
    
    def has_user(self, phone):
        return phone in self.data()['users']

    def get_users(self):
        return [DBUser(phone) for phone in self.data()['users']]

