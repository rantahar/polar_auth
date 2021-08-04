import os
from django.test import TestCase
from django.core import mail
from users.models import User, Subscriber
import users.forms as forms

# TestCases for the user model
class UserTestCase(TestCase):
    def setUp(self):
        # create 2 users
        User.objects.create_user("user1@aalto.fi", password="a", is_admin=False, is_staff=False, is_active=True)
        User.objects.create_user("user2@aalto.fi", password="b", is_admin=False, is_staff=False, is_active=True)

        # create a subscriber
        Subscriber.objects.create(email="user1@aalto.fi")


class UserModelTestCase(UserTestCase):
    def test_user_creation(self):
        user1 = User.objects.get(email="user1@aalto.fi")
        user2 = User.objects.get(email="user2@aalto.fi")

        # Check the email
        self.assertEqual(user1.email, "user1@aalto.fi")

        # The consent, privacy, authorized and first survey fields should
        # be set to false
        self.assertFalse(user1.consent)
        self.assertFalse(user1.privacy)
        self.assertFalse(user1.first_survey_done)

        # Received data, received email and device sent are also False
        self.assertFalse(user1.has_received_email)
        self.assertFalse(user1.device_sent)
        self.assertFalse(user1.received_data)

        # Each user should have an ID
        self.assertNotEqual(user1.user_id, user2.user_id)

        # No username, first name or last name fields
        self.assertIsNone(user1.username)
        self.assertIsNone(user1.first_name)
        self.assertIsNone(user1.last_name)

        # Polar_id is None
        self.assertIsNone(user1.polar_id)

        # The user is not ready to authorize
        self.assertFalse(user1.ready_to_authorize())

        # Finally, __str__ returns the email
        self.assertEqual(str(user1), user1.email)

    def test_usbscriber_creation(self):
        subsriber1 = User.objects.get(email="user1@aalto.fi")

        # Check the email
        self.assertEqual(subsriber1.email, "user1@aalto.fi")

        # Received data, received email and device sent are also False
        self.assertFalse(subsriber1.has_received_email)

        # __str__ returns the email
        self.assertEqual(str(subsriber1), subsriber1.email)


class UserRegisterFormTestCase(UserTestCase):
    def setUp(self):
        super().setUp()

        # Correct data for the form
        self.data = {
            "email": "user3@aalto.fi",
            "has_own_device": True,
            "full_time": True,
            "do_not_foresee_changing_employer": True,
            "will_return_tracker": True,
            "password1": "1Xx7*4&ZFNNM",
            "password2": "1Xx7*4&ZFNNM",
        }

    def check_error_with_field_false(self, field_name):
        ''' Check that a form fails when given field is false '''
        # Fill in the data and create initialize form
        self.data[field_name] = False
        form = forms.UserRegisterForm(data=self.data)

        # Check that the form is not valid
        self.assertFalse(form.is_valid())
        self.assertIn(field_name, form.errors.keys())

    def test_with_own_device(self):
        ''' Check with valid data. '''
        # Fill in the data and create initialize form
        form = forms.UserRegisterForm(data=self.data)

        # Check that the form is valid
        self.assertTrue(form.is_valid())

        # Check that saving the form adds to the database
        form.save()
        user = User.objects.get(email="user3@aalto.fi")
        self.assertEqual(user.email, "user3@aalto.fi")

    def test_with_no_device(self):
        ''' Should fail if the user does not have a device '''
        # Fill in the data and create initialize form
        self.data["has_own_device"] = False
        form = forms.UserRegisterForm(data=self.data)

        # Check that the form is not valid
        self.assertFalse(form.is_valid())
        self.assertTrue(len(form.non_field_errors()) > 0)

    def test_without_full_time(self):
        ''' Should fail if the user is not full time '''
        self.check_error_with_field_false("full_time")

    def test_foresee_changing_jobs(self):
        ''' should fail if the user expect to change jobs '''
        self.check_error_with_field_false("do_not_foresee_changing_employer")

    def test_will_return_tracker(self):
        ''' should fail if the user does not promise to return the tracker '''
        self.check_error_with_field_false("will_return_tracker")

    def test_with_no_email(self):
        ''' Fail if email is not provided '''
        # Fill in the data and create initialize form
        self.data["email"] = ""
        form = forms.UserRegisterForm(data=self.data)

        # Check that the form is not valid
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors.keys())

    def test_with_non_aalto_email(self):
        ''' Fail if the email is not under Aalto domain. '''
        # Fill in the data and create initialize form
        self.data["email"] = "user@example.com"
        form = forms.UserRegisterForm(data=self.data)

        # Check that the form is not valid
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors.keys())


