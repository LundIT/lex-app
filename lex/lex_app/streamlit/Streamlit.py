import os

from lex.lex_app.lex_models.html_report import HTMLReport


class Streamlit(HTMLReport):
    """
    Streamlit class that inherits from HTMLReport.

    This class is responsible for generating an HTML iframe to embed a Streamlit app.
    """

    def get_html(self, user):
        """
        Generate HTML iframe to embed a Streamlit app.

        Parameters
        ----------
        user : object
            The user object (not used in this method).

        Returns
        -------
        str
            HTML string containing an iframe to embed the Streamlit app.
        """
        return f"""<iframe
              src="{os.getenv("STREAMLIT_URL", "http://localhost:8501")}/?embed=true"
              style="width:100%;border:none;height:100%"
            ></iframe>"""
