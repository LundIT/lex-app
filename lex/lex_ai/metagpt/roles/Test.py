from datetime import datetime

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, List, Set


@dataclass
class TestInfo:
    """Represents metadata and configuration for a single test"""
    test_name: str
    test_file_path: Path
    test_json_path: Path
    test_code: Dict[str, str]
    dependencies: List[str] = None
    parameters: Optional[Dict[str, Any]] = None
    project_name: Optional[str] = None
    set_to_test: Set[str] = None
    test_output: Optional[str] = None

    def __post_init__(self):
        """Validate and process paths after initialization"""
        self.test_file_path = Path(self.test_file_path).as_posix()
        self.test_json_path = Path(self.test_json_path).as_posix()

    @property
    def test_file_name(self) -> str:
        """Get the test file name from the path"""
        return self.test_file_path.name

    @property
    def full_test_path(self) -> Path:
        """Get the complete test path including project name"""
        return Path(self.project_name) / self.test_file_path if self.project_name else self.test_file_path

    @property
    def full_json_path(self) -> Path:
        """Get the complete JSON path including project name"""
        return Path(self.project_name) / self.test_json_path if self.project_name else self.test_json_path

