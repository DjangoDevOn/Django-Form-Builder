import re
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.messages.views import SuccessMessageMixin
from .forms import *
# from website.models import *
from .models import *
from note.models import *
from django.template import loader
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import redirect, render
from django.views.generic import UpdateView, View
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail


def team_signup(request, manager_id): # JS caches pk (manager id of inviter) adds to form field manger_id for new team user after redirecting to the signup page
    return render(request, 'accounts/team-signup.html', {})

####### AJAX #######
def unread_alerts_count(request):
    my_alerts = Alert.objects.filter(user=request.user)
    unread_alerts = my_alerts.filter(read=False)
    unread_alerts_count = unread_alerts.count()
    return JsonResponse({'unread_alerts_count':unread_alerts_count})


def user_status(request):  
    user = get_user_model().objects.get(id=request.user.id)
    team_user_status = user.team_user
    if team_user_status: # if they are a team user (or fresh manager account with no invite link generated)
        manager = False
    else:
        manager = True
    print(manager)
    return JsonResponse({'manager':manager})

def unread_alerts(request):
    my_alerts = Alert.objects.filter(user=request.user)
    unread_alerts = my_alerts.filter(read=False).order_by('-id')
    unread_alert_list = [] 
    for obj in unread_alerts:
        obj_name = 'ERROR'
        obj_url = ''
        if obj.comment:
            obj_name = 'Comment'
            obj_url = 'note-details/' + str(obj.comment.form_entry.id) + '/#comments'
        if obj.note:
            obj_name = 'Note'
            obj_url = 'note-details/' + str(obj.note.id) + '/'
        if obj.contact:
            obj_name = 'Contact'
            obj_url = 'contact-details/' + str(obj.contact.id) + '/'
        created = str(obj.created)
        created = created[:10]
        item = {
            'id': obj.id,
            'created': created,
            'obj_name': obj_name, # the created object's "kind"
            'obj_url':obj_url,
        }
        unread_alert_list.append(item) # append dictionary to the list
    return JsonResponse({'unread_alert_list':unread_alert_list})


def profile_photo(request):
    profile = get_user_model().objects.get(id=request.user.id)
    profile_photo = str(profile.profile_photo)
    profile_photo = '/media/' + profile_photo
    return JsonResponse({'profile_photo':profile_photo})

####### END AJAX #######

class SignUpView(View):
    form_class = SignUpForm
    template_name = 'accounts/signup.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():

            user = form.save(commit=False)
            # user.is_active = False # Deactivate account till it is confirmed
            user.save()

            # current_site = get_current_site(request)
            # subject = 'Activate Your StandingNotation Account'
            # message = render_to_string('accounts/account-activation-email.html', {
            #     'user': user,
            #     'domain': current_site.domain,
            #     'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            #     'token': account_activation_token.make_token(user),
            # })
            # user.email_user(subject, message)

            # messages.success(request, ('Please Confirm your email to complete registration.'))
            messages.success(request, ('Welcome to StandingNotation!'))

            msg_content = 'Welcome to StandingNotation.com! ' + user.first_name + '!'

            # Create contact associated with manager, pointing to this newly created user
            managers = get_user_model().objects.filter(team_user=False)
            for manager in managers:
                if manager.manager_id == user.manager_id:
                    new_contact = Contact.objects.create(
                        user=manager, # the user is the manager
                        contact_user_account=user, # the contact_user_account is who just signed up
                    )
                    # alert the manager a contact was created / their invited team member signed up
                    new_alert = Alert.objects.create(
                        user=manager,
                        contact=new_contact,
                    )
                    # # Check notification settings, email the manager
                    # if manager.receive_email_notifications:
                    #     html_message = loader.render_to_string(
                    #                 'note/emails/new-contact.html',
                    #                 {
                    #                     'obj_id': new_contact.id,
                    #                     'username': manager.first_name,
                    #                     'team-member': user.first_name,
                    #                 }
                    #             )
                        
                        # send_mail(
                        #     user.first_name + user.last_name + ' joined StandingNotation! 🎉 ',
                        #     '',
                        #     'StandingNotation@gmail.com', # from_email
                        #     [manager.email], # to_list (send to eac user in notify list)
                        #     fail_silently=False,
                        #     html_message=html_message
                        # )

            return redirect('login')

        return render(request, self.template_name, {'form': form})


class ActivateAccount(View):
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.email_confirmed = True
            user.save()

            login(request, user)
            messages.success(request, ('Your account have been confirmed.'))
            return redirect('dashboard')
        else:
            messages.warning(request, ('The confirmation link was invalid, possibly because it has already been used.'))
            return redirect('login')


def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.info(request,"Username or Password is not correct.")
    return render(request, 'accounts/login.html',{})



def signout(request):
    logout(request)
    return redirect('login') 



################################### PROFILE ###################################

# Personal Profile View
def my_profile(request):
    profile = User.objects.get(id=request.user.id)
    context = {
        'profile':profile,
    }
    return render(request, 'accounts/config/my-profile.html', context)


class UserAccountUpdate(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    template_name = 'accounts/config/edit-profile.html'
    fields = (
    'profile_photo',
    'first_name',
    'last_name',
    'receive_email_notifications',
    )
    success_message = 'Your Settings have been updated!'
    success_url = reverse_lazy('my-profile')
 
class UserEmailUpdate(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    template_name = 'accounts/config/edit-profile.html'
    fields = (
    'email',
    )
    success_message = 'Your Email has been updated!'
    success_url = reverse_lazy('my-profile')
 

def send_feedback(request):
    feedback_type = request.POST['feedback_type']
    feedback_content = request.POST['feedback_content']
    try:
        video_url = request.POST['video_url']
    except:
        video_url = ''
    try:
        screenshot_url = request.POST['screenshot_url']
    except:
        screenshot_url = ''
    try:
        issue_page_url = request.POST['issue_page_url']
    except:    
        issue_page_url = ''


    new_feedback = Feedback.objects.create(
        sender=request.user,
        video_url=video_url,
        screenshot_url=screenshot_url,
        issue_page_url=issue_page_url,
        feedback_content=feedback_content,
        feedback_type=feedback_type,
    )

    # STATIC SEND TO ADDRESS FOR THE ADMIN OF STANDING NOTATION:
    # send_mail(
    #             'Hey, you got some feedback on StandingNotation! 🎊',
    #             'You can view the message in the Admin Dashboard.',
    #             'noreply@StandingNotation.com', # from_email
    #             ['StandingNotation@gmail.com'],  
    #             fail_silently=False,
    #         )

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
