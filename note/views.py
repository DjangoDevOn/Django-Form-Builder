from django.contrib.auth import get_user_model
User = get_user_model()
from datetime import datetime, date
from django.http import JsonResponse
import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import *
# from django.db.models import Count, Q
from django.template import loader
from django.template.loader import render_to_string
from django.core.mail import send_mail
import re
from django.http import HttpResponseRedirect
from django.views.generic import UpdateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy


@login_required(login_url='login')
def dashboard(request):
    recent_notes = MeetingFormEntry.objects.filter(user=request.user).order_by('-id')[:20]  # limit to 20
    # get manager_id - if still set to default create a 
    # boolean and sent to template for check to show button or link
    current_user = get_user_model().objects.get(id=request.user.id)
    if current_user.manager_id == '':
        made_share_url = False
    else:
        made_share_url = True # second check in template see dashboard.html
    context = {
        'made_share_url':made_share_url,
        'recent_notes':recent_notes,
    }
    return render(request, 'note/dashboard.html', context)

def new_share_url(request):
    # this will permanently make this user "team_user" = False and the rest will default to True automatically (see models.py)
    current_user = get_user_model().objects.get(id=request.user.id)
    current_user.team_user = False

    import random, string
    def randomword(length):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(length))
        
    rand_num = randomword(12) # GEN RAND NUM 
    current_user.manager_id = rand_num
    current_user.save()
    return redirect('dashboard')

# forms

# New Form:
# AJAX GET For select form to create note -> returns users forms, 
# if none - show user create form button -> if some, select to link to new note page
def get_user_forms_data(request): 
    user_forms = MeetingFormSettings.objects.filter(user=request.user).order_by('-id')

    data = []
    for obj in user_forms:
        item = {
            'id': obj.id,
            'title': obj.title,
        } 
        data.append(item)
    return JsonResponse({'data':data})
    
     
@login_required(login_url='login')
def forms(request):
    forms = MeetingFormSettings.objects.filter(user=request.user).order_by('-id')
    forms = forms.filter(archived=False)
    context = {
        'forms':forms,
    }
    return render(request, 'note/forms/forms.html', context)
 
@login_required(login_url='login')
def archived_forms(request):
    forms = MeetingFormSettings.objects.filter(user=request.user).order_by('-id')
    forms = forms.filter(archived=True)
    return render(request, 'note/forms/archived-forms.html', {'forms':forms,})

@login_required(login_url='login')
def archive_form(request, pk):
    form = MeetingFormSettings.objects.get(id=pk)
    form.archived = True
    form.save()
    # get all forms to redirect to "forms"
    forms = MeetingFormSettings.objects.filter(user=request.user).order_by('-id')
    forms = forms.filter(archived=True)
    alert = 'You archived a Form!'
    return render(request, 'note/forms/archived-forms.html', {'alert':alert,'forms':forms,})

@login_required(login_url='login')
def revive_form(request, pk):
    form = MeetingFormSettings.objects.get(id=pk)
    form.archived = False
    form.save()
    # get all forms to redirect to "forms"
    forms = MeetingFormSettings.objects.filter(user=request.user).order_by('-id')
    forms = forms.filter(archived=False)
    alert = 'You revived a Form!'
    return render(request, 'note/forms/forms.html', {'alert':alert,'forms':forms,})

