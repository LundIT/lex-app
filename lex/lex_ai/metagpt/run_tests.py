
from django.test.runner import DiscoverRunner
from concurrent.futures import ThreadPoolExecutor
import traceback
import sys
from io import StringIO


class CustomTestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        """Skip environment setup as it's already done"""
        pass

    def teardown_test_environment(self, **kwargs):
        """Skip environment teardown to prevent conflicts"""
        pass


def execute_tests(project_name, test_file):
    stdout = StringIO()
    stderr = StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = stdout
    sys.stderr = stderr

    try:
        runner = CustomTestRunner(
            keepdb=False,
            interactive=False,
            verbosity=3,
            debug_sql=False,
            debug_mode=True
        )

        if test_file:
            failures = runner.run_tests([f'{project_name}.Tests.{test_file.split(".")[0]}'])
        else:
            failures = runner.run_tests([f'{project_name}.Tests'])

        return {
            'success': failures == 0,
            'failures': failures,
            'output': stdout.getvalue(),
            'errors': stderr.getvalue(),
            'test_output': {
                'stdout': stdout.getvalue().split('\n'),
                'stderr': stderr.getvalue().split('\n')
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
            'test_output': {
                'stdout': stdout.getvalue().split('\n'),
                'stderr': stderr.getvalue().split('\n')
            }
        }
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def run_tests(project_name='DemoWindparkConsolidation', test_file=None):
    """Wrapper function to handle thread execution"""
    with ThreadPoolExecutor(max_workers=1) as executor:
        try:
            future = executor.submit(execute_tests, project_name=project_name, test_file=test_file)
            test_results = future.result(timeout=30)
            response_data = {
                'success': test_results['success'],
                'test_results': {
                    'failures': test_results.get('failures', 0),
                    'error': test_results.get('error'),
                    'traceback': test_results.get('traceback')
                },
                'console_output': {
                    'stdout': test_results.get('test_output', {}).get('stdout', []),
                    'stderr': test_results.get('test_output', {}).get('stderr', [])
                }
            }
            return response_data
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
def get_failed_test_classes(stderr_output):
    failed_classes = []
    for line in stderr_output:
        if ' ... ERROR' in line or ' ... FAIL' in line:
            test_info = line.split('(')[1].split(')')[0]
            class_name = test_info.split('.')[-1]
            failed_classes.append(class_name)
    return list(set(failed_classes))
