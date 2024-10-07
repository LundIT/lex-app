"""Entry-point for the :program:`lex` umbrella command."""

import sys
def main() -> None:
    """
    Entrypoint to the ``lex`` umbrella command.

    This function imports the main function from the lex.bin.lex module
    and executes it, then exits the program with the returned status code.
    """
    from lex.bin.lex import main as _main
    sys.exit(_main())

if __name__ == '__main__':  # pragma: no cover
    main()