@login_required(login_url='login')
def form_details(request, pk):
    form_settings = MeetingFormSettings.objects.get(id=pk) 
    # Calculate time goal success rate (SAME AS BELOW: ToDo - MAKE HELPER FUNC)
    time_goal = form_settings.meeting_time_goal
    my_entries = MeetingFormEntry.objects.filter(user=request.user).order_by('-id')
    my_entries_with_settings_to_this = my_entries.filter(form_settings=form_settings).order_by('-id') # get all my MeetingFormEntry objects that point to this MeetingFormSettings we're submiting a form for
    entries_length = len(my_entries_with_settings_to_this)
    meeting_time_realization_sum = 0
    for entry in my_entries_with_settings_to_this:
        meeting_time_realization_sum += entry.meeting_time_realization
    time_goal_sum = entries_length * time_goal
    # print('goal time: ' + str(time_goal_sum))
    # print('realized time: ' + str(meeting_time_realization_sum))
    # "Percent Differnce" formula: https://tutorial.eyehunts.com/python/python-percentage-difference-between-two-numbers-example-code/
    try:
        percent_difference = int(((time_goal_sum - meeting_time_realization_sum) * 100) / meeting_time_realization_sum)
        if percent_difference < 101:
            time_tracker = '<p class="small text-dark">You are ' + '<b><span class="text-success">' + str(percent_difference) + '% </span></b>' + ' on track with time goals! <br> Good job keeping your talent working - not blabbing! 🧐</p>'
        else:
            time_tracker = '<p class="small text-dark">You are ' + '<b><span class="text-danger">' + str(percent_difference) + '% </span></b>' + ' off track with time goals. <br>  Try to keep it shorter or adjust your goals 🤔</p>'
    except:
        time_tracker = ''
    # End calculate time goal success rate
    entries = MeetingFormEntry.objects.filter(form_settings=form_settings).order_by('-id')
    context = {
        'entries':entries,
        'form_settings':form_settings,
        'time_tracker':time_tracker,
    }
    return render(request, 'note/forms/form-details.html', context)



@login_required(login_url='login')
# Form first save on "POST"
def new_form(request):
    if request.method == "POST":
        title = request.POST['title']
        meeting_time_goal = request.POST['meeting_time_goal']
        meeting_time_goal = int(meeting_time_goal[:-8]) 
        meeting_room_link = request.POST['static_meeting_link']
        scheduled_time = request.POST['start_time']
        # Get the time without the ' minutes' and type cast to integer..
        # ..will aggregate these later to see if meeting time goals

        # Get the ids of the "Project" and the "Team"
        project_id = request.POST['project']
        team_id = request.POST['team']
        try:
            sometimes_record = request.POST['sometimes_record']
        except:
            sometimes_record = 'False'
        # Get actual object
        project = Project.objects.get(id=project_id)
        team = Team.objects.get(id=team_id)
        # Dynamic Text Field Titles (Questions)
        text_field_questions = request.POST.getlist('text_field_questions') # get all questions
        # Create the MeetingFormEntry
        new_form_settings = MeetingFormSettings.objects.create(
            user=request.user,
            project=project,
            team=team,
            title=title,
            meeting_time_goal=meeting_time_goal,
            sometimes_record=sometimes_record,
            scheduled_time=scheduled_time,
            meeting_room_link=meeting_room_link,
        ) 
        i = 0
        for question in text_field_questions:
            MeetingFormQuestion.objects.create(user=request.user, question=question, form_settings=new_form_settings)
            i += 1 
        # Create success alert ToDo: Create try/catch for this and error message/alert
        alert = "Nice! You are on your way to rocking your standups! 😎 🎸"

        # Variables (Form configuration on default page load)
        projects = Project.objects.filter(user=request.user).order_by('-id')
        priority_choices = [
            'Low',
            'Med',
            'High',
        ]
        teams = Team.objects.filter(user=request.user).order_by('-id')
        forms = MeetingFormSettings.objects.filter(user=request.user).order_by('-id')
        # This is for the modal to create a team, whereby the user will select contacts for that team
        contacts = Contact.objects.filter(user=request.user).order_by('-id')
        # End Variables
        context = {
            'contacts':contacts,
            'teams':teams,
            'priority_choices':priority_choices,
            'projects':projects,
            'alert':alert,
            'forms':forms,
        }
        return render(request, 'note/forms/new-form.html', context)
    

    # Variables (Form configuration on default page load)
    projects = Project.objects.filter(user=request.user).order_by('-id')
    priority_choices = [
        'Low',
        'Med',
        'High',
    ]
    teams = Team.objects.filter(user=request.user).order_by('-id')
    forms = MeetingFormSettings.objects.filter(user=request.user).order_by('-id')
    contacts = Contact.objects.filter(user=request.user).order_by('-id')
    # End Variables
    context = {
        'contacts':contacts,
        'teams':teams,
        'priority_choices':priority_choices,
        'projects':projects,
        'forms':forms,
    }
    return render(request, 'note/forms/new-form.html', context)


