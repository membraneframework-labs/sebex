from typing import List, Type

from sebex.log import operation, logcontext
from sebex.release.executor.cleanup import Cleanup
from sebex.release.executor.merge_pull_request import MergePullRequest
from sebex.release.executor.open_pull_request import OpenPullRequest
from sebex.release.executor.open_release_branch import OpenReleaseBranch
from sebex.release.executor.publish_package import PublishPackage
from sebex.release.executor.types import Action, Task
from sebex.release.state import ProjectState, ReleaseState, ReleaseStage

_ALL_TASK_TYPES: List[Type[Task]] = [
    OpenReleaseBranch,
    OpenPullRequest,
    MergePullRequest,
    PublishPackage,
    Cleanup,
]


def get_task_by_stage(stage: ReleaseStage) -> Type[Task]:
    for job in _ALL_TASK_TYPES:
        if job.stage == stage:
            return job
    else:
        raise ValueError(f'Stage {stage} cannot be reached by any task.')


def plan(release: ReleaseState) -> List[Task]:
    def do_plan():
        for proj in _get_current_subset(release):
            klass = get_task_by_stage(proj.stage.next)
            yield klass(project=proj)

    return list(do_plan())


def proceed(release: ReleaseState) -> Action:
    hit_breakpoint = False

    for proj in _get_current_subset(release):
        with logcontext(str(proj.project)):
            for next_stage in proj.stage:
                klass = get_task_by_stage(next_stage)
                task: Task = klass(project=proj)

                with operation(task.human_name) as reporter:
                    action = task.run()
                    proj.stage = next_stage
                    reporter(action.report())

                    if action == Action.BREAKPOINT:
                        hit_breakpoint = True

                    if action != Action.PROCEED:
                        break

    if hit_breakpoint:
        return Action.BREAKPOINT
    else:
        return Action.FINISH


def _get_current_subset(rel: ReleaseState) -> List[ProjectState]:
    return [p for p in rel.current_phase() if p.stage != ReleaseStage.DONE]
