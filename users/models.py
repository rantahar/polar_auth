import uuid

from django.db import models
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.utils.safestring import mark_safe

from survey.models.survey import Survey


# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, is_admin=False, is_staff=False, is_active=True):
        if not email:
            raise ValueError("User email missing")
        if not password:
            raise ValueError("User pasword missing")

        user = self.model(
            email=self.normalize_email(email)
        )
        user.set_password(password)
        user.admin = is_admin
        user.staff = is_staff
        user.active = is_active
        user.is_superuser = is_admin

        # Consent always starts as False
        user.consent = False

        # Create a subject id
        user.user_id = int(uuid.uuid1().int>>96)

        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("User email missing")
        if not password:
            raise ValueError("User password missing")

        user = self.model(
            email=self.normalize_email(email)
        )
        user.set_password(password)
        user.admin = True
        user.is_staff = True
        user.active = True
        user.is_superuser = True
        user.consent = False

        # Create a user id
        user.user_id = int(uuid.uuid1().int>>96)

        user.save()
        return user


class User(AbstractUser):
    # Remove the username as a separate field (we use email)
    username = None

    # Require email to be unique
    email = models.EmailField('email address', unique=True,
                              help_text="Email (aalto.fi only)")

    # Set email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # Also remove the name
    first_name = None
    last_name = None

    # We do need an address to send the device to
    home_address = models.CharField(
                'home address', max_length=50, blank=True,
                help_text=mark_safe(
                  """<ul>
                  <li>Address for receiving the Polar fitness tracker. It can be any address within Finland where you would like to receive the fitness tracker. (Don't fill if you already have one.)</li>
                  <li>The size of the fitness tracker is M/L, which means wrist circumference 155–210 mm.</li>
                  </ul>"""
                )
              )

    # Whether the user already has a Polar Ignite. If so, we don't need to send
    # one
    has_own_device = models.BooleanField(
            "I already have a Polar fitness tracker", default=False,
            help_text=mark_safe(
              "<ul><li>We have run out of fitness trackers, please only register if you have a Polar fitness tracker of your own.</li></ul>"
            )
        )

    # Device address
    size_choices = (
        ('S', "S: wrist circumference 130–185 mm"),
        ('M/L', "M/L: wrist circumference 155–210 mm"),
    )

    size = models.CharField(
        'Fitness tracker size',
        max_length=20, choices=size_choices,
        help_text=mark_safe(
          "<ul><li>Size of the fitness tracker we send you.</li></ul>"
        ),
        blank=True
    )

    # Track the three steps that the user needs to complete before they have
    # signed up to the study.
    consent = models.BooleanField('Consented to study', default=False)
    privacy = models.BooleanField('Agreed to privacy notice', default=False)
    first_survey_done = models.BooleanField('Filled first survey', default=False)

    # True if the user has given authorization (and not removed it)
    authorized = models.BooleanField('Authorized access', default=False)

    # We use the polar_id to identify the user to the data server.
    # This could, in principle, be identify the user, but we already
    # store the email here in any case.
    polar_id = models.CharField(max_length=20, null=True, blank=True)

    # Before we have access to the polar_id, we need a user ID for the survey
    user_id = models.CharField('ID', max_length=32, blank=True)

    # This becomes True when an email is sent to this user in the admin
    # interface
    has_received_email = models.BooleanField('Has received email', default=False)

    # Checked manually by an admin when the device has been posted or delivered
    device_sent = models.BooleanField('Fitness tracker sent', default=False)

    # Checked manually by an admin when a user has dropped out of the study
    dropped_out = models.BooleanField('Dropped out', default=False)

    # For checking if we are receiving data from the user
    received_data = models.BooleanField('Received data', default=False)

    # The latest date data has been received
    data_received_date = models.DateField('Data received', null=True, default=None)

    # Link to surveys the user has filled (without linking to the answers)
    filled_surveys = models.ManyToManyField(Survey, blank=True)

    # Set the user manager
    objects = UserManager()

    def ready_to_authorize(self):
        ''' Check if a user is ready to authorize data collection '''
        return self.privacy and self.consent and self.first_survey_done

    def __str__(self):
        return self.email


class Subscriber(models.Model):
    ''' This model only contains an email. Added emails are
    expressions of interest, not actual registrations.'''
    email = models.EmailField(unique=True, help_text="Email (aalto.fi only)")

    user_id = models.CharField('ID', max_length=32, blank=True)
    has_received_email = models.BooleanField('Has received email', default=False)

    def __str__(self):
        return self.email
