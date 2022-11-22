import uuid
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
# Auth/User
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin


################################### CUSTOM USER MODEL ###################################
class CustomUserManager(BaseUserManager):
    
    def create_user(self, email, first_name, last_name, profile_photo, password=None,):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
            profile_photo=profile_photo,
            email_confirmed = models.BooleanField(default=False),
        )

        user.set_password(password)
        # Toggle if: superuser create broke from this stuff
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        # endToggle if: superuser broke
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        user = self.create_user(
            email,
            password=password,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
    

class User(AbstractUser, PermissionsMixin):
    updated = models.DateTimeField(auto_now=True) # Be sure to update this when they save profile settings
    created = models.DateTimeField(auto_now_add=True)
    profile_photo = models.ImageField(default='default.jpg')
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    email = models.EmailField(max_length=254, unique=True)
    email_confirmed = models.BooleanField(default=False)
    password = models.CharField(max_length=200)
    dark_mode = models.BooleanField(default=False)
    receive_email_notifications = models.BooleanField(default=True)
    team_user = models.BooleanField(default=True) # toggle to false when makes manager link
    manager_id = models.CharField(max_length=200, blank=True) # Redundant if team_user=True, but that's okay
    # when manager creates shareable link, they get a code to replace 'manager' here
    # when someone/team member signs up using that link, the default 'manager' will be replaced with that code
    # on signup, default to a manager account, (team_user=False)
    # that manager gets a signup link with their manager_id at the end
    # CSS in signup will make the manager_id field invisible
    # JS will grab the manager_id code from the url and add it to the .value of the field 
    # JS will use a default code if there is no code in url (manager account)
    # Sign up view will check for default code, if it gets default code:
    # keep team_user as false, if it gets a manager_id code, lookup a user with that code
    # create a contact object, with that user as the "user" and the newly created user
    # as the contact_user_account
    # JS in base.py hides all links and adds the right ones for the team_user,
    # And, JS hides the top two cards / top row of the dashboard + the signup link


    @property
    def imageURL(self):
        try:
            url = self.profile_photo.url
        except:
            url = ''
        return url

    def __str__(self):
        return self.user.username
    
    
    username = None
    
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['password']
    
    objects = CustomUserManager()
    
    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

 



################################## FEEDBACK ###################################



class Feedback(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="feedbackSender",  on_delete=models.CASCADE, null=True)
    feedback_type = models.CharField(max_length=20, null=True, blank=True)
    # for "Noticed a Bug" these are dynamic fields (optional)
    video_url = models.CharField(max_length=300, null=True, blank=True)
    screenshot_url = models.CharField(max_length=300, null=True, blank=True)
    issue_page_url = models.CharField(max_length=200, null=True, blank=True)
    # end "Noticed a Bug" 
    feedback_content = models.CharField(max_length=5000, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sender.first_name




################################### FAQ ###################################
class FaqCat(models.Model):
    cat_title = models.CharField(max_length=200, null=True)
    def __str__(self):
        return self.cat_title


class Faq(models.Model):
    category = models.ForeignKey(FaqCat, on_delete=models.CASCADE)
    question = models.CharField(max_length=100)
    answer = models.CharField(max_length=1000)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question




