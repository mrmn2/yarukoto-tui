from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from uuid import uuid4


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


class TaskKind(Enum):
    TO_DO = auto()
    DONE = auto()
    BACKLOG = auto()

    def __str__(self):
        return f'{self.name.replace('_', '-')}'


class TaskStatus(Enum):
    TO_DO = auto()
    DONE = auto()


class ResourceKind(Enum):
    TASK = auto()
    WORKSPACE = auto()

    def __str__(self):
        return self.name


class BaseResourceClass(ABC):
    @abstractmethod
    def to_row(self) -> Row:
        pass

    @classmethod
    def get_columns(cls) -> list[Column]:
        pass


class Task(BaseResourceClass):
    def __init__(
        self,
        name: str,
        priority: int = 0,
        kind: TaskKind = TaskKind.TO_DO,
        description: str = '',
        due_datetime: str = '',
        id: str = '',
    ):
        self.name = name
        if id:
            self.id = id
        else:
            self.id = uuid4()
        self.description = description
        if due_datetime:
            self.due_datetime = datetime.strptime(due_datetime, '%Y/%m/%d')
        else:
            self.due_datetime = ''
        self.priority = priority
        self.kind = kind
        self.creation_datetime = datetime.now()
        self.status = TaskStatus.TO_DO

    # --------------------------------------------------------------------------------------
    # humanize

    def to_row(self) -> Row:
        if self.status == TaskStatus.DONE:
            task_name = f'✓ {self.name}'
        else:
            task_name = f'□ {self.name}'

        return Row(str(self.id), (task_name, self.due_datetime, self.priority, self.creation_datetime))


class Workspace(BaseResourceClass):
    def __init__(self, name: str, task_dict: dict[str, Task], id: str = ''):
        self.name = name
        if id:
            self.id = id
        else:
            self.id = uuid4()
        self.task_dict = task_dict
        self.creation_datetime = datetime.now()

    def to_row(self) -> Row:
        return Row(
            str(self.id), (self.name, len(self.task_dict.keys()), len(self.task_dict.keys()), self.creation_datetime)
        )
