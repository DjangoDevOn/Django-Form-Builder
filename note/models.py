from django.db import models
from datetime import datetime
from django.conf import settings
# from django.urls import NoReverseMatch


class Contact(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="mycontact",  on_delete=models.CASCADE, null=True) # THIS IS FOR THE CURRENT LOGGED IN USER / TEAM LEAD
    contact_user_account = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="contactUserAccount",  on_delete=models.CASCADE, null=True) # THIS IS THE USER ACCOUNT THAT THE CONTACT OWNS / CAN LOG INTO AND SEE THE CONTENT / UPDATE THEIR EMAIL ADDRESS
    archived = models.BooleanField(default=False) # only team managers can see/archive contacts

    def __str__(self):
        return str(self.contact_user_account.first_name)


class Team(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="myteam",  on_delete=models.CASCADE, null=True) # THIS IS FOR THE CURRENT LOGGED IN USER / TEAM LEAD
    contacts = models.ManyToManyField(Contact, related_name="teamContacts")
    title = models.CharField(max_length=120)
    created = models.DateTimeField(auto_now_add=True)
    archived = models.BooleanField(default=False)

    def __str__(self):
        return str(self.title)


class Project(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="myproject",  on_delete=models.CASCADE, null=True) # THIS IS FOR THE CURRENT LOGGED IN USER / TEAM LEAD
    team = models.ForeignKey(Team, related_name="projectteam",  on_delete=models.CASCADE, null=True) # Team can have many projects, so a project gets a team
    title = models.CharField(max_length=120)
    created = models.DateTimeField(auto_now_add=True)
    archived = models.BooleanField(default=False)

    def __str__(self):
        return str(self.title)

class MeetingFormSettings(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="mymeetingformsettings",  on_delete=models.CASCADE, null=True) # THIS IS FOR THE CURRENT LOGGED IN USER / TEAM LEAD
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    title = models.CharField(max_length=120)
    meeting_time_goal = models.IntegerField(help_text="How many minutes should the meeting last?")
    sometimes_record = models.BooleanField(default=False)
    meeting_room_link = models.CharField(max_length=2000)
    scheduled_time = models.CharField(max_length=20) #meeting is supposed to start at:
    created = models.DateTimeField(auto_now_add=True)
    archived = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    # Call from template
    def entry_count(self):
        entry_ct = len(self.meetingformentry_set.all())
        return entry_ct

    def get_form_questions(self):
        questions = list(self.meetingformquestion_set.all())
        return questions

    class Meta:
        verbose_name_plural = 'Meeting Forms'


class MeetingFormEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="mymeetingformentry",  on_delete=models.CASCADE, null=True) # THIS IS FOR THE CURRENT LOGGED IN USER / TEAM LEAD
    form_settings = models.ForeignKey(MeetingFormSettings, on_delete=models.CASCADE)
    video_link = models.CharField(max_length=2000)
    meeting_time_realization = models.IntegerField(help_text="How many minutes did the meeting take?")
    participants = models.ManyToManyField(Contact, related_name="meetingParticipants")
    notify_user_list = models.ManyToManyField(Contact, related_name="meetingNotify")
    viewed_by_list = models.ManyToManyField(Contact, related_name="noteViewedBy")
    meeting_priority = models.CharField(max_length=20)
    created = models.DateTimeField(auto_now_add=True)
    archived = models.BooleanField(default=False)

    # Call from template
    @property
    def has_comments(self):
        return self.meetingformentrycomment_set.all()

    # Call from template
    @property
    def get_viewed_by_list(self):
        viewed_by = self.viewed_by_list.all()
        viewed_by_list = []
        for contact in viewed_by:
            viewed_by_list.append(contact)
        return viewed_by_list

    # Call from template
    @property
    def get_participants(self):
        participants = self.participants.all()
        participants_list = []
        for participant in participants:
            participants_list.append(participant)
        return participants_list

    # Call from template
    @property
    def get_notified(self):
        notified_list_all = self.notify_user_list.all()
        notified_list = []
        for notified in notified_list_all:
            notified_list.append(notified)
        return notified_list

    def __str__(self):
        return self.form_settings.title


class MeetingFormEntryComment(models.Model):    
    author = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="annotationAuthor",  on_delete=models.CASCADE, null=True) # THIS IS THE USER ACCOUNT THAT THE CONTACT OWNS / CAN LOG INTO AND SEE THE CONTENT / UPDATE THEIR EMAIL ADDRESS
    form_entry = models.ForeignKey(MeetingFormEntry, on_delete=models.CASCADE)
    comment = models.CharField(max_length=5000)
    created = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.author.first_name
        

class MeetingFormQuestion(models.Model): # Questions
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="mymeetingformquestion",  on_delete=models.CASCADE, null=True) # THIS IS FOR THE CURRENT LOGGED IN USER / TEAM LEAD
    question = models.CharField(max_length=1000)
    form_settings = models.ForeignKey(MeetingFormSettings, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.question)

    def get_responses(self):
        return self.meetingformanswer_set.all()



class MeetingFormAnswer(models.Model): # Answers: the user takes a note and answers the question from the form they made before
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="mymeetingformanswer",  on_delete=models.CASCADE, null=True) # THIS IS FOR THE CURRENT LOGGED IN USER / TEAM LEAD
    input_prompt = models.ForeignKey(MeetingFormQuestion(), on_delete=models.CASCADE)
    input_response = models.CharField(max_length=1200)

    def __str__(self):
        return self.input_response


 
class Alert(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="alertIsFor",  on_delete=models.CASCADE, null=True)
    read = models.BooleanField(default=False) 
    # optional (but will always be selected in the hard-coded create method) value to point to the new object that relates to a user (ex: comment, new note they were notified in)
    comment = models.ForeignKey(MeetingFormEntryComment, blank=True, on_delete=models.CASCADE, null=True) 
    note = models.ForeignKey(MeetingFormEntry, blank=True, on_delete=models.CASCADE, null=True) 
    contact = models.ForeignKey(Contact, blank=True, on_delete=models.CASCADE, null=True) # alert managers when new contact is created (someone signed up as team_user with)
    created = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return str(self.user.first_name)
