from rest_framework import serializers, viewsets


class RestApiModelSerializerTemplate(serializers.ModelSerializer):
    """
    A template serializer for REST API models.

    This serializer includes a method field for a short description of the object.

    Attributes
    ----------
    short_description : serializers.SerializerMethodField
        A method field that provides a short description of the object.
    """
    short_description = serializers.SerializerMethodField()

    def get_short_description(self, obj):
        """
        Get a short description of the object.

        Parameters
        ----------
        obj : Any
            The object to describe.

        Returns
        -------
        str
            A string representation of the object.
        """
        return str(obj)

    class Meta:
        """
        Meta options for the serializer.

        Attributes
        ----------
        model : None
            The model class to serialize.
        fields : str
            The fields to include in the serialization.
        """
        model = None
        fields = "__all__"


class RestApiModelViewSetTemplate(viewsets.ModelViewSet):
    """
    A template view set for REST API models.

    This view set provides default queryset and serializer class attributes.

    Attributes
    ----------
    queryset : None
        The queryset to use for the view set.
    serializer_class : None
        The serializer class to use for the view set.
    """
    queryset = None
    serializer_class = None


ID_FIELD_NAME = 'id_field'
SHORT_DESCR_NAME = 'short_description'


def model2serializer(model, fields=None):
    """
    Create a serializer class for a given model.

    This function dynamically creates a serializer class for the specified model,
    including all specified fields and additional fields for the primary key and
    a short description.

    Parameters
    ----------
    model : Model
        The Django model class to serialize.
    fields : list of str, optional
        The list of field names to include in the serialization. If not provided,
        all fields from the model are included.

    Returns
    -------
    type
        A dynamically created serializer class for the model.
    """
    if fields is None:
        fields = [field.name for field in model._meta.fields]

    serialized_pk_name = serializers.ReadOnlyField(default=model._meta.pk.name)
    fields.append(ID_FIELD_NAME)
    fields.append(SHORT_DESCR_NAME)

    return type(
        model._meta.model_name + 'Serializer',
        (RestApiModelSerializerTemplate,),
        {
            # the primary-key field is always mapped to a field with name id, as the frontend requires it
            ID_FIELD_NAME: serialized_pk_name,
            'Meta': type(
                'Meta',
                (RestApiModelSerializerTemplate.Meta,),
                {
                    'model': model,
                    'fields': fields
                }
            )
        }
    )
