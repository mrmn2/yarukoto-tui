from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from uuid import uuid4

from services import humanize_date


@dataclass
class Row:
    key: str
    values: tuple


@dataclass
class TableData:
    rows: list[Row]
    column_names: list[str]
    title: str


class TaskKind(IntEnum):
    CURRENT = 1
    COMPLETED = 2
    BACKLOG = 3

    def __str__(self):
        return f'{self.name.replace('_', '-')}'


class ResourceKind(IntEnum):
    TASK = 1
    WORKSPACE = 2

    def __str__(self):
        return self.name


class BaseResource(ABC):
    _DATE_TIME_FORMAT = '%Y/%m/%d-%H:%M:%S'
    _DATE_FORMAT = '%Y/%m/%d'

    @abstractmethod
    def to_row(self) -> Row:
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    @property
    @abstractmethod
    def creation_datetime(self):
        # return some dummy value, function will be overwritten by children
        return datetime(2025, 9, 2)

    @classmethod
    def get_date_as_str(cls, date_time: datetime):
        return date_time.strftime(cls._DATE_FORMAT)

    def get_creation_time_as_str(self):
        return self.creation_datetime.strftime(self._DATE_TIME_FORMAT)


class Task(BaseResource):
    def __init__(
        self,
        name: str,
        workspace_id: str,
        priority: int = 0,
        kind: TaskKind = TaskKind.CURRENT,
        description: str = '',
        due_datetime: str = '',
        creation_datetime: str = '',
        id: str = '',
    ):
        self.name = name
        self.description = description
        self.priority = priority
        self.kind = kind
        self.workspace_id = workspace_id

        if id:
            self.id = id
        else:
            self.id = str(uuid4())
        if due_datetime:
            if len(due_datetime) == 10:
                due_datetime = f'{due_datetime}-23:59:59'

            self.due_datetime = datetime.strptime(due_datetime, self._DATE_TIME_FORMAT)
        else:
            self.due_datetime = ''
        if creation_datetime:
            self._creation_datetime = datetime.strptime(creation_datetime, self._DATE_TIME_FORMAT)
        else:
            self._creation_datetime = datetime.now()

    @property
    def creation_datetime(self):
        return self._creation_datetime

    def to_row(self) -> Row:
        return Row(
            self.id,
            (self.name, self.priority, humanize_date(self.due_datetime), humanize_date(self.creation_datetime)),
        )

    def to_dict(self) -> dict:
        if self.due_datetime:
            # noinspection PyUnresolvedReferences
            due_datetime = self.due_datetime.strftime(self._DATE_TIME_FORMAT)
        else:
            due_datetime = ''

        as_dict = {
            'name': self.name,
            'id': self.id,
            'priority': self.priority,
            'kind': self.kind,
            'description': self.description,
            'creation_datetime': self.creation_datetime.strftime(self._DATE_TIME_FORMAT),
            'due_datetime': due_datetime,
            'workspace_id': self.workspace_id,
        }

        return as_dict


class Workspace(BaseResource):
    def __init__(self, name: str, task_dict: dict[str, Task] = None, id: str = '', creation_datetime: str = ''):
        self.name = name
        if id:
            self.id = id
        else:
            self.id = str(uuid4())
        if task_dict:
            self.task_dict = task_dict
        else:
            self.task_dict = dict()

        if creation_datetime:
            self._creation_datetime = datetime.strptime(creation_datetime, self._DATE_TIME_FORMAT)
        else:
            self._creation_datetime = datetime.now()

    @property
    def creation_datetime(self):
        return self._creation_datetime

    def to_row(self) -> Row:
        return Row(
            self.id,
            (self.name, len(self.task_dict.keys()), len(self.task_dict.keys()), humanize_date(self.creation_datetime)),
        )

    def to_dict(self) -> dict:
        as_dict = {
            'name': self.name,
            'id': self.id,
            'creation_datetime': self.creation_datetime.strftime(self._DATE_TIME_FORMAT),
        }

        return as_dict


class AppState:
    def __init__(
        self,
        workspaces: dict[str, Workspace],
        workspace_id: str,
        resource_kind: ResourceKind = ResourceKind.TASK,
        task_kind: TaskKind = TaskKind.CURRENT,
    ):
        self.workspaces = workspaces
        self.workspace_id = workspace_id
        self.resource_kind = resource_kind
        self.task_kind = task_kind
