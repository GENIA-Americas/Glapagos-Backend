from rest_framework import permissions, mixins, filters, status
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.utils.translation import gettext_lazy as _

from api.datasets.serializers import TableSerializer, TableTransformSerializer, ChartSerializer
from api.datasets.services import ChartService, apply_transformations, chart_select
from api.datasets.models import File, Table


class TableViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = TableSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        return Table.objects.filter(mounted=True, file__owner=self.request.user)

    @action(detail=True, methods=['post'], name='transform', url_path='transform',
            permission_classes=[permissions.IsAuthenticated], serializer_class=TableTransformSerializer)
    def transform(self, request, pk, **kwargs):
        user = request.user
        table = Table.objects.filter(pk=pk).first()
        if not table:
            raise NotFound(detail=_(f"Table not found."))

        serializer = self.get_serializer(data=request.data, context={"table": table, "user": user})
        serializer.is_valid(raise_exception=True)

        create_table = serializer.validated_data['create_table']
        public_destination = serializer.validated_data.get('public_destination')
        transformations = serializer.validated_data['transformations']

        transformed_table = apply_transformations(table, user, transformations, create_table, public_destination)

        return Response(data={
            'detail': _("Table transformed successfully: ") + transformed_table.name
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], name='chart', url_path='chart',
            permission_classes=[permissions.IsAuthenticated], serializer_class=ChartSerializer)
    def transform(self, request, pk, **kwargs):
        user = request.user
        table = Table.objects.filter(pk=pk).first()
        if not table:
            raise NotFound(detail=_(f"Table not found."))

        serializer = self.get_serializer(data=request.data, context={"table": table, "user": user})
        serializer.is_valid(raise_exception=True)

        x = serializer.validated_data.get('x')
        y = serializer.validated_data.get('y')
        limit = serializer.validated_data.get('limit', 0)

        service: ChartService = chart_select(x, y, table=table, user=self.request.user, limit=limit)
        results = service.process()

        return Response(data=results, status=status.HTTP_200_OK)


class PublicTableListView(mixins.ListModelMixin, GenericViewSet):
    serializer_class = TableSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        return Table.objects.filter(public=True, mounted=True)


class PrivateTableListView(mixins.ListModelMixin, GenericViewSet):
    serializer_class = TableSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        return Table.objects.filter(public=False, mounted=True, owner=self.request.user)


class TransformedTableListView(mixins.ListModelMixin, GenericViewSet):
    serializer_class = TableSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        return Table.objects.filter(is_transformed=True, mounted=True, owner=self.request.user)
