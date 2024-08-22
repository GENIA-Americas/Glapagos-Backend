def register_viewset_url(views, router, model_definition):
    name = model_definition['name']
    model_class_name = name.capitalize()
    url_route_name = name.lower()
    viewset_class_name = f'{model_class_name}ViewSet'

    router.register(url_route_name, getattr(views, viewset_class_name), basename=name.lower())

def register_viewset_urls(views, router, model_definitions):
    for model_definition in model_definitions:
        register_viewset_url(views, router, model_definition)