# @login_required(login_url='login')
# def edit_form(request, pk):
#     # Variables (Form configuration on default page load)
#     form_settings = MeetingFormSettings.objects.get(id=pk)
#     projects = Project.objects.filter(user=request.user).order_by('-id')
#     teams = Team.objects.filter(user=request.user).order_by('-id')
#     forms = MeetingFormSettings.objects.filter(user=request.user).order_by('-id')
#     # End Variables
#     context = {
#         'form_settings':form_settings,
#         'teams':teams,
#         'projects':projects,
#         'forms':forms,
#     }
#     return render(request, 'note/forms/edit-form.html', context)

@login_required(login_url='login')
def edit_form(request, pk):
    if request.method == 'POST':
        form_settings = MeetingFormSettings.objects.get(id=pk) 
        # main fields
        title = request.POST['title']
        meeting_time_goal = request.POST['meeting_time_goal']
        scheduled_time = request.POST['start_time']
        try:
            meeting_room_link = request.POST['static_meeting_link']
            form_settings.meeting_room_link=meeting_room_link
        except:
            pass
        try:
            meeting_time_goal = int(meeting_time_goal[:-8]) 
        except:
            pass
        try:
            sometimes_record = request.POST['sometimes_record']
            form_settings.sometimes_record=False
        except:
            form_settings.sometimes_record=False
        form_settings.scheduled_time=scheduled_time
        form_settings.meeting_time_goal=meeting_time_goal
        form_settings.title=title
        # project FK
        project_id = request.POST['project']
        project = Project.objects.get(id=project_id)
        form_settings.project=project
        # team FK
        team_id = request.POST['team']
        team = Team.objects.get(id=team_id)
        form_settings.team=team
        # questions FK
        text_field_questions = request.POST.getlist('text_field_questions') # get all questions
        # Update the text field questions
        my_questions = MeetingFormQuestion.objects.filter(user=request.user)
        this_form_questions = my_questions.filter(form_settings=form_settings)
        for new_q in text_field_questions:
            for q in this_form_questions: # OG Question
                if q.question == new_q: # Updated Question
                    q.question=new_q
                    q.save()
        
        form_settings.save()
        
        return redirect('form-details', pk=pk)
    

    # Variables (Form configuration on default page load)
    projects = Project.objects.filter(user=request.user).order_by('-id')
    # priority_choices = [
    #     'Low',
    #     'Med',
    #     'High',
    # ]
    teams = Team.objects.filter(user=request.user).order_by('-id')
    forms = MeetingFormSettings.objects.filter(user=request.user).order_by('-id')
    contacts = Contact.objects.filter(user=request.user).order_by('-id')
    form_settings = MeetingFormSettings.objects.get(id=pk)
    # End Variables
    context = {
        'form_settings':form_settings,
        'contacts':contacts,
        'teams':teams,
        # 'priority_choices':priority_choices,
        'projects':projects,
        'forms':forms,
    }
    return render(request, 'note/forms/edit-form.html', context)



# notes
@login_required(login_url='login')
def notes(request): # return variables for managers and team members, template if/else hides each section by user type
    manager_notes = MeetingFormEntry.objects.filter(user=request.user).order_by('-id')
    manager_notes = manager_notes.filter(archived=False)
    team_notes = MeetingFormEntry.objects.filter(archived=False).order_by('-id')
    print(team_notes)
    my_manager_id = request.user.manager_id
    print(my_manager_id)
    my_fellow_team_members = get_user_model().objects.filter(manager_id=my_manager_id)
    print(my_fellow_team_members)
    team_manager = my_fellow_team_members.filter(team_user=False)[0]
    print(team_manager)
    team_notes = team_notes.filter(user=team_manager)
    print(team_notes)
    context = {
        'team_notes':team_notes,
        'manager_notes':manager_notes,
    }
    return render(request, 'note/notes/notes.html', context)

@login_required(login_url='login')
def archived_notes(request): # managers only (all archiving)
    notes = MeetingFormEntry.objects.filter(user=request.user).order_by('-id')
    notes = notes.filter(archived=True)
    return render(request, 'note/notes/archived-notes.html', {'notes':notes,})

@login_required(login_url='login')
def archive_note(request, pk):
    note = MeetingFormEntry.objects.get(id=pk)
    note.archived = True
    note.save()
    # get all notes to redirect to "notes"
    notes = MeetingFormEntry.objects.filter(user=request.user).order_by('-id')
    notes = notes.filter(archived=True)
    alert = 'You archived a Note!'
    return render(request, 'note/notes/archived-notes.html', {'alert':alert,'notes':notes,})

