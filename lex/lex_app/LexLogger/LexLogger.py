# custom_logger.py
import ast
import logging
import time

import mistune
import pandas as pd
from django.conf import settings

from lex.lex_app.LexLogger.WebSockerHandler import WebSocketHandler
from lex.lex_app.decorators.LexSingleton import LexSingleton
from lex.lex_app.logging.CalculationLog import CalculationLog
from lex_app.LexLogger.LexLogLevel import LexLogLevel


@LexSingleton
class LexLogger:
    class MarkdownBuilder:
        lexLogger = None

        def __init__(self, level, flushing=True, **kwargs):
            self.kwargs = kwargs
            self.flushing = flushing
            self.level = level
            self.parts = []
            self.det = []
            self.content = self.parts

        def builder(self, level=LexLogLevel.INFO, flushing=True, **kwargs):
            self.kwargs = {**{key: value for key, value in kwargs.items()
                           if key != "flushing" and key != "level" and key not in self.kwargs.keys()}, **self.kwargs}
            return self

        def details(self):
            self.content = self.det
            return self

        def normal(self):
            self.content = self.parts
            return self

        def _check_flush(self):
            if self.flushing:
                self.log()
            return self

        def add_heading(self, text: str, level: int = 1):
            if 1 <= level <= 6:
                self.content.append(f"{'#' * level} {text}\n")
            return self._check_flush()

        def add_paragraph(self, text: str):
            """Add a paragraph."""
            self.content.append(f"{text}\n\n")
            return self._check_flush()

        def sleep(self, seconds):
            time.sleep(seconds)
            return self

        def add_colored_text(self, text, color="black"):
            self.content.append(f"<span style='color:{color}'>{text}</span>\n\n")
            return self._check_flush()

        def add_bold(self, text: str):
            """Add bold text."""
            self.content.append(f"**{text}** ")
            return self._check_flush()

        def add_table(self, data: dict):
            """Add a table from a dictionary. Keys are the headers, values are lists of column data."""
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
            if dataframe.empty:
                return self.add_paragraph("No data available")._check_flush()

            if with_borders:
                table_md = dataframe.to_markdown(index=False)
            else:
                table_md = dataframe.to_string(index=False)

            # Add to the content
            return self.add_paragraph(table_md)._check_flush()

        def add_df_from_string(self, string_data):
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
            """Add italic text."""
            self.content.append(f"*{text}*")
            return self._check_flush()

        def add_link(self, text: str, url: str):
            """Add a link."""
            self.content.append(f"[{text}]({url})")
            return self._check_flush()

        def add_list(self, items: list, ordered: bool = False):
            """Add a list, either ordered (numbered) or unordered (bullets)."""
            if ordered:
                self.content.extend([f"{i + 1}. {item}" for i, item in enumerate(items)])
            else:
                self.content.extend([f"- {item}" for item in items])
            self.content.append("\n")
            return self._check_flush()

        def add_code_block(self, code: str, language: str = ""):
            """Add a code block with optional language syntax highlighting."""
            self.content.append(f"```{language}\n{code}\n```\n")
            return self._check_flush()

        def add_horizontal_rule(self):
            """Add a horizontal rule."""
            self.content.append("---\n")
            return self._check_flush()

        def add_blockquote(self, text: str):
            """Add blockquote."""
            self.content.append(f"> {text}\n\n")
            return self._check_flush()

        def add_image(self, alt_text: str, url: str):
            """Add an image."""
            self.content.append(f"![{alt_text}]({url})\n\n")
            return self._check_flush()

        def log(self, level: int = LexLogLevel.INFO):
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
            self.log()

        def __str__(self):
            """Return the entire Markdown text as a string."""
            return "".join(self.parts)

        def details_to_str(self):
            return "".join(self.det)

        def return_markdown(self):
            return {**{WebSocketHandler.DJANGO_TO_REACT_MAPPER[key]: value for key, value in self.kwargs.items() if key != "flushing"}, WebSocketHandler.DJANGO_TO_REACT_MAPPER['details']: self.details_to_str(),
                    WebSocketHandler.DJANGO_TO_REACT_MAPPER['message']: self.__str__(), WebSocketHandler.DJANGO_TO_REACT_MAPPER['level']: 'INFO'}

    def is_valid_markdown(self, message: str) -> bool:
        try:
            self.parser(message)
            return True
        except Exception as e:
            print(e)
            return False

    def __init__(self):
        self.logger = None
        self._initialize_logger()
        self.parser = mistune.create_markdown()
        self.MarkdownBuilder.lexLogger = self

    def _initialize_logger(self):
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
        if not self.is_valid_markdown(message):
            return

        self.logger.error(message)

    def markdown(self, level, message, **kwargs):
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
        return self.MarkdownBuilder(level=level, flushing=flushing, **kwargs)

    def markdown_warning(self, message):
        if not self.is_valid_markdown(message):
            return

        self.logger.warning(message)

    def verbose(self, message):
        self.logger.log(LexLogLevel.VERBOSE, message)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        self.logger.critical(message)


