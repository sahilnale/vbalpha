from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    @staticmethod
    def from_mongo(data):
        return User(username=data['username'], email=data['email'], password=data['password'])

    @staticmethod
    def get_by_username(username, mongo):
        user = mongo.db.users.find_one({'username': username})
        if user:
            return User.from_mongo(user)
        return None

    @staticmethod
    def get_by_id(user_id, mongo):
        user = mongo.db.users.find_one({'_id': user_id})
        if user:
            return User.from_mongo(user)
        return None

    def save_to_db(self, mongo):
        mongo.db.users.insert_one({'username': self.username, 'email': self.email, 'password': self.password})
