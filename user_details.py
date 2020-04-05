MALE = u'זכר'
FEMALE = u'נקבה'
UNKNOWN = 0

PLUS_MESSAGES = {
    MALE: "אתה יכול להיות רגוע יש לך עודף של {}",
    FEMALE: "את ממש בסדר... יש לך עודף של {}"
}

MINUS_MESSAGES = {
    MALE: "אחי אתה חייב {} שקלים לקופה",
    FEMALE: "אחותי את חייבת {} שקלים לקופה"
}

NEUTRAL_MESSAGE = "הכל טוב והמאזן מושלם"


class User:
    def __init__(self, phone_number):
        self._phone_number = phone_number
        self._name = "Rand"
        self._group = None
        self._sex = MALE  # default
        self._value = 0
        self._is_admin = False

    def __str__(self):
        return (
            "טלפון: {}".format(self._phone_number)
        )

    @property
    def phone_number(self):
        return self._phone_number

    @phone_number.setter
    def phone_number(self, value):
        self._phone_number = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def group(self):
        return self._group

    @group.setter
    def group(self, value):
        self._group = value

    @property
    def sex(self):
        return self._sex

    @sex.setter
    def sex(self, value):
        self._sex = value

    def get_value_status(self):
        if self._value > 0:
            return PLUS_MESSAGES[self.sex]

        if self._value < 0:
            return MINUS_MESSAGES[self.sex]

        return NEUTRAL_MESSAGE
