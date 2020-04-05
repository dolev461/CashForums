MALE = u'זכר'
FEMALE = u'נקבה'


class User:
    def __init__(self, name):
        self._name = name
        self._mador = None
        self._sex = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def mador(self):
        return self._mador

    @mador.setter
    def mador(self, value):
        self._mador = value

    @property
    def sex(self):
        return self._sex

    @sex.setter
    def sex(self, value):
        self._sex = value
