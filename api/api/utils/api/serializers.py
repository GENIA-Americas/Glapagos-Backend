from django.apps import apps
from rest_framework import serializers
from .model import model_to_model_defintion
from collections import OrderedDict

def related_field_model_get_model_fields(related_field):
    for field in related_field.field.model._meta.get_fields():
        if related_field.field.name == field.name:
            continue
        yield field.name

def django_serializers_from_model_field(related_field):
    serializer_fields = []
    for field in related_field_model_get_model_fields(related_field):
        serializer_fields.append(field)
    return django_serializers_from_model(related_field.field.model, fields=serializer_fields)

def get_key_chain(obj, key_chain, default=None):
    if not key_chain:
        return obj
    if key_chain[0] not in obj:
        return default
    return get_key_chain(obj[key_chain[0]], key_chain[1:])

def django_serializer_from_model_definition(model_definition, crud_serializers={}, requester_field=['created_by', 'owner', 'updated_by'], fields=None):
    app = model_definition['app'] if 'app' in model_definition else 'api'
    model_class = apps.get_model(app_label=app, model_name=model_definition['name'])
    name = model_definition['name']
    model_class_name = name.capitalize()
    serializer_class_name = f'{model_class_name}Serializer'
    # TODO: verify if field is in class
    serializer_field_names = ('id', 
        *(field['name'] for field in model_definition['fields'] if field['name'] != 'id')
    ) if fields is None else fields
    related_fields_expand = get_key_chain(model_definition, ['actions', 'read', 'related_fields_expand'], [])
    
    class Meta:
        model = model_class
        fields = serializer_field_names
    
    # get read only fields
    serializer_read_fields = dict()
    if related_fields_expand:
        for related_field in related_fields_expand:
            if hasattr(model_class, related_field):
                # serializer_read_fields[related_field] = django_serializers_from_model_field(getattr(model_class, related_field))['list']
                serializer_read_fields[related_field] = django_serializers_from_model_field(getattr(model_class, related_field))['list']

    # get write only fields
    serializer_write_fields = dict()
    if requester_field:
        for field_name in serializer_field_names:
            if field_name in requester_field:
                serializer_write_fields[field_name] = serializers.HiddenField(default=serializers.CurrentUserDefault())

    serializer_fields = dict(
        Meta=Meta,
    )

    write_serializer = type(serializer_class_name, (serializers.ModelSerializer, ), {**serializer_fields, **serializer_write_fields})
    list_serializer = type(serializer_class_name, (serializers.ModelSerializer, ), {**serializer_read_fields, **serializer_fields})
    #list_serializer = serializers.ModelSerializer.__new__(serializers.ModelSerializer, (serializers.ModelSerializer, ), {**serializer_read_fields, **serializer_fields})

    serializer_classes = dict()

    if 'crud' not in crud_serializers:
        serializer_classes['crud'] = write_serializer
    
    if 'create' not in crud_serializers:
        serializer_classes['create'] = write_serializer
    
    if 'update' not in crud_serializers:
        serializer_classes['update'] = write_serializer
    
    if 'list' not in crud_serializers:
        serializer_classes['list'] = list_serializer
    
    if 'retrieve' not in crud_serializers:
        serializer_classes['retrieve'] = list_serializer
    
    serializer_classes.update(crud_serializers)
    
    return serializer_classes

def django_serializers_from_model(model, fields=None):
    model_definition = model_to_model_defintion(model, fields)
    serializer_class = django_serializer_from_model_definition(model_definition)
    return serializer_class
