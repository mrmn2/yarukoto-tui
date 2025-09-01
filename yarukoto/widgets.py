from classes import ResourceKind
from data_processors import TasksProcessor, WorkspacesProcessor
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, HorizontalGroup, VerticalGroup
from textual.coordinate import Coordinate
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, DataTable, Input, Label
from validators import DueDateValidator, TaskNameValidator


class AppStateMixin:
    app = None

    def get_current_workspaces(self):
        return self.app.state.workspaces

    def get_current_workspace_id(self):
        return self.app.state.current_workspace_id

    def get_current_data_processor(self):
        if self.app.state.current_resource_kind == ResourceKind.TASK:
            return TasksProcessor
        else:
            return WorkspacesProcessor

    def get_current_task_kind(self):
        return self.app.state.current_task_kind

    def get_current_resource_kind(self):
        return self.app.state.current_resource_kind

    def get_current_filter_dict(self):
        if self.app.state.current_resource_kind == ResourceKind.TASK:
            workspaces = self.app.state.workspaces
            current_workspace_id = self.app.state.current_workspace_id
            current_workspace_name = workspaces[current_workspace_id].name

            return {
                'workspace_id': current_workspace_id,
                'workspace_name': current_workspace_name,
                'kind': self.app.state.current_task_kind,
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

    def set_content(self):
        self.clear(columns=True)

        data_processor = self.get_current_data_processor()
        workspaces = self.get_current_workspaces()
        table_data = data_processor.get_table_data(workspaces, self.get_current_filter_dict())

        for column in table_data.columns:
            width = self.adjust_column_width(
                column.width,
                self.size.width,
                len(table_data.columns),
                self.parent.styles.padding,
                self.parent.styles.margin,
            )
            self.add_column(label=column.name, key=column.name, width=width)

        for row in table_data.rows:
            self.add_row(*row.values, key=row.key)
        # self.add_rows(row.values for row in table_data.rows)
        self.border_title = table_data.title

    def adjust_column_width(self, width: int, table_width: int, number_of_columns: int, padding, margin):
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
        resource_kind = self.get_current_resource_kind()
        resource_name = self.get_row(resource_id)[0]
        self.post_message(self.OpenDeleteModal(resource_id, resource_name, resource_kind))


class Header(HorizontalGroup, AppStateMixin):
    number_workspaces = reactive(default='', init=False)
    number_due_today = reactive(default='')
    number_current = reactive(default='')
    number_backlog = reactive(default='')
    version = reactive(default='dev')

    def compose(self) -> ComposeResult:
        style = '#ffff66'
        label_names = ['Workspaces: ', 'Due Today:  ', 'Current:    ', 'Backlog:    ', 'Version:    ']
        label_values = [
            self.number_workspaces,
            self.number_due_today,
            self.number_current,
            self.number_backlog,
            self.version,
        ]
        label_ids = ['number_workspaces', 'number_due_today', 'number_current', 'number_backlog', 'version']

        yield HorizontalGroup(
            VerticalGroup(
                *(
                    Label(Text.assemble((text, style), str(value)), id=label_id)
                    for text, value, label_id in zip(label_names, label_values, label_ids)
                ),
                id='info'
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

    @staticmethod
    def generate_label_value(value: str | int) -> Text:
        return Text.assemble(('Workspaces: ', '#ffff66'), str(value))

    def watch_number_workspaces(self, number_workspaces: str) -> None:
        self.query_one('#number_workspaces', Label).update(number_workspaces)


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