class UserPrivacyFormTestCase(UserTestCase):
    def setUp(self):
        super().setUp()

        # Correct data for the form
        self.data = {"privacy": True}

    def test_without_agreement(self):
        ''' Should fail the user does not agree '''
        # Fill in the data and create initialize form
        self.data['privacy'] = False
        form = forms.PrivacyForm(data=self.data)
        form.instance = User.objects.get(email="user1@aalto.fi")

        # Check that the form is valid
        self.assertFalse(form.is_valid())
        self.assertIn('privacy', form.errors.keys())

    def validate_and_save_form(self, user):
        ''' Validate and save with valid data. '''
        # Fill in the data and create initialize form
        form = forms.PrivacyForm(data=self.data)
        form.instance = user

        # Check that the form is valid
        self.assertTrue(form.is_valid())

        # Check that saving the form adds to the database
        form.save()
        user = User.objects.get(email=user.email)
        self.assertTrue(user.privacy)

    def test_no_consent(self):
        ''' User has not consented -> no email '''
        user = User.objects.get(email="user1@aalto.fi")
        for consent, survey in [(False, False), (True, False), (False, True)]:
            user.consent = consent
            user.first_survey_done = survey
            user.save()
            self.validate_and_save_form(user)

            # Check that no email has been sent
            self.assertEqual(len(mail.outbox), 0)

    def test_with_survey_and_consent(self):
        ''' User has consented and filled the survey -> send email '''
        user = User.objects.get(email="user1@aalto.fi")
        user.consent = True
        user.first_survey_done = True
        user.save()
        self.validate_and_save_form(user)

        # Check that the email has been sent
        self.assertEqual(len(mail.outbox), 1)


class UserConsentFormTestCase(UserTestCase):
    def setUp(self):
        super().setUp()

        # Correct data for the form
        self.data = {
            "field_1": True,
            "field_2": True,
            "field_3": True,
            "field_4": True,
            "field_5": True,
            "field_6": True,
        }

    def test_with_missing_field(self):
        ''' Should fail the user does not agree to all points '''
        # Fill in the data and create initialize form
        for i in range(1, 7):
            field_name = f"field_{i}"
            self.data[field_name] = False
            form = forms.ConsentForm(data=self.data)
            form.instance = User.objects.get(email="user1@aalto.fi")

            # Check that the form is valid
            self.assertFalse(form.is_valid())
            self.assertIn(field_name, form.errors.keys())

    def validate_and_save_form(self, user):
        ''' Validate and save with valid data. '''
        # Fill in the data and create initialize form
        form = forms.ConsentForm(data=self.data)
        form.instance = user

        # Check that the form is valid
        self.assertTrue(form.is_valid())

        # Check that saving the form adds to the database
        form.save()
        user = User.objects.get(email=user.email)
        self.assertTrue(user.consent)

    def test_no_privacy_or_survey(self):
        ''' User has filled the privacy form -> no email '''
        user = User.objects.get(email="user1@aalto.fi")
        for privacy, survey in [(False, False), (True, False), (False, True)]:
            user.privacy = privacy
            user.first_survey_done = survey
            user.save()
            self.validate_and_save_form(user)

            # Check that no email has been sent
            self.assertEqual(len(mail.outbox), 0)

    def test_with_survey_and_privacy(self):
        ''' User has filled the privacy form and the survey -> send email '''
        user = User.objects.get(email="user1@aalto.fi")
        user.privacy = True
        user.first_survey_done = True
        user.save()
        self.validate_and_save_form(user)

        # Check that the email has been sent
        self.assertEqual(len(mail.outbox), 1)



