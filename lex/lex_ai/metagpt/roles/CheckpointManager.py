from datetime import datetime


class CheckpointManager:
    def __init__(self):
        self.checkpoints = {}
        self.checkpoint_order = []

    def save_checkpoint(self, class_set, test_result):
        checkpoint = {
            'class_set': class_set,
            'timestamp': datetime.now(),
            'test_result': test_result,
            'dependencies': self._get_dependencies(class_set)
        }
        checkpoint_id = self._generate_checkpoint_id(class_set)
        self.checkpoints[checkpoint_id] = checkpoint
        self.checkpoint_order.append(checkpoint_id)

    async def restore_from_checkpoint(self, checkpoint_id):
        if checkpoint_id not in self.checkpoints:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")
        return self.checkpoints[checkpoint_id]

    def _generate_checkpoint_id(self, class_set):
        return f"checkpoint_{len(self.checkpoint_order)}_{'-'.join(sorted(class_set))}"