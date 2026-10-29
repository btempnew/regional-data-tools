"""Resume saved work automatically; stop retry storms when nothing improves."""
import json
import os
from pathlib import Path
import subprocess


def continuation(progress, inputs, run_id):
    remaining = len(progress.get('pending_regions', []))
    remaining += progress.get('unique_postings_missing_descriptions') or 0
    if not remaining or progress.get('pipeline_error'):
        return None
    if str(inputs.get('auto_continue', 'true')).lower() == 'false':
        return None
    old = int(inputs.get('previous_remaining') or -1)
    stalls = int(inputs.get('continuation_stalls') or 0) + 1 if old >= 0 and remaining >= old else 0
    if stalls >= 3:
        print('::warning::Three continuations made no progress. Saved work is safe; inspect the source failures before resuming.')
        return None
    return {**inputs, 'resume_run_id': str(run_id), 'previous_remaining': str(remaining),
            'continuation_stalls': str(stalls), 'auto_continue': 'true'}


def main():
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    progress = json.loads(Path('progress/crawl_progress.json').read_text())
    inputs = continuation(progress, event.get('inputs') or {}, os.environ['GITHUB_RUN_ID'])
    if inputs is None:
        return
    workflow = os.environ['GITHUB_WORKFLOW_REF'].split('/.github/workflows/', 1)[1].rsplit('@', 1)[0]
    payload = {'ref': os.environ['GITHUB_REF_NAME'], 'inputs': inputs}
    subprocess.run(['gh', 'api', '--method', 'POST',
                    f'repos/{os.environ["GITHUB_REPOSITORY"]}/actions/workflows/{workflow}/dispatches',
                    '--input', '-'], input=json.dumps(payload), text=True, check=True)
    print('Continuation dispatched with all prior data and unfinished checkpoints.')


if __name__ == '__main__':
    main()
