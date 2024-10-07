import os

from lex.lex_app.lex_models.html_report import HTMLReport


class Streamlit(HTMLReport):
    """
    Streamlit class that inherits from HTMLReport.

    This class is responsible for generating an HTML iframe
    to embed a Streamlit application.

    Methods
    -------
    get_html(user)
        Generates the HTML iframe for embedding the Streamlit app.
    """

    def get_html(self, user):
        """
        Generates the HTML iframe for embedding the Streamlit app.

        Parameters
        ----------
        user : object
            The user object (not used in the current implementation).

        Returns
        -------
        str
            The HTML string containing the iframe to embed the Streamlit app.
        """
        return f"""<iframe
              src="{os.getenv("STREAMLIT_URL", "http://localhost:8501")}/?embed=true"
              style="width:100%;border:none;height:100%"
            ></iframe>"""
