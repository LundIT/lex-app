# from: https://stackoverflow.com/a/52700398
from rest_framework import response, status


class DestroyOneWithPayloadMixin:
    """
    The default destroy methods of Django do not return anything.
    However, we want to send the deleted instance with the response.
    """

    def destroy(self, *args, **kwargs):
        """
        Destroy the object and return the serialized data of the deleted instance.

        Parameters
        ----------
        *args
            Variable length argument list.
        **kwargs
            Arbitrary keyword arguments.

        Returns
        -------
        response.Response
            A response object containing the serialized data of the deleted instance.
        """
        serializer = self.get_serializer(self.get_object())
        super().destroy(*args, **kwargs)
        return response.Response(serializer.data, status=status.HTTP_200_OK)