from django.db.models import Q
from rest_framework.viewsets import GenericViewSet
from rest_framework import permissions, mixins, filters

from api.datasets.serializers import TableSerializer
from api.datasets.models import File, Table


class TableViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = TableSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        return Table.objects.filter(mounted=True, file__owner=self.request.user)


class PublicTableListView(mixins.ListModelMixin, GenericViewSet):
    serializer_class = TableSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        return Table.objects.filter(file__public=True, mounted=True)


class PrivateTableListView(mixins.ListModelMixin, GenericViewSet):
    serializer_class = TableSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        return Table.objects.filter(file__public=False, mounted=True, file__owner=self.request.user)
