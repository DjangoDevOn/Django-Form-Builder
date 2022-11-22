from django.urls import path
from .views import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views # For reset password


urlpatterns = [
    path("user-status/", user_status, name="user-status"), # AJAX
    path("unread-alerts/", unread_alerts, name="unread-alerts"), # AJAX
    path("unread-alerts-count/", unread_alerts_count, name="unread-alerts-count"), # AJAX
    path("profile-photo/", profile_photo, name="profile-photo"), # AJAX
    # form to reset email
    path('reset_password/', auth_views.PasswordResetView.as_view(template_name="password/forgot-password.html"), name="reset_password"),
    # email link success message
    path('reset_password-sent/', auth_views.PasswordResetDoneView.as_view(template_name="password/password-reset-sent.html"), name="password_reset_done"),
    # link to reset password form in email
    path('password_change/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="password/password-reset-form.html"), name="password_reset_confirm"),
    # password successfully changed message
    # signup stuff
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name="password/password-reset-done.html"), name="password_reset_complete"),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('activate/<uidb64>/<token>/', ActivateAccount.as_view(), name='activate'),
    path("team-signup/<str:manager_id>", team_signup, name="team-signup"), # stores manager_id code from url and places in manager_id field (invisible)
    path("login/", signin, name="login"),
    path("signout/", signout, name="signout"),
    # account settings
    # path('change-password/', login_required(PasswordsChangeView.as_view(template_name="config/change-password.html")), name='change-password'),
    path("edit-profile/<int:pk>", login_required(UserAccountUpdate.as_view()), name="edit-profile"),
    path("edit-email/<int:pk>", login_required(UserEmailUpdate.as_view()), name="edit-email"),
    path("my-profile", login_required(my_profile), name="my-profile"),
    # global
    path("send-feedback/", send_feedback, name="send-feedback"), # uses a modal / form 
]

