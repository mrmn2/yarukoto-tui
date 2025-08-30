from abc import ABC, abstractmethod

from classes import BaseResourceClass, Column, TableData, Task, TaskKind, Workspace


class DataProcessor(ABC):
    @classmethod
    def get_table_data(cls, workspaces: dict[str, Workspace], filter_dict: dict) -> TableData:
        columns = cls._get_columns()

        resources = cls._get_resources(workspaces, filter_dict)
        resources = cls._apply_filters(resources, filter_dict)
        rows = [resource.to_row() for resource in resources]
        title = cls._get_table_title(resources, filter_dict)

        return TableData(rows, columns, title)

    @classmethod
    @abstractmethod
    def _get_table_title(cls, resources: list[BaseResourceClass], filter_dict: dict) -> str:
        pass

    @classmethod
    @abstractmethod
    def _get_columns(cls) -> list[Column]:
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

    @classmethod
    @abstractmethod
    def get_default_column_width(cls) -> int | str:
        pass


class TasksProcessor(DataProcessor):
    __DEFAULT_COLUMN_WIDTH = 12

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

        return f'{str(filter_dict.get('kind', TaskKind.TO_DO))}({workspace_name})[{len(resources)}]'

    @classmethod
    def _get_columns(cls) -> list[Column]:
        columns = [
            Column('TASK', 'auto'),
            Column('DUE', cls.__DEFAULT_COLUMN_WIDTH),
            Column('PRIORITY', cls.__DEFAULT_COLUMN_WIDTH),
            Column('CREATED', cls.__DEFAULT_COLUMN_WIDTH),
        ]

        return columns

    @staticmethod
    def _apply_filters(resources: list[Task], filter_dict: dict) -> list[Task]:
        return resources

    @staticmethod
    def _create_resource(**kwargs) -> Task:
        task = Task(**kwargs)

        return task

    @classmethod
    def get_default_column_width(cls) -> int | str:
        return cls.__DEFAULT_COLUMN_WIDTH


class WorkspacesProcessor(DataProcessor):
    __DEFAULT_COLUMN_WIDTH = 'auto'

    @classmethod
    def _get_table_title(cls, resources: list[BaseResourceClass], filter_dict: dict) -> str:
        return f'WORKSPACES[{len(resources)}])'

    @classmethod
    def _get_resources(cls, workspaces: dict[str, Workspace], filter_dict: dict) -> dict[str, Workspace]:
        return workspaces

    @classmethod
    def _get_columns(cls) -> list[Column]:
        columns = [
            Column('WORKSPACE', cls.__DEFAULT_COLUMN_WIDTH),
            Column('TASKS', cls.__DEFAULT_COLUMN_WIDTH),
            Column('BACKLOG', cls.__DEFAULT_COLUMN_WIDTH),
            Column('CREATED', cls.__DEFAULT_COLUMN_WIDTH),
        ]

        return columns

    @staticmethod
    def _apply_filters(resources: list[Workspace], filter_dict: dict) -> list[Workspace]:
        return resources

    @classmethod
    def get_default_column_width(cls) -> int | str:
        return cls.__DEFAULT_COLUMN_WIDTH

    @staticmethod
    def _create_resource(**kwargs) -> Workspace:
        return Workspace(**kwargs)