@login_required(login_url='login')
def revive_note(request, pk):
    note = MeetingFormEntry.objects.get(id=pk)
    note.archived = False
    note.save()
    # get all notes to redirect to "notes"
    notes = MeetingFormEntry.objects.filter(user=request.user).order_by('-id')
    notes = notes.filter(archived=False)
    alert = 'You revived a Note!'
    return render(request, 'note/notes/notes.html', {'alert':alert,'notes':notes,})

 
@login_required(login_url='login')
def note_details(request, pk):
    """check if current user has an unread Alert associated with this object, then if so: toggle it"""
    my_alerts = Alert.objects.filter(user=request.user)
    note = MeetingFormEntry.objects.get(id=pk)
    comments = MeetingFormEntryComment.objects.filter(form_entry=note)
    for comment in comments:
        for alert in my_alerts:
            # try:
            if alert.comment == comment: # if the alert in my_alerts has a note that has an id the same as the id we're viewing, then toggle the read field on that alert
                alert.read = True
                alert.save()
            # except:
            #     pass
    note_details = MeetingFormEntry.objects.get(id=pk)
    """Add the contact to the note_details viewed_by_list"""
    current_user_contact = Contact.objects.filter(user=request.user)[0] # THIS IS BUGGY!!!!!
    note_details.viewed_by_list.add(current_user_contact)

    time_goal = note_details.form_settings.meeting_time_goal
    time_took = note_details.meeting_time_realization
    went_over_time = time_took - time_goal
    # form_questions = note_details.form_settings.get_form_questions()
    # form_answers = note_details.form_settings.get_form_answers()
    form_questions = MeetingFormQuestion.objects.filter(user=request.user).order_by('-id')
    form_questions = form_questions.filter(form_settings=note_details.form_settings)
    form_answers = MeetingFormAnswer.objects.filter(user=request.user).order_by('-id')

    # comments is here just to show/hide the section in the template
    comments = True

    context = {
        'comments':comments,
        'form_questions':form_questions,
        'form_answers':form_answers,
        'note_details':note_details,
        'went_over_time':went_over_time,
    }
    return render(request, 'note/notes/note-details.html', context)


@login_required(login_url='login')
def new_note(request, pk):
    form_settings = MeetingFormSettings.objects.get(id=pk)
    questions = MeetingFormQuestion.objects.filter(user=request.user).order_by('-id') #TESTING ONLY
    questions = questions.filter(form_settings=form_settings)

    form_settings = MeetingFormSettings.objects.get(id=pk) #testing static id
    # Calculate time goal success rate
    time_goal = form_settings.meeting_time_goal
    my_entries = MeetingFormEntry.objects.filter(user=request.user).order_by('-id')
    my_entries_with_settings_to_this = my_entries.filter(form_settings=form_settings) # get all my MeetingFormEntry objects that point to this MeetingFormSettings we're submiting a form for
    entries_length = len(my_entries_with_settings_to_this)
    meeting_time_realization_sum = 0
    for entry in my_entries_with_settings_to_this:
        meeting_time_realization_sum += entry.meeting_time_realization
    time_goal_sum = entries_length * time_goal
    # print('goal time: ' + str(time_goal_sum))
    # print('realized time: ' + str(meeting_time_realization_sum))
    # "Percent Differnce" formula: https://tutorial.eyehunts.com/python/python-percentage-difference-between-two-numbers-example-code/
    try:
        percent_difference = int(((time_goal_sum - meeting_time_realization_sum) * 100) / meeting_time_realization_sum)
        if percent_difference < 101:
            time_tracker = '<p class="small text-dark">You are ' + '<b><span class="text-success">' + str(percent_difference) + '% </span></b>' + ' on track with time goals! <br> Good job keeping your talent working - not blabbing! 🧐</p>'
        else:
            time_tracker = '<p class="small text-dark">You are ' + '<b><span class="text-danger">' + str(percent_difference) + '% </span></b>' + ' off track with time goals. <br>  Try to keep it shorter or adjust your goals 🤔</p>'
    except:
        time_tracker = ''
    # End calculate time goal success rate
    project = Project.objects.get(id=form_settings.project.id) # get the project from above form_settings
    # team_members = Contact.objects.filter(user=request.user).order_by('-id') # get the team based on that project, for select participants
    team = Team.objects.get(id=project.team.id)
    team_members = team.contacts.all()
    print(team_members)

    context = {
        'time_tracker':time_tracker,
        'form_settings':form_settings,
        'project':project, # show the user what the name of the project for this meeting note is, (what project the meeting was about)
        'team_members':team_members, # this will allow the user to select multiple participants of this meeting, in case someone was absent, and also who to notify
        'questions':questions, 
    }

    return render(request, 'note/notes/new-note.html', context)

