from datetime import datetime


class TestState:
    def __init__(self):
        self.executed_tests = {}
        self.skipped_tests = set()
        self.failed_tests = {}
        self.current_checkpoint = None
        self.checkpoints = []

    def update_test_status(self, test_name, status, result=None):
        if status == 'skipped':
            self.skipped_tests.add(test_name)
        else:
            self.executed_tests[test_name] = {
                'status': status,
                'result': result,
                'timestamp': datetime.now()
            }

    def save_checkpoint(self, class_set, test_result, code_state):
        checkpoint = {
            'timestamp': datetime.now(),
            'class_set': class_set,
            'test_result': test_result,
            'code_state': code_state
        }
        self.checkpoints.append(checkpoint)
        self.current_checkpoint = checkpoint