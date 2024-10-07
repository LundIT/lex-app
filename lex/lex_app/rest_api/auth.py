from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class TokenObtainPairWithUserSerializer(TokenObtainPairSerializer):
    """
    Serializer for obtaining JWT tokens with additional user information.

    This serializer extends the TokenObtainPairSerializer to include the
    username of the authenticated user in the response data.

    Methods
    -------
    validate(attrs)
        Validates the input data and returns the token pair along with the
        username of the authenticated user.
    """
    def validate(self, attrs):
        """
        Validate the input data and include the username in the response.

        Parameters
        ----------
        attrs : dict
            The input data to validate.

        Returns
        -------
        dict
            The validated data including the token pair and the username.
        """
        data = super(TokenObtainPairWithUserSerializer, self).validate(attrs)
        data.update({'user': {'username': self.user.username}})
        return data


class TokenObtainPairWithUserView(TokenObtainPairView):
    """
    View for obtaining JWT tokens with additional user information.

    This view uses the TokenObtainPairWithUserSerializer to include the
    username of the authenticated user in the response data.

    Attributes
    ----------
    serializer_class : class
        The serializer class to use for validating and creating the token pair.
    """
    serializer_class = TokenObtainPairWithUserSerializer
