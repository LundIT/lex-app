from dataclasses import dataclass, field
from typing import Dict, Set, List, Any, Optional
from pathlib import Path
import json
import pickle
from datetime import datetime


@dataclass
class CheckpointState:
    """Represents the state of code generation at a specific point"""
    generated_code_dict: Dict[str, tuple]
    generated_json_dict: Dict[str, str]
    completed_tests: Set[str]
    remaining_test_groups: List[Set[str]]
    test_reflections: Dict[str, List[str]]
    project_name: str
    timestamp: datetime = field(default_factory=datetime.now)

    def generate_json_tree(self):
        return {f"{k}_json": v[2] for k, v in self.generated_json_dict.items()} | {k: v[4] for k, v in self.generated_json_dict.items()}

    def generate_code_tree(self):
        return {k: v[0] for k, v in self.generated_code_dict.items()}
    def generate_tree(self):
        return {
            **self.generate_code_tree(),
            **self.generate_json_tree(),
        }

    def __post_init__(self):
        """Convert all paths to Path objects"""
        self.completed_tests = set(self.completed_tests)
        self.remaining_test_groups = [set(group) for group in self.remaining_test_groups]


class CodeGeneratorCheckpoint:
    """Manages checkpoints for code generation process"""

    def __init__(self, project_name: str, checkpoint_dir: str = "checkpoints"):
        self.project_name = project_name
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)

    async def restore_latest_checkpoint(self) -> CheckpointState:
        latest_checkpoint = self._get_latest_checkpoint()
        return self.load_checkpoint(latest_checkpoint)

    def save_checkpoint(self, state: CheckpointState) -> datetime:
        """Save current state to a checkpoint file"""
        checkpoint_path = self._get_checkpoint_path(state.timestamp)

        checkpoint_data = {
            'generated_code_dict': state.generated_code_dict,
            'generated_json_dict': state.generated_json_dict,
            'completed_tests': list(state.completed_tests),
            'remaining_test_groups': [list(group) for group in state.remaining_test_groups],
            'test_reflections': state.test_reflections,
            'project_name': state.project_name,
            'timestamp': state.timestamp.isoformat()
        }

        with open(checkpoint_path, 'wb') as f:
            pickle.dump(checkpoint_data, f)

        return state.timestamp

    def load_checkpoint(self, checkpoint_path: Optional[Path] = None) -> CheckpointState:
        """Load state from a checkpoint file"""
        if checkpoint_path is None:
            checkpoint_path = self._get_latest_checkpoint()

        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")

        with open(checkpoint_path, 'rb') as f:
            data = pickle.load(f)

        return CheckpointState(
            generated_code_dict=data['generated_code_dict'],
            generated_json_dict=data['generated_json_dict'],
            completed_tests=set(data['completed_tests']),
            remaining_test_groups=[set(group) for group in data['remaining_test_groups']],
            test_reflections=data['test_reflections'],
            project_name=data['project_name'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )

    def _get_checkpoint_path(self, timestamp: datetime) -> Path:
        """Generate checkpoint file path"""
        timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
        return self.checkpoint_dir / f"{self.project_name}_checkpoint_{timestamp_str}.pkl"

    def _get_latest_checkpoint(self) -> Path:
        """Get the most recent checkpoint file"""
        checkpoints = list(self.checkpoint_dir.glob(f"{self.project_name}_checkpoint_*.pkl"))
        if not checkpoints:
            raise FileNotFoundError(f"No checkpoints found for project {self.project_name}")
        return max(checkpoints, key=lambda p: p.stat().st_mtime)