@login_required(login_url='login')
def create_note(request, pk):
    # Get basic form info
    meeting_priority = request.POST['priority']
    meeting_time = request.POST['meeting_time']
    meeting_time = int(meeting_time.replace(' minutes', ''))
    try:
        video_link = request.POST['video_link']
    except:
        video_link = ''
    # Store the text fields (answers)
    answers = request.POST.getlist('answers')
    # ManytoMany fields will later be added
    participants = request.POST.getlist('participants') 
    notify_users = request.POST.getlist('notify-users')
    # Get the form settings
    form_settings = MeetingFormSettings.objects.get(id=pk)
    # Create the form entry
    new_form = MeetingFormEntry.objects.create(
    user=request.user,
    form_settings=form_settings,
    meeting_time_realization=meeting_time,
    video_link=video_link,
    meeting_priority=meeting_priority,
    )
    sent_name_list = ''
    # ManytoMany fields now added
    for participant_id in participants:
        myparticipant = Contact.objects.get(id=participant_id)
        new_form.participants.add(myparticipant)
    for participant_id in notify_users:
        mynotify = Contact.objects.get(id=participant_id)
        new_form.notify_user_list.add(mynotify)
        # Add to sent_name_list
        sent_name_list += mynotify.first_name + ' ' + mynotify.last_name + ' '
        # alert the manager he created a note
        new_alert = Alert.objects.create(
            user=request.user,
            note=new_form,
            )
        # alert the team that a Note was created
        for contact in new_form.notify_user_list:
            new_alert = Alert.objects.create(
            user=contact,
            note=new_form,
            )
            # Check notification settings of each team member
            # if contact.receive_email_notifications:
            #     html_message = loader.render_to_string(
            #                 'note/emails/new-standup-note.html',
            #                 {
            #                     'obj_id': new_form.id,
            #                 }
            #             )
            
            #     send_mail(
            #         'Hey, ' + contact.contact_user_account.first_name + ' Checkout Today\'s Standup Notes! 🧐',
            #         '',
            #         'StandingNotation@gmail.com', # from_email
            #         [contact.contact_user_account.email], # to_list (send to eac user in notify list)
            #         fail_silently=False,
            #         html_message=html_message
            #     )
    # Create "MeetingFormAnswer" Objects
    text_field_answers = request.POST.getlist('text_field_answers')
    i = 0
    question_list = MeetingFormQuestion.objects.filter(form_settings=form_settings)
    for question in question_list:
        for answer in text_field_answers:
            MeetingFormAnswer.objects.create(user=request.user, input_prompt=question, input_response=answer)
            i += 1 
    if sent_name_list != '':
        alert = '<p class="small text-dark">Awesome job staying on track with meeting notes 🎉 <br> Notes sent to ' + str(sent_name_list) + '</p>'
    else:
        alert = '<p class="small text-dark">Awesome job staying on track with meeting notes 🎉 <br> The notes weren\'t sent to any contacts</p>'
    notes = MeetingFormEntry.objects.filter(user=request.user).order_by('-id')
    return render(request, 'note/notes/new-note.html', {'notes':notes,'alert':alert})


# @login_required(login_url='login')
# def edit_note(request):
#     return render(request, 'note/notes/edit-note.html', {})


# contacts
def contact_details(request, pk):
    profile = get_user_model().objects.get(id=pk)
    """check if current user has an unread Alert associated with this object, then if so: toggle it"""
    my_alerts = Alert.objects.filter(user=request.user)
    for alert in my_alerts:
        # try:
        if alert.contact.contact_user_account == profile: # if the alert in my_alerts has a contact that has an id the same as the id we're viewing, then toggle the read field on that alert
            alert.read = True
            alert.save()
        # except:
            # pass
    context = {
        'profile':profile,
    }
    return render(request, 'note/contacts/contact-details.html', context)

