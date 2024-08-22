from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response

from django.apps import apps

from api.utils.api.model import model_to_model_defintion
from api.utils.api.serializers import django_serializer_from_model_definition


def get_viewset_parents_by_actions(actions):
    parents = []
    for action in actions:
        if action == 'crud':
            parents = [viewsets.ModelViewSet]
            break
        if action == 'read':
            parents = [viewsets.ReadOnlyModelViewSet]
            break
    return tuple(parents)


def get_viewset_permissions_by_actions(actions):
    parents = [IsAuthenticated]
    for action in actions:
        if action.get('public') == True:
            parents = [AllowAny]
            break
    return tuple(parents)


def get_serializer_class_function(model_definitions, serializer_classes=None):
    if serializer_classes is None:
        serializer_classes = django_serializer_from_model_definition(model_definitions)

    def get_serializer_class(self, *args, **kwargs):
        if self.action in serializer_classes:
            return serializer_classes[self.action]
        elif self.action in ['create', 'update', 'partial_update'] and 'write' in serializer_classes:
            return serializer_classes['write']
        elif self.action in ['retrieve', 'list'] and 'read' in serializer_classes:
            return serializer_classes['read']
        elif 'crud' in serializer_classes:
            return serializer_classes['crud']

    return get_serializer_class


def model_viewset_from_model_definition(serializer_classes, model_definition, permissions=None, lookup_field=None,
                                        search_fields=None):
    name = model_definition['name']
    model_class_name = name.capitalize()
    viewset_class_name = f'{model_class_name}ViewSet'
    app = model_definition['app'] if 'app' in model_definition else 'api'

    action_definitions = model_definition['actions']
    view_parents = get_viewset_parents_by_actions(action_definitions)

    model_class = apps.get_model(
        app_label=app, model_name=model_definition['name'])
    viewset_class_attributes = {
        # "__module__": "cmsapi.api.views",
        'queryset': model_class.objects.all().order_by('id'),
        'permission_classes': permissions if permissions else get_viewset_permissions_by_actions(action_definitions),
        'get_serializer_class': get_serializer_class_function(model_definition, serializer_classes=serializer_classes),
    }

    if lookup_field:
        viewset_class_attributes['lookup_field'] = lookup_field

    if search_fields:
        viewset_class_attributes['search_fields'] = search_fields
        viewset_class_attributes['filter_backends'] = [filters.SearchFilter]

    viewset_class = type(viewset_class_name, view_parents, viewset_class_attributes)
    return viewset_class


def model_viewsets_from_model_definitions(serializers, model_definitions):
    for model_definition in model_definitions:
        viewset_class = model_viewset_from_model_definition(
            serializers, model_definition)
        yield viewset_class


def crud_from_model(
        model,
        default_serializer=None,
        requester_field=['created_by', 'owner', 'updated_by'],
        permissions=None,
        lookup_field=None,
        search_fields=None,
):
    model_definitions = model_to_model_defintion(model)
    model_definitions['actions'] = {
        'crud': {},
    }
    if default_serializer:
        serializer_classes = {
            'crud': default_serializer
        }
    else:
        serializer_classes = django_serializer_from_model_definition(model_definitions, requester_field=requester_field)
    viewset = model_viewset_from_model_definition(
        serializer_classes, model_definitions, permissions=permissions, search_fields=search_fields,
        lookup_field=lookup_field)
    return viewset


def read_view_from_model(
        model,
        serializer_classes=None,
        permissions=None,
        lookup_field=None,
        related_fields_expand=None,
        fields=None,
        search_fields=None,
):
    model_definitions = model_to_model_defintion(model, fields)
    model_definitions['actions'] = {
        "read": {
            "related_fields_expand": related_fields_expand,
        }
    }

    serializer_classes = serializer_classes if serializer_classes else django_serializer_from_model_definition(
        model_definitions)
    viewset = model_viewset_from_model_definition(
        serializer_classes, model_definitions, permissions=permissions, lookup_field=lookup_field,
        search_fields=search_fields)
    return viewset
