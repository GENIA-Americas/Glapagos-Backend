def model_to_model_defintion(model, fields=None):
    fields = fields if fields else [field.name for field in model._meta.get_fields()]
    model_fields = [
        {
            'name': field
        }
        for field in fields
    ]
    model_definition = {
        'app': model._meta.app_label,
        'name': model._meta.model_name,
        'fields': model_fields
    }
    return model_definition