@login_required(login_url='login')
def contacts(request):
    contacts = Contact.objects.filter(user=request.user).order_by('-id')
    contacts = contacts.filter(archived=False)
    context = {
        'contacts':contacts,
    }
    return render(request, 'note/contacts/contacts.html', context)

@login_required(login_url='login')
def archived_contacts(request):
    contacts = Contact.objects.filter(user=request.user).order_by('-id')
    contacts = contacts.filter(archived=True)
    return render(request, 'note/contacts/archived-contacts.html', {'contacts':contacts,})

@login_required(login_url='login')
def archive_contact(request, pk):
    contact = Contact.objects.get(id=pk)
    contact.archived = True
    contact.save()
    # get all forms to redirect to "forms"
    contacts = Contact.objects.filter(user=request.user).order_by('-id')
    contacts = contacts.filter(archived=True)
    alert = 'You archived a Contact!'
    return render(request, 'note/contacts/archived-contacts.html', {'alert':alert,'contacts':contacts,})

@login_required(login_url='login')
def revive_contact(request, pk):
    contact = Contact.objects.get(id=pk)
    contact.archived = False
    contact.save()
    # get all forms to redirect to "forms"
    contacts = Contact.objects.filter(user=request.user).order_by('-id')
    contacts = contacts.filter(archived=False)
    alert = 'You revived a Contact!'
    return render(request, 'note/contacts/contacts.html', {'alert':alert,'contacts':contacts,})

 
@login_required(login_url='login')
def new_contact(request):
    return render(request, 'note/contacts/new-contact.html', {})


@login_required(login_url='login')
def edit_contact(request):
    return render(request, 'note/contacts/edit-contact.html', {})


# projects
@login_required(login_url='login')
def projects(request):
    projects = Project.objects.filter(user=request.user).order_by('-id')
    projects = projects.filter(archived=False)
    teams = Team.objects.filter(user=request.user).order_by('-id')
    context = {
        'teams':teams, # for the create modal
        'projects':projects,
    }
    return render(request, 'note/projects/projects.html', context)


@login_required(login_url='login')
def archived_projects(request):
    projects = Project.objects.filter(user=request.user).order_by('-id')
    projects = projects.filter(archived=True)
    teams = Team.objects.filter(user=request.user).order_by('-id')
    context = {
        'teams':teams, # for the create modal
        'projects':projects,
    }
    return render(request, 'note/projects/archived-projects.html', context)

@login_required(login_url='login')
def archive_project(request, pk):
    project = Project.objects.get(id=pk)
    project.archived = True
    project.save()
    # get all forms to redirect to "forms"
    projects = Project.objects.filter(user=request.user).order_by('-id')
    projects = projects.filter(archived=True)
    alert = 'You archived a Project!'
    teams = Team.objects.filter(user=request.user).order_by('-id')
    context = {
        'alert':alert,
        'teams':teams, # for the create modal
        'projects':projects,
    }
    return render(request, 'note/projects/archived-projects.html', context)

@login_required(login_url='login')
def revive_project(request, pk):
    project = Project.objects.get(id=pk)
    project.archived = False
    project.save()
    # get all forms to redirect to "forms"
    projects = Project.objects.filter(user=request.user).order_by('-id')
    projects = projects.filter(archived=False)
    alert = 'You revived a Project!'
    teams = Team.objects.filter(user=request.user).order_by('-id')
    context = {
        'alert':alert,
        'teams':teams, # for the create modal
        'projects':projects,
    }
    return render(request, 'note/projects/projects.html', context)


