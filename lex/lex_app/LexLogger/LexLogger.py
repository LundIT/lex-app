# custom_logger.py
import ast
import logging
import time
import uuid

import mistune
import pandas as pd
from django.conf import settings

from lex.lex_app.LexLogger.WebSockerHandler import WebSocketHandler
from lex.lex_app.decorators.LexSingleton import LexSingleton
from lex.lex_app.logging.CalculationLog import CalculationLog


class LexLogLevel:
    """
    Defines custom log levels for the LexLogger.
    """
    VERBOSE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


@LexSingleton
class LexLogger:
    """
    Custom logger class with Markdown support and various logging levels.
    """
    class MarkdownBuilder:
        """
        Builder class for creating Markdown formatted log messages.
        """
        lexLogger = None

        def __init__(self, level, flushing=True, **kwargs):
            """
            Initialize the MarkdownBuilder.

            Parameters
            ----------
            level : int
                The logging level.
            flushing : bool, optional
                Whether to flush the log after each addition, by default True.
            **kwargs
                Additional keyword arguments.
            """
            self.kwargs = kwargs
            self.flushing = flushing
            self.level = level
            self.parts = []
            self.det = []
            self.content = self.parts

        def builder(self, level=LexLogLevel.INFO, flushing=True, **kwargs):
            """
            Configure the builder.

            Parameters
            ----------
            level : int, optional
                The logging level, by default LexLogLevel.INFO.
            flushing : bool, optional
                Whether to flush the log after each addition, by default True.
            **kwargs
                Additional keyword arguments.

            Returns
            -------
            MarkdownBuilder
                The configured builder instance.
            """
            self.kwargs = {**{key: value for key, value in kwargs.items()
                           if key != "flushing" and key != "level" and key not in self.kwargs.keys()}, **self.kwargs}
            return self

        def details(self):
            """
            Switch to details content.

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            self.content = self.det
            return self

        def normal(self):
            """
            Switch to normal content.

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            self.content = self.parts
            return self

        def _check_flush(self):
            """
            Check if flushing is enabled and log the content.

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            if self.flushing:
                self.log()
            return self

        def add_heading(self, text: str, level: int = 1):
            """
            Add a heading.

            Parameters
            ----------
            text : str
                The heading text.
            level : int, optional
                The heading level (1-6), by default 1.

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            if 1 <= level <= 6:
                self.content.append(f"{'#' * level} {text}\n")
            return self._check_flush()

        def add_paragraph(self, text: str):
            """
            Add a paragraph.

            Parameters
            ----------
            text : str
                The paragraph text.

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            self.content.append(f"{text}\n\n")
            return self._check_flush()

        def sleep(self, seconds):
            """
            Sleep for a specified number of seconds.

            Parameters
            ----------
            seconds : int
                The number of seconds to sleep.

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            time.sleep(seconds)
            return self

        def add_colored_text(self, text, color="black"):
            """
            Add colored text.

            Parameters
            ----------
            text : str
                The text to color.
            color : str, optional
                The color of the text, by default "black".

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            self.content.append(f"<span style='color:{color}'>{text}</span>\n\n")
            return self._check_flush()

        def add_bold(self, text: str):
            """
            Add bold text.

            Parameters
            ----------
            text : str
                The text to make bold.

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            self.content.append(f"**{text}** ")
            return self._check_flush()

        def add_table(self, data: dict):
            """
            Add a table from a dictionary.

            Parameters
            ----------
            data : dict
                The table data where keys are headers and values are lists of column data.

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            headers = list(data.keys())
            rows = list(zip(*data.values()))

            # Add header row
            self.content.append(f"| {' | '.join(headers)} |\n")
            self.content.append(f"|{'|'.join([' --- ' for _ in headers])}|\n")

            # Add rows
            for row in rows:
                self.content.append(f"| {' | '.join(map(str, row))} |\n")
            self.content.append("\n")
            return self._check_flush()

        def add_df(self, dataframe, with_borders=True):
            """
            Add a DataFrame as a table.

            Parameters
            ----------
            dataframe : pd.DataFrame
                The DataFrame to add.
            with_borders : bool, optional
                Whether to include borders, by default True.

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            if dataframe.empty:
                return self.add_paragraph("No data available")._check_flush()

            if with_borders:
                table_md = dataframe.to_markdown(index=False)
            else:
                table_md = dataframe.to_string(index=False)

            # Add to the content
            return self.add_paragraph(table_md)._check_flush()

        def add_df_from_string(self, string_data):
            """
            Add a DataFrame from a string representation.

            Parameters
            ----------
            string_data : str
                The string representation of the DataFrame.

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            data = ast.literal_eval(string_data)

            # If the data is a list of tuples/lists, infer the number of columns
            if isinstance(data, list) and len(data) > 0:
                # Infer the number of columns dynamically from the first row of the data
                num_columns = len(data[0])
                columns = [f"Column {i + 1}" for i in range(num_columns)]

                # Create a DataFrame
                df = pd.DataFrame(data, columns=columns)
                return self.add_table(df.to_dict())._check_flush()

            return self.add_paragraph("Invalid data format")._check_flush()

        def add_italic(self, text: str):
            """
            Add italic text.

            Parameters
            ----------
            text : str
                The text to italicize.

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            self.content.append(f"*{text}*")
            return self._check_flush()

        def add_link(self, text: str, url: str):
            """
            Add a hyperlink.

            Parameters
            ----------
            text : str
                The link text.
            url : str
                The URL for the link.

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            self.content.append(f"[{text}]({url})")
            return self._check_flush()

        def add_list(self, items: list, ordered: bool = False):
            """
            Add a list.

            Parameters
            ----------
            items : list
                The list items.
            ordered : bool, optional
                Whether the list is ordered (numbered), by default False.

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            if ordered:
                self.content.extend([f"{i + 1}. {item}" for i, item in enumerate(items)])
            else:
                self.content.extend([f"- {item}" for item in items])
            self.content.append("\n")
            return self._check_flush()

        def add_code_block(self, code: str, language: str = ""):
            """
            Add a code block.

            Parameters
            ----------
            code : str
                The code to include.
            language : str, optional
                The language for syntax highlighting, by default "".

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            self.content.append(f"```{language}\n{code}\n```\n")
            return self._check_flush()

        def add_horizontal_rule(self):
            """
            Add a horizontal rule.

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            self.content.append("---\n")
            return self._check_flush()

        def add_blockquote(self, text: str):
            """
            Add a blockquote.

            Parameters
            ----------
            text : str
                The blockquote text.

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            self.content.append(f"> {text}\n\n")
            return self._check_flush()

        def add_image(self, alt_text: str, url: str):
            """
            Add an image.

            Parameters
            ----------
            alt_text : str
                The alt text for the image.
            url : str
                The URL of the image.

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            self.content.append(f"![{alt_text}]({url})\n\n")
            return self._check_flush()

        def log(self, level: int = LexLogLevel.INFO):
            """
            Log the current content.

            Parameters
            ----------
            level : int, optional
                The logging level, by default LexLogLevel.INFO.

            Returns
            -------
            MarkdownBuilder
                The builder instance.
            """
            message = self.__str__()
            if not message:
                return
            self.lexLogger.markdown(self.level, self.__str__(), **self.kwargs)
            if self.content is self.parts:
                self.parts = []
                self.det = []
                self.content = self.parts
            else:
                self.parts = []
                self.det = []
                self.content = self.det

            return self

        def __del__(self, **kwargs):
            """
            Destructor to ensure the log is flushed.
            """
            self.log()

        def __str__(self):
            """
            Return the entire Markdown text as a string.

            Returns
            -------
            str
                The Markdown text.
            """
            return "".join(self.parts)

        def details_to_str(self):
            """
            Return the details content as a string.

            Returns
            -------
            str
                The details content.
            """
            return "".join(self.det)

        def return_markdown(self):
            """
            Return the Markdown content as a dictionary.

            Returns
            -------
            dict
                The Markdown content.
            """
            return {**{WebSocketHandler.DJANGO_TO_REACT_MAPPER[key]: value for key, value in self.kwargs.items() if key != "flushing"}, WebSocketHandler.DJANGO_TO_REACT_MAPPER['details']: self.details_to_str(),
                    WebSocketHandler.DJANGO_TO_REACT_MAPPER['message']: self.__str__(), WebSocketHandler.DJANGO_TO_REACT_MAPPER['level']: 'INFO'}

    def is_valid_markdown(self, message: str) -> bool:
        """
        Check if a message is valid Markdown.

        Parameters
        ----------
        message : str
            The message to check.

        Returns
        -------
        bool
            True if the message is valid Markdown, False otherwise.
        """
        try:
            self.parser(message)
            return True
        except Exception as e:
            print(e)
            return False

    def __init__(self):
        """
        Initialize the LexLogger.
        """
        self.logger = None
        self._initialize_logger()
        self.parser = mistune.create_markdown()
        self.MarkdownBuilder.lexLogger = self

    def _initialize_logger(self):
        """
        Initialize the logger with handlers and formatters.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(LexLogLevel.VERBOSE)

        # Add custom log level
        logging.addLevelName(LexLogLevel.VERBOSE, "VERBOSE")

        # Create handlers
        console_handler = logging.StreamHandler()
        file_handler = logging.FileHandler(settings.LOG_FILE_PATH)
        websocket_handler = WebSocketHandler()

        # Set levels for handlers
        console_handler.setLevel(LexLogLevel.WARNING)
        file_handler.setLevel(LexLogLevel.VERBOSE)
        websocket_handler.setLevel(LexLogLevel.VERBOSE)

        # Create formatters and add them to handlers
        # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        websocket_handler.setFormatter(formatter)

        # Add handlers to the logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(websocket_handler)

    def markdown_error(self, message):
        """
        Log an error message in Markdown format.

        Parameters
        ----------
        message : str
            The error message.
        """
        if not self.is_valid_markdown(message):
            return

        self.logger.error(message)

    def markdown(self, level, message, **kwargs):
        """
        Log a message in Markdown format.

        Parameters
        ----------
        level : int
            The logging level.
        message : str
            The message to log.
        **kwargs
            Additional keyword arguments.
        """
        if not self.is_valid_markdown(message):
            return
        obj = CalculationLog.create(
            message=message,
            message_type=kwargs.get('message_type', "Progress"),
            trigger_name=kwargs.get('trigger_name', None),
            is_notification=kwargs.get('is_notification', False),
        )
        self.logger.log(level, message, extra={**kwargs, 'log_id': obj.id, 'calculation_id': obj.calculationId, 'class_name': obj.calculation_record, "trigger_name": obj.trigger_name, "method": obj.method})

    def builder(self, level=LexLogLevel.INFO, flushing=True, **kwargs):
        """
        Create a MarkdownBuilder instance.

        Parameters
        ----------
        level : int, optional
            The logging level, by default LexLogLevel.INFO.
        flushing : bool, optional
            Whether to flush the log after each addition, by default True.
        **kwargs
            Additional keyword arguments.

        Returns
        -------
        MarkdownBuilder
            The MarkdownBuilder instance.
        """
        return self.MarkdownBuilder(level=level, flushing=flushing, **kwargs)

    def markdown_warning(self, message):
        """
        Log a warning message in Markdown format.

        Parameters
        ----------
        message : str
            The warning message.
        """
        if not self.is_valid_markdown(message):
            return

        self.logger.warning(message)

    def verbose(self, message):
        """
        Log a verbose message.

        Parameters
        ----------
        message : str
            The verbose message.
        """
        self.logger.log(LexLogLevel.VERBOSE, message)

    def debug(self, message):
        """
        Log a debug message.

        Parameters
        ----------
        message : str
            The debug message.
        """
        self.logger.debug(message)

    def info(self, message):
        """
        Log an info message.

        Parameters
        ----------
        message : str
            The info message.
        """
        self.logger.info(message)

    def warning(self, message):
        """
        Log a warning message.

        Parameters
        ----------
        message : str
            The warning message.
        """
        self.logger.warning(message)

    def error(self, message):
        """
        Log an error message.

        Parameters
        ----------
        message : str
            The error message.
        """
        self.logger.error(message)

    def critical(self, message):
        """
        Log a critical message.

        Parameters
        ----------
        message : str
            The critical message.
        """
        self.logger.critical(message)
