from django.urls import path
from api.contacts.views import ContactCreateView

urlpatterns = [
    path('contacts/', ContactCreateView.as_view(), name='contact-create'),
]