@login_required(login_url='login')
def create_project(request):
    team_id = request.POST['team']
    team = Team.objects.get(id=team_id)
    title = request.POST.get('title') 

    new_project = Project.objects.create(
        user=request.user,
        team=team,
        title=title
    )
    # Variables (Form configuration on default page load)
    # projects = Project.objects.filter(user=request.user).order_by('-id')
    # priority_choices = [
    #     'Low',
    #     'Med',
    #     'High',
    # ]
    # teams = Team.objects.filter(user=request.user).order_by('-id')
    # forms = MeetingFormSettings.objects.filter(user=request.user).order_by('-id')
    # # End Variables
    # general_alert = 'You created your first Project - So pro! 👔'
    # context = {
    #     'general_alert':general_alert,
    #     'teams':teams,
    #     'priority_choices':priority_choices,
    #     'projects':projects,
    #     'forms':forms,
    # }
    # return render(request, 'note/forms/new-form.html', context)
    return redirect('projects')


@login_required(login_url='login')
def project_details(request, pk):
    project_details = Project.objects.get(id=pk) 
    project_team_contacts = project_details.team.contacts.all()
    if project_details.user == request.user:
        context = {
            'project_team_contacts':project_team_contacts,
            'project_details':project_details,
        }
        return render(request, 'note/projects/project-details.html', context)
    else:
        return redirect('projects') # ..you naughty user


@login_required(login_url='login')
def new_project(request):
    return render(request, 'note/projects/new-project.html', {})


@login_required(login_url='login')
def edit_project(request):
    return render(request, 'note/projects/edit-project.html', {})


# teams
@login_required(login_url='login')
def teams(request):
    teams = Team.objects.filter(user=request.user).order_by('-id')
    teams = teams.filter(archived=False)
    context = {
        'teams':teams,
    }
    return render(request, 'note/teams/teams.html', context)


@login_required(login_url='login')
def archived_teams(request):
    teams = Team.objects.filter(user=request.user).order_by('-id')
    teams = teams.filter(archived=True)
    return render(request, 'note/teams/archived-teams.html', {'teams':teams,})

@login_required(login_url='login')
def archive_team(request, pk):
    team = Team.objects.get(id=pk)
    team.archived = True
    team.save()
    # get all forms to redirect to "forms"
    teams = Team.objects.filter(user=request.user).order_by('-id')
    teams = teams.filter(archived=True)
    alert = 'You archived a Team!'
    return render(request, 'note/teams/archived-teams.html', {'alert':alert,'teams':teams,})

@login_required(login_url='login')
def revive_team(request, pk):
    team = Team.objects.get(id=pk)
    team.archived = False
    team.save()
    # get all forms to redirect to "forms"
    teams = Team.objects.filter(user=request.user).order_by('-id')
    teams = teams.filter(archived=False)
    alert = 'You revived a Team!'
    return render(request, 'note/teams/teams.html', {'alert':alert,'teams':teams,})


@login_required(login_url='login')
def team_details(request, pk):
    team_details = Team.objects.get(id=pk) 
    if team_details.user == request.user:
        team_projects = Project.objects.filter(team=team_details)
        team_contacts = team_details.contacts.all()
        contacts = Contact.objects.filter(user=request.user)
        context = {
            'contacts':contacts,
            'team_contacts':team_contacts,
            'team_details':team_details,
            'team_projects':team_projects,
        }
        return render(request, 'note/teams/team-details.html', context)
    else:
        return redirect('teams') # ..you naughty user

 
@login_required(login_url='login')
def new_team(request):
    return render(request, 'note/teams/new-team.html', {})

@login_required(login_url='login')
def create_team(request):
    team_name = request.POST['team_name']
    team_contacts = request.POST.getlist('team_contacts') 

    new_team = Team.objects.create(
        user=request.user,
        title=team_name,
    )
   # ManytoMany field "contacts" are now added to the new_team
    for contact_id in team_contacts:
        teamContact = Contact.objects.get(id=contact_id)
        new_team.contacts.add(teamContact)

    # # Variables (Form configuration on default page load)
    # projects = Project.objects.filter(user=request.user).order_by('-id')
    # priority_choices = [
    #     'Low',
    #     'Med',
    #     'High',
    # ]
    # teams = Team.objects.filter(user=request.user).order_by('-id')
    # forms = MeetingFormSettings.objects.filter(user=request.user).order_by('-id')
    # contacts = Contact.objects.filter(user=request.user).order_by('-id')
    # # End Variables
    # general_alert = 'You created your first Team - What a team player! 🙌'
    # context = {
    #     'general_alert':general_alert,
    #     'contacts':contacts,
    #     'teams':teams,
    #     'priority_choices':priority_choices,
    #     'projects':projects,
    #     'forms':forms,
    # }
    # return render(request, 'note/forms/new-form.html', context)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER')) # return to last page for now since its in new form for new users and  also general new create project/team




