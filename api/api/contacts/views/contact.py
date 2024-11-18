from rest_framework import generics
from api.contacts.models import Contact
from api.contacts.serializers import ContactSerializer


class ContactCreateView(generics.CreateAPIView):
    serializer_class = ContactSerializer
