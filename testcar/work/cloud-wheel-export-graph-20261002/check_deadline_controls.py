"""Two pure-memory controls of the runner's actual terminal observation logic."""
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_graph_inspection import native_exit_passes, record_exit_observation


def check_controls():
    rows = []
    for name, terminal_at, expected in [('within_deadline', 59.95, True),
                                        ('first_terminal_observation_after_deadline', 60.1, False)]:
        record = {'native_exit_code': None, 'timed_out': False}
        record_exit_observation(record, None, 59.9, 60.0, 0.0, 'native')
        record_exit_observation(record, 0, terminal_at, 60.0, 0.0, 'native')
        # Later cleanup polling must preserve the original terminal time/code.
        record_exit_observation(record, 0, 61.0, 60.0, 0.0, 'cleanup')
        assert record['native_exit_code'] == 0
        assert record['first_terminal_observed_monotonic'] == terminal_at
        assert native_exit_passes(record) is expected
        assert record['timed_out'] is (not expected)
        rows.append({'control': name, 'status': 'PASS', 'eligible_for_native_success': expected,
                     'observations': [{'code': None, 'elapsed': 59.9},
                                      {'code': 0, 'elapsed': terminal_at},
                                      {'code': 0, 'elapsed': 61.0, 'phase': 'cleanup'}],
                     'record': record})
    return {'status': 'TWO_FOCUSED_PURE_MEMORY_CONTROLS_PASS',
            'original_witness': {'loop_entered_elapsed': 59.9, 'first_terminal_observed_elapsed': 60.1,
                                 'exit_code': 0, 'old_loop_incorrect_timed_out': False,
                                 'cause': 'The old while-condition poll saw exit0 after wait and skipped the deadline body'},
            'controls': rows, 'native_execution': False}


if __name__ == '__main__':
    result = check_controls()
    print(json.dumps({'status': result['status'], 'controls': len(result['controls'])}))
