import logging


class Logger:
    """
    A class used to log messages with different levels of severity.
    """
    @staticmethod
    def logger_msg(out):
        """
        Logs a debug message with a specific format.

        Parameters
        ----------
        out : str
            The message to be logged.
        """
        logger = logging.getLogger(__name__)
        logger.debug("-----------------")
        logger.debug(out)
        logger.debug("-----------------")

    @staticmethod
    def logger_msg(out):
        """
        Logs a debug message with a specific format.

        Parameters
        ----------
        out : str
            The message to be logged.
        """
        logger = logging.getLogger(__name__)
        logger.debug("-----------------")
        logger.debug(out)
        logger.debug("-----------------")

    @staticmethod
    def subprocess_log(function_name, out):
        """
        Logs messages related to subprocess execution.

        Parameters
        ----------
        function_name : str
            The name of the function where the subprocess was called.
        out
            The output object from the subprocess, expected to have `stdout` and `stderr` attributes.
        """
        logger = logging.getLogger(__name__)
        logger.error("########################################################################")
        logger.debug(function_name)
        logger.error("########################################################################")
        logger.debug(out.stdout)
        logger.warning(out.stderr)
        logger.error("########################################################################")
        logger.error("")