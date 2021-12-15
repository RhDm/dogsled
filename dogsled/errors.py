"""Custom errors."""
from typing import Optional


class UserInputError(ValueError):

    """Invalid user-defined constant
    path/slide
    name/slide
    index.
    """

    def __init__(self,
                 message: str,
                 incorrect_data: Optional[str] = None) -> None:
        self.incorrect_data = incorrect_data
        self.message = message
        super().__init__(message)


class CleaningError(Exception):
    """When something went wrong during cleaning."""

    def __init__(self,
                 message: str) -> None:
        self.message = message
        super().__init__(message)


class LibVipsError(ModuleNotFoundError):
    """When libvips has to be downloaded for Linux/macOS.
    ..homebrew etc.
    """

    def __init__(self,
                 message: str) -> None:
        self.message = message
        super().__init__(message)
