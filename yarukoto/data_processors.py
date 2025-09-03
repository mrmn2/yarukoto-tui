from abc import ABC, abstractmethod

from classes import BaseResourceClass, TableData, Task, TaskKind, Workspace


class DataProcessor(ABC):
    @classmethod
    def get_table_data(cls, workspaces: dict[str, Workspace], filter_dict: dict) -> TableData:
        column_names = cls._get_column_names()

        resources = cls._get_resources(workspaces, filter_dict)
        resources = cls._apply_filters(resources, filter_dict)
        rows = [resource.to_row() for resource in resources]
        title = cls._get_table_title(resources, filter_dict)

        return TableData(rows, column_names, title)

    @classmethod
    @abstractmethod
    def _get_table_title(cls, resources: list[BaseResourceClass], filter_dict: dict) -> str:
        pass

    @classmethod
    @abstractmethod
    def _get_column_names(cls) -> list[str]:
        pass

    @classmethod
    @abstractmethod
    def _get_resources(cls, workspaces: dict[str, Workspace], filter_dict: dict) -> list[BaseResourceClass]:
        pass

    @staticmethod
    @abstractmethod
    def _apply_filters(resources: list[BaseResourceClass], filter_dict: dict) -> list[BaseResourceClass]:
        pass

    @classmethod
    def create(cls, **kwargs) -> BaseResourceClass:
        created_resource = cls._create_resource(**kwargs)

        return created_resource

    @staticmethod
    @abstractmethod
    def _create_resource(cls, **kwargs) -> BaseResourceClass:
        pass


class TasksProcessor(DataProcessor):
    @classmethod
    def _get_resources(cls, workspaces: dict[str, Workspace], filter_dict: dict) -> list[Task]:
        if filter_dict.get('workspace_id'):
            workspaces = [workspaces[filter_dict['workspace_id']]]
        else:
            workspaces = workspaces.values()

        tasks = []

        for workspace in workspaces:
            tasks.extend(workspace.task_dict.values())

        return tasks

    @classmethod
    def _get_table_title(cls, resources: list[BaseResourceClass], filter_dict: dict) -> str:
        workspace_name = filter_dict.get('workspace_name', 'all')
        task_kind = filter_dict.get('task_kind', TaskKind.CURRENT)

        return f'{str(filter_dict.get('kind', task_kind))}({workspace_name})[{len(resources)}]'

    @classmethod
    def _get_column_names(cls) -> list[str]:
        column_names = ['TASK', 'PRIORITY', 'DUE', 'CREATED']

        return column_names

    @staticmethod
    def _apply_filters(resources: list[Task], filter_dict: dict) -> list[Task]:
        return resources

    @staticmethod
    def _create_resource(**kwargs) -> Task:
        task = Task(**kwargs)

        return task


class WorkspacesProcessor(DataProcessor):
    @classmethod
    def _get_table_title(cls, resources: list[BaseResourceClass], filter_dict: dict) -> str:
        return f'WORKSPACES[{len(resources)}])'

    @classmethod
    def _get_resources(cls, workspaces: dict[str, Workspace], filter_dict: dict) -> dict[str, Workspace]:
        return workspaces

    @classmethod
    def _get_column_names(cls) -> list[str]:
        column_names = ['WORKSPACE', 'TASKS', 'BACKLOG', 'CREATED']

        return column_names

    @staticmethod
    def _apply_filters(resources: list[Workspace], filter_dict: dict) -> list[Workspace]:
        return resources

    @staticmethod
    def _create_resource(**kwargs) -> Workspace:
        return Workspace(**kwargs)
