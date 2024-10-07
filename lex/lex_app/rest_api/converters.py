def create_model_converter(model_collection):
    """
    Creates a model converter for a given model collection.

    This function generates a converter class that can be used to convert
    model IDs to model instances and vice versa. The converter class will
    have methods `to_python` and `to_url` for these conversions.

    Parameters
    ----------
    model_collection
        A collection of models that provides methods to get model instances
        and all model IDs.

    Returns
    -------
    type
        A dynamically created converter class with `to_python` and `to_url` methods.
    """
    def to_python(self, value):
        return model_collection.get_container(value)

    def to_url(self, value):
        return value.id

    regex = '|'.join([id for id in model_collection.all_model_ids])

    converter = type('ModelConverter', (), dict(regex=regex))
    converter.to_python = to_python
    converter.to_url = to_url
    return converter