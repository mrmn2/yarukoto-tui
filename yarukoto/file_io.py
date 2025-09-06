import json
from os import environ
from pathlib import Path

from classes import AppState, BaseResource, ResourceKind, Task, TaskKind, Workspace


class FileIO:
    INDENT = 4

    @staticmethod
    def _get_app_path() -> Path:
        return Path(environ.get('HOME')) / '.tasknomi'

    @classmethod
    def load_data(cls) -> AppState:
        app_path = cls._get_app_path()
        config_file_path = app_path / 'config.json'
        workspaces_file_path = app_path / 'workspaces.json'

        if not (app_path.exists() and config_file_path.exists() and workspaces_file_path.exists()):
            app_state = cls._create_first_time_data()
        else:
            app_state = cls._read()

        return app_state

    @classmethod
    def write_resource(cls, resource: BaseResource) -> None:
        if isinstance(resource, Task):
            cls._write_task_to_file(resource)
        elif isinstance(resource, Workspace):
            cls._write_workspace_to_file(resource)

    @classmethod
    def delete_resource(cls, resource_id: str, resource_kind: ResourceKind) -> None:
        if resource_kind == ResourceKind.TASK:
            cls._delete_task(resource_id)
        elif resource_kind == ResourceKind.WORKSPACE:
            cls._delete_workspace(resource_id)

    @classmethod
    def _read(cls) -> AppState:
        app_path = cls._get_app_path()

        config_file_path = app_path / 'config.json'
        workspace_file_path = app_path / 'workspaces.json'

        with open(config_file_path, 'r') as f:
            config_dict = json.load(f)

        with open(workspace_file_path, 'r') as f:
            workspaces_list = json.load(f)
            workspaces = {
                workspace['id']: Workspace(
                    name=workspace['name'],
                    id=workspace['id'],
                    task_dict=dict(),
                    creation_datetime=workspace['creation_datetime'],
                )
                for workspace in workspaces_list
            }

        for workspace_id, workspace in workspaces.items():
            for task_file_path in (app_path / workspace_id).iterdir():
                if task_file_path.is_file():
                    with open(task_file_path, 'r') as f:
                        task_dict = json.load(f)
                        task = Task(
                            name=task_dict['name'],
                            id=task_dict['id'],
                            kind=TaskKind(task_dict['kind']),
                            description=task_dict['description'],
                            priority=task_dict['priority'],
                            workspace_id=task_dict['workspace_id'],
                            creation_datetime=task_dict['creation_datetime'],
                            due_datetime=task_dict['due_datetime'],
                        )

                        workspace.task_dict[task.id] = task

        app_state = AppState(
            workspaces=workspaces,
            workspace_id=config_dict['workspace_id'],
            task_kind=TaskKind(config_dict['task_kind']),
            resource_kind=ResourceKind(config_dict['resource_kind']),
        )

        return app_state

    @classmethod
    def _write_task_to_file(cls, task: Task) -> None:
        file_path = cls._get_app_path() / task.workspace_id / f'{task.id}.json'

        if not file_path.exists():
            file_path.touch()

        with open(file_path, 'w') as f:
            json.dump(task.to_dict(), f, indent=4)

    @classmethod
    def _write_workspace_to_file(cls, workspace: Workspace) -> None:
        pass

    @classmethod
    def _create_first_time_data(cls) -> AppState:
        app_path = cls._get_app_path()
        config_file_path = app_path / 'config.json'
        workspaces_file_path = app_path / 'workspaces.json'

        app_path.mkdir(exist_ok=True)
        config_file_path.touch(exist_ok=True)
        workspaces_file_path.touch(exist_ok=True)

        default_workspace = Workspace('default', dict())
        default_workspace_task_path = app_path / default_workspace.id
        default_workspace_task_path.mkdir(exist_ok=True)

        app_state = AppState(
            workspaces={default_workspace.id: default_workspace},
            workspace_id=default_workspace.id,
        )

        initial_config_dict = {
            'workspace_id': app_state.workspace_id,
            'resource_kind': app_state.task_kind,
            'task_kind': app_state.task_kind,
        }

        with open(config_file_path, 'w') as f:
            json.dump(initial_config_dict, f, indent=cls.INDENT)

        with open(workspaces_file_path, 'w') as f:
            json.dump([default_workspace.to_dict()], f, indent=cls.INDENT)

        return app_state

    @classmethod
    def _delete_task(cls, resource_id: str):
        app_path = cls._get_app_path()

        for workspace_dir in app_path.iterdir():
            if workspace_dir.is_dir():
                try:
                    (workspace_dir / f'{resource_id}.json').unlink()
                except FileNotFoundError:
                    pass

    @classmethod
    def _delete_workspace(cls, resource_id: str):
        pass
