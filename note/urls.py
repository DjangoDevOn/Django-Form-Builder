from django.urls import path
from .views import *

urlpatterns = [
    path('dashboard/', dashboard, name="dashboard"),
    path('new-share-url/', new_share_url, name="new-share-url"),
    # forms
    path('forms/', forms, name="forms"),
    path('archived-forms/', archived_forms, name="archived-forms"),
    path('archive-form/<int:pk>/', archive_form, name="archive-form"), 
    path('revive-form/<int:pk>/', revive_form, name="revive-form"),
    path('new-form/', new_form, name="new-form"),
    path('edit-form/<int:pk>/', edit_form, name="edit-form"),
    path('form-details/<int:pk>/', form_details, name="form-details"),
    # notes
    path('notes/', notes, name="notes"),
    path('archived-notes/', archived_notes, name="archived-notes"),
    path('archive-note/<int:pk>/', archive_note, name="archive-note"), 
    path('revive-note/<int:pk>/', revive_note, name="revive-note"),
    path('new-note/<int:pk>/', new_note, name="new-note"), # use the PK of a MeetingFormSettings to save a note to it
    path('create-note/<int:pk>/', create_note, name="create-note"), # new note submit
    # path('edit-note/<int:pk>/', edit_note, name="edit-note"),
    path('note-details/<int:pk>/', note_details, name="note-details"),
    # contacts
    path('contacts/', contacts, name="contacts"),
    path("contact-details/<int:pk>/", login_required(contact_details), name="contact-details"),
    path('archived-contacts/', archived_contacts, name="archived-contacts"),
    path('archive-contact/<int:pk>/', archive_contact, name="archive-contact"), 
    path('revive-contact/<int:pk>/', revive_contact, name="revive-contact"),
    path('new-contact/', new_contact, name="new-contact"),
    # projects
    path('projects/', projects, name="projects"),
    path('archived-projects/', archived_projects, name="archived-projects"),
    path('archive-project/<int:pk>/', archive_project, name="archive-project"), 
    path('revive-project/<int:pk>/', revive_project, name="revive-project"),
    path('new-project/', new_project, name="new-project"),
    path('create-project/', create_project, name="create-project"), # new team submit
    path('edit-project/<int:pk>/', EditProjectView.as_view(), name="edit-project"),
    path('project-details/<int:pk>/', project_details, name="project-details"),
    # teams
    path('teams/', teams, name="teams"),
    path('archived-teams/', archived_teams, name="archived-teams"),
    path('archive-team/<int:pk>/', archive_team, name="archive-team"), 
    path('revive-team/<int:pk>/', revive_team, name="revive-team"),
    path('new-team/', new_team, name="new-team"), # new team form
    path('create-team/', create_team, name="create-team"), # new team submit
    path('edit-team/<int:pk>/', EditTeamView.as_view(), name="edit-team"),
    path('team-details/<int:pk>/', team_details, name="team-details"),
    # comments
    path('create-comment/<int:pk>/', create_comment, name="create-comment"), # AJAX POST - in note-details.html: new comment submit
    path('get-comments-data/', get_comments_data, name="get-comments-data"), #AJAX GET - in note-details.html
    path('delete-comment/<int:pk>/', delete_comment, name="delete-comment"),
    # global
    path('get-user-forms-data/', get_user_forms_data, name="get-user-forms-data"), # AJAX GET - in base.html check on modal open
    path('dark-mode-toggle/<int:mode>/', dark_mode_toggle, name="dark-mode-toggle"), # DARK MODE TOGGLE
]

