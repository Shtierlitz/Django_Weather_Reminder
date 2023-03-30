from django.test import TestCase

from weatherreminder.forms import RegisterUserForm, LoginUserForm, ChangeProfileForm
from weatherreminder.models import User


class TestForms(TestCase):
    def test_register_form(self):
        form = RegisterUserForm(data={
            'username': 'form_test_username',
            'email': 'form_test_@mail.com',
            'password1': 'test_password_000',
            'password2': 'test_password_000'
        })
        self.assertTrue(form.is_valid())

    def test_register_form_fail(self):
        form = RegisterUserForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 4)

    def test_RegisterForm_clean_fields(self):
        form = RegisterUserForm(data={
            'username': 'u' * 151,
            'email': "test_email",
            'password1': '1234_test_true',
            'password2': '1234_test_false'
        })
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 3)

    def test_login_form(self):
        User.objects.create_user(username='form_test_username', password='test_password_000', email='test_form_@mail.com')
        form = LoginUserForm(data={
            'username': 'form_test_username',
            'password': 'test_password_000',
        })
        self.assertTrue(form.is_valid())

    def test_LoginForm_no_data(self):
        form = LoginUserForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 2)

    def test_LoginForm_clean_passwords(self):
        form = LoginUserForm(data={
            'password': '1234'  # to short
        })
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 1)

    def test_ChangeProfileForm(self):
        form = ChangeProfileForm(data={
            'username': 'test_username',
            'email': 'test_email@mail.com'
        })
        self.assertTrue(form.is_valid())

    def test_test_ChangeProfileForm_no_data(self):
        form = ChangeProfileForm({})
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 2)

    def test_test_ChangeProfileForm_clean_data(self):
        form = ChangeProfileForm(data={'username': 'test_username', 'email': '1234'})
        self.assertFalse(form.is_valid())
        self.assertEquals(len(form.errors), 1)

