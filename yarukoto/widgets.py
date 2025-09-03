from datetime import datetime

from classes import ResourceKind, TaskKind, Workspace
from data_processors import DataProcessor, TasksProcessor, WorkspacesProcessor
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, HorizontalGroup, VerticalGroup
from textual.coordinate import Coordinate
from textual.message import Message
from textual.widgets import Button, DataTable, Input, Label
from validators import DueDateValidator, TaskNameValidator


class AppStateMixin:
    app = None

    def get_current_workspaces(self) -> dict[str, Workspace]:
        return self.app.state.workspaces

    def get_workspace_id(self) -> str:
        return self.app.state.workspace_id

    def get_current_data_processor(self) -> type[DataProcessor]:
        if self.app.state.resource_kind == ResourceKind.TASK:
            return TasksProcessor
        else:
            return WorkspacesProcessor

    def get_task_kind(self) -> TaskKind:
        return self.app.state.task_kind

    def get_resource_kind(self) -> ResourceKind:
        return self.app.state.resource_kind

    def get_current_filter_dict(self) -> dict:
        if self.app.state.resource_kind == ResourceKind.TASK:
            workspaces = self.app.state.workspaces
            workspace_id = self.app.state.workspace_id
            current_workspace_name = workspaces[workspace_id].name

            return {
                'workspace_id': workspace_id,
                'workspace_name': current_workspace_name,
                'kind': self.app.state.task_kind,
            }
        else:
            return dict()


class Overview(DataTable, AppStateMixin):
    BINDINGS = [('ctrl+d', 'delete_resource', 'Delete Resource')]

    class OpenDeleteModal(Message):
        def __init__(self, resource_id: str, resource_name: str, resource_kind: ResourceKind) -> None:
            self.resource_id = resource_id
            self.resource_name = resource_name
            self.resource_kind = resource_kind
            super().__init__()

    def set_content(self, highlighted_row: int = 0):
        self.clear(columns=True)

        data_processor = self.get_current_data_processor()
        workspaces = self.get_current_workspaces()
        table_data = data_processor.get_table_data(workspaces, self.get_current_filter_dict())

        for column in table_data.columns:
            width = self._adjust_column_width(
                column.width,
                self.size.width,
                len(table_data.columns),
                self.parent.styles.padding,
                self.parent.styles.margin,
            )
            self.add_column(label=column.name, key=column.name, width=width)

        for row in table_data.rows:
            self.add_row(*row.values, key=row.key)

        self.border_title = table_data.title
        self.move_cursor(row=highlighted_row)

    def _adjust_column_width(self, width: int, table_width: int, number_of_columns: int, padding, margin):
        if width == 'auto':
            data_processor = self.get_current_data_processor()

            width = (
                table_width
                - (number_of_columns - 1) * (data_processor.get_default_column_width() + 3)
                - padding.left
                - padding.right
                - margin.left
                - margin.right
            )

        return width

    def on_mount(self) -> None:
        self.add_column(label='Loading Data')

    def action_delete_resource(self):
        cell_key = self.coordinate_to_cell_key(Coordinate(column=self.cursor_column, row=self.cursor_row))
        resource_id = cell_key.row_key.value
        resource_kind = self.get_resource_kind()
        resource_name = self.get_row(resource_id)[0]
        self.post_message(self.OpenDeleteModal(resource_id, resource_name, resource_kind))


class Header(HorizontalGroup, AppStateMixin):
    _label_title_dict = {
        'number_due_today': 'Due Today:  ',
        'number_current': 'Current:    ',
        'number_backlog': 'Backlog:    ',
        'number_workspaces': 'Workspaces: ',
    }

    def compose(self) -> ComposeResult:
        yield HorizontalGroup(
            VerticalGroup(
                *(
                    Label(self._generate_label_value(label_title, ''), id=label_id)
                    for label_id, label_title, in zip(self._label_title_dict.keys(), self._label_title_dict.values())
                ),
                Label(self._generate_label_value('Version:    ', 'dev'), id='version'),
                id='info',
            ),
            Container(id='commands'),
            VerticalGroup(
                Label(Text('  ______   __  __', style='#ffff66 bold')),
                Label(Text(' /_  __/  / | / /', style='#ffff66 bold')),
                Label(Text('  / /    /  |/ / ', style='#ffff66 bold')),
                Label(Text(' / /    / /|  /  ', style='#ffff66 bold')),
                Label(Text('/_/ask /_/ |_/ omi', style='#ffff66 bold')),
                id='logo',
            ),
        )

    def set_info_content(self):
        workspaces = self.get_current_workspaces()
        number_workspaces = len(workspaces)
        number_current = 0
        number_backlog = 0
        number_due_today = 0

        for workspace in workspaces.values():
            for task in workspace.task_dict.values():
                if task.kind == TaskKind.CURRENT:
                    number_current += 1
                    if task.due_datetime and (task.due_datetime.date() - datetime.now().date()).days < 0:
                        number_due_today += 1
                elif task.kind == TaskKind.BACKLOG:
                    number_backlog += 1

        label_value_dict = {
            'number_workspaces': number_workspaces,
            'number_current': number_current,
            'number_backlog': number_backlog,
            'number_due_today': number_due_today,
        }

        for label_id, label_title in self._label_title_dict.items():
            label = self.query_one(f'#{label_id}', Label)
            label.update(self._generate_label_value(label_title, label_value_dict[label_id]))

    @staticmethod
    def _generate_label_value(label_title: str, value: str | int, style='#ffff66') -> Text:
        return Text.assemble((f'{label_title}', style), str(value))


class CreateElementModal(VerticalGroup):
    def compose(self) -> ComposeResult:
        error_label = Label('', id='error_label')
        error_label.display = False
        yield error_label


class CreateTaskModal(CreateElementModal):
    def compose(self) -> ComposeResult:
        yield Input(
            placeholder='Task Name',
            restrict=r'^[ \w\-\_\/,;.:?]*$',
            max_length=200,
            id='name',
            validate_on=[],
            validators=TaskNameValidator(),
        )
        yield Input(placeholder='Priority (Between 1 and 5 - Optional)', restrict=r'^[12345]{0,1}$', id='priority')
        yield Input(
            placeholder='Due Date (yyyy/mm/dd - Optional)',
            restrict=r'^[\d/]{0,10}$',
            id='due_datetime',
            validate_on=[],
            validators=DueDateValidator(),
        )

        # spaces needed for correct coloring
        yield HorizontalGroup(Container(), Button(label='     Save     ', compact=True), Container())

        for widget in super().compose():
            yield widget