class EditTeamView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Team
    template_name = 'note/teams/edit-team.html'
    fields = (
            'title', 
            'contacts', 
            )
    success_message = 'Your Team has been updated!'
    success_url = reverse_lazy('teams')



class EditProjectView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Project
    template_name = 'note/projects/edit-project.html'
    fields = (
            'title', 
            'team', 
            )
    success_message = 'Your Project has been updated!'
    success_url = reverse_lazy('projects')




# AJAX GET - comments
def get_comments_data(request): 
    comments = MeetingFormEntryComment.objects.all().order_by('-id')
    data = []
    for obj in comments:
        # True/False if current user is owner, to show edit/delete options
        if obj.author.id == request.user.id:
            owner_bool = True
        else:
            owner_bool = False
        # if request.user in obj.liked.all():
        name = obj.author.first_name + ' ' + obj.author.last_name
        # date = datetime.strptime(obj.created, '%Y-%m-%d')
        date = obj.created
        print(date)
        item = {
            'id': obj.id,
            'owner':owner_bool,
            'comment': obj.comment,
            'date': date,
            'name': name,
            'profile_photo': str(obj.author.imageURL),
            # ToDo: Check if the user liked the comment or not
            # 'liked': True if request.user in obj.liked.all() else False,
            # 'count': obj.like_count,
        } 
        data.append(item)
    return JsonResponse({'data':data})


# AJAX POST
@login_required(login_url='login')
def create_comment(request, pk):
    comment = request.POST.get('commentContent')
    note_details = MeetingFormEntry.objects.get(id=pk)
    new_comment = MeetingFormEntryComment.objects.create(
        author=request.user,
        form_entry=note_details,
        comment=comment,
    )
    data = [] # clean up
    # alert the manager someone created a comment
    new_alert = Alert.objects.create(
        user=note_details.user, # user who made the note_details
        comment=new_comment,
        )
    return JsonResponse({'data':data})
    # email the manager someone created a comment
    # if note_details.user.receive_email_notifications:
    #         html_message = loader.render_to_string(
    #                     'note/emails/new-note-comment.html',
    #                     {
    #                         'obj_id': note_details.id,
    #                         'status': 'created',
    #                     }
    #                 )
        
    #         send_mail(
    #             'Hey, ' + note_details.user.first_name + ' - Checkout a new comment! 🎊',
    #             '',
    #             'StandingNotation@gmail.com', # from_email
    #             [note_details.user.email],  
    #             fail_silently=False,
    #             html_message=html_message
    #         )
    # alert the users in the contact list that a Note got a comment
    # for contact in note_details.notify_user_list.all():
    #     new_alert = Alert.objects.create(
    #     user=contact,
    #     comment=new_comment,
    #     )
    #     # Check notification settings of each team member
    #     if contact.receive_email_notifications:
    #         html_message = loader.render_to_string(
    #                     'note/emails/new-note-comment.html',
    #                     {
    #                         'obj_id': note_details.id,
    #                         'status': 'are tagged in',
    #                     }
    #                 )
        
    #         send_mail(
    #             'Hey, ' + contact.contact_user_account.first_name + ' - Checkout a new comment! 🎊',
    #             '',
    #             'StandingNotation@gmail.com', # from_email
    #             [contact.contact_user_account.email], # to_list (send to eac user in notify list)
    #             fail_silently=False,
    #             html_message=html_message
    #         )
    


# AJAX POST
@login_required(login_url='login')
def delete_comment(request, pk):
    comment_id = request.POST['deleteCommentID']
    comment_id = int(comment_id)
    comment = MeetingFormEntryComment.objects.get(id=comment_id)
    comment.delete()
    return redirect("note-details", pk=pk)



# DARK MODE TOGGLE
def dark_mode_toggle(request, mode): # 1 is dark mode, 2 is light mode
    current_user = get_user_model().objects.get(id=request.user.id)
    if mode == 2:
        current_user.dark_mode = False
        current_user.save()
    if mode == 1:
        current_user.dark_mode = True
        current_user.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))