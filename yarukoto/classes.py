from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from uuid import uuid4

from services import humanize_date


@dataclass
class Column:
    name: str
    width: str | int


@dataclass
class Row:
    key: str
    values: tuple


@dataclass
class TableData:
    rows: list[Row]
    columns: list[Column]
    title: str


class TaskKind(IntEnum):
    TO_DO = 1
    DONE = 2
    BACKLOG = 3

    def __str__(self):
        return f'{self.name.replace('_', '-')}'


class TaskStatus(IntEnum):
    TO_DO = 1
    DONE = 2


class ResourceKind(IntEnum):
    TASK = 1
    WORKSPACE = 2

    def __str__(self):
        return self.name


class BaseResourceClass(ABC):
    DATE_TIME_FORMAT = '%Y/%m/%d-%H:%M:%S'

    @abstractmethod
    def to_row(self) -> Row:
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass


class Task(BaseResourceClass):
    def __init__(
        self,
        name: str,
        workspace_id: str,
        priority: int = 0,
        kind: TaskKind = TaskKind.TO_DO,
        description: str = '',
        due_datetime: str = '',
        creation_datetime: str = '',
        id: str = '',
    ):
        self.name = name
        self.description = description
        self.priority = priority
        self.kind = kind
        self.status = TaskStatus.TO_DO
        self.workspace_id = workspace_id

        if id:
            self.id = id
        else:
            self.id = str(uuid4())
        if due_datetime:
            if len(due_datetime) == 10:
                due_datetime = f'{due_datetime}-23:59:59'

            self.due_datetime = datetime.strptime(due_datetime, self.DATE_TIME_FORMAT)
        else:
            self.due_datetime = ''
        if creation_datetime:
            self.creation_datetime = datetime.strptime(creation_datetime, self.DATE_TIME_FORMAT)
        else:
            self.creation_datetime = datetime.now()

    def to_row(self) -> Row:
        if self.status == TaskStatus.DONE:
            task_name = f'✓ {self.name}'
        else:
            task_name = f'[ ] {self.name}'

        return Row(
            str(self.id),
            (task_name, humanize_date(self.due_datetime), self.priority, humanize_date(self.creation_datetime)),
        )

    def to_dict(self) -> dict:
        if self.due_datetime:
            # noinspection PyUnresolvedReferences
            due_datetime = self.due_datetime.strftime(self.DATE_TIME_FORMAT)
        else:
            due_datetime = ''

        as_dict = {
            'name': self.name,
            'id': self.id,
            'priority': self.priority,
            'kind': self.kind,
            'description': self.description,
            'creation_datetime': self.creation_datetime.strftime(self.DATE_TIME_FORMAT),
            'due_datetime': due_datetime,
            'status': self.status,
            'workspace_id': self.workspace_id,
        }

        return as_dict


class Workspace(BaseResourceClass):
    def __init__(self, name: str, task_dict: dict[str, Task], id: str = '', creation_datetime: str = ''):
        self.name = name
        self.task_dict = task_dict

        if id:
            self.id = id
        else:
            self.id = str(uuid4())

        if creation_datetime:
            self.creation_datetime = datetime.strptime(creation_datetime, self.DATE_TIME_FORMAT)
        else:
            self.creation_datetime = datetime.now()

    def to_row(self) -> Row:
        return Row(
            str(self.id),
            (self.name, len(self.task_dict.keys()), len(self.task_dict.keys()), humanize_date(self.creation_datetime)),
        )

    def to_dict(self) -> dict:
        as_dict = {
            'name': self.name,
            'id': self.id,
            'creation_datetime': self.creation_datetime.strftime(self.DATE_TIME_FORMAT),
        }

        return as_dict


@dataclass
class AppState:
    workspaces: dict[str, Workspace]
    current_workspace_id: str
    current_resource_kind: ResourceKind
    current_task_kind: TaskKind
