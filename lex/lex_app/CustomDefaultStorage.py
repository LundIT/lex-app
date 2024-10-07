from urllib.parse import urljoin

from django.core.files.storage import FileSystemStorage


class CustomDefaultStorage(FileSystemStorage):
    """
    Custom storage class that extends Django's FileSystemStorage to provide
    URL generation for stored files.

    Methods
    -------
    url(name)
        Generates a URL for the given file name.
    """
    def url(self, name):
        """
        Generates a URL for the given file name.

        Parameters
        ----------
        name : str
            The name of the file for which to generate the URL.

        Returns
        -------
        str
            The generated URL for the file.

        Raises
        ------
        ValueError
            If the base URL is not set, indicating the file is not accessible via a URL.
        """
        if self.base_url is None:
            raise ValueError("This file is not accessible via a URL.")
        url = name
        if url is not None:
            url = url.lstrip("/")
        return urljoin(self.base_url, url)