from flexbot.user import User

class TestUser(object):
    def test_init(self):
        u = User('id', 'un', 'fn', 'ln')
        assert u.id == 'id'
        assert u.username == 'un'
        assert u.firstname == 'fn'
        assert u.lastname == 'ln'

    def test_get_mention(self):
        u = User('id', 'un', 'fn', 'ln')
        assert u.get_mention() == '<@un>'
