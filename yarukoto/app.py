from asyncio import sleep
from dataclasses import dataclass
from datetime import datetime

from classes import ResourceKind, TaskKind, Workspace
from data_processors import DataProcessor, TasksProcessor, WorkspacesProcessor
from textual.app import App, Binding, ComposeResult
from textual.containers import VerticalGroup
from textual.message import Message
from textual.screen import Screen
from textual.validation import ValidationResult, Validator
from textual.widgets import DataTable, Input, Label
from textual.worker import Worker, WorkerState


class AppStateMixin:
    app = None

    def get_app_workspaces(self):
        return self.app.state.workspaces

    def get_app_current_workspace_name(self):
        return self.app.state.current_workspace_name

    def get_app_data_processor(self):
        return self.app.state.data_processor


class Overview(DataTable, AppStateMixin):
    def set_content(self):
        self.clear(columns=True)

        data_processor = self.get_app_data_processor()
        workspaces = self.get_app_workspaces()
        current_workspace_name = self.get_app_current_workspace_name()

        table_data = data_processor.get_table_data(
            workspaces, {'workspace_name': current_workspace_name, 'kind': TaskKind.TO_DO}
        )

        for column in table_data.columns:
            width = self.adjust_column_width(
                column.width,
                self.size.width,
                len(table_data.columns),
                self.parent.styles.padding,
                self.parent.styles.margin,
            )
            self.add_column(label=column.name, key=column.name, width=width)

        self.add_rows(row.values for row in table_data.rows)
        self.border_title = table_data.title

    def adjust_column_width(self, width: int, table_width: int, number_of_columns: int, padding, margin):
        if width == 'auto':
            data_processor = self.get_app_data_processor()

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


class CreateElementModal(VerticalGroup):
    def compose(self) -> ComposeResult:
        error_label = Label('', id='error_label')
        error_label.display = False
        yield error_label


class CreateTaskModal(CreateElementModal):
    def compose(self) -> ComposeResult:
        yield Input(
            placeholder='Task Name',
            restrict=r'^[ \w-]*$',
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

        for widget in super().compose():
            yield widget


class TaskNameValidator(Validator):
    def validate(self, value: str) -> ValidationResult:
        if value:
            return self.success()
        else:
            return self.failure('You need to set a task name!')


class DueDateValidator(Validator):
    def validate(self, value: str) -> ValidationResult:
        # ----------------------
        # needs to be in the future
        try:
            if value:
                datetime.strptime(value, '%Y/%m/%d')
        except ValueError:
            return self.failure('Date is not in the correct format!')
        else:
            return self.success()


class CreateResourceScreen(Screen):
    BINDINGS = [
        ('escape', 'cancel_create_resource', 'Cancel Resource Creation'),
        Binding('down', 'app.focus_next', 'Focus Next', priority=True),
        Binding('up', 'app.focus_previous', 'Focus Previous', priority=True),
        Binding('enter', 'submit_create_resource', 'Submit Resource Creation', priority=True),
    ]

    # to be changed
    def __init__(self, create_modal_class: type[CreateElementModal], resource_kind: ResourceKind):
        super().__init__()

        self.create_modal_class = create_modal_class
        self.resource_kind = resource_kind

    def compose(self) -> ComposeResult:
        # noinspection PyCallingNonCallable
        create_modal = self.create_modal_class()
        create_modal.border_title = f'CREATE {str(self.resource_kind)}'

        yield create_modal

    class ResourceCreated(Message):
        """Color selected message."""

        def __init__(self, creation_kwargs_dict: dict, resource_kind: ResourceKind) -> None:
            self.creation_kwargs_dict = creation_kwargs_dict
            self.resource_kind = resource_kind
            super().__init__()

    def action_cancel_create_resource(self) -> None:
        self.dismiss(True)

    def action_submit_create_resource(self) -> None:
        creation_inputs = self.query(Input)

        creation_kwargs_dict = {creation_input.id: creation_input.value for creation_input in creation_inputs}
        # send message to create

        for creation_input in creation_inputs:
            input_value = creation_input.value.strip()
            validation_result = creation_input.validate(input_value)

            if validation_result and validation_result != ValidationResult.success():
                error_label = self.query_one('#error_label', Label)
                error_label.update(validation_result.failures[0].description)
                error_label.display = True
                return

        # self.data_processor.create(**creation_kwargs_dict)
        self.post_message(self.ResourceCreated(creation_kwargs_dict, self.resource_kind))
        self.dismiss(True)


class Yarukoto(App):
    """A Textual app to manage stopwatches."""

    TITLE = 'Yarukoto'
    ENABLE_COMMAND_PALETTE = False
    CSS_PATH = 'app.tcss'

    BINDINGS = [('ctrl+t', 'create_task', 'Create Task')]

    def __init__(self, *args, **kwargs):
        self.state = AppState(workspaces=dict(), current_workspace_name='default', data_processor=TasksProcessor)

        super().__init__(*args, **kwargs)

    async def on_mount(self) -> None:
        self.run_worker(self.load_data())

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""

        yield Overview(cursor_type='row')

    def action_create_task(self) -> None:
        """An action to toggle dark mode."""

        self.push_screen(CreateResourceScreen(CreateTaskModal, ResourceKind.TASK))

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Called when the worker state changes."""

        if event.state == WorkerState.SUCCESS and event.worker.name == 'load_data':
            overview = self.query_one(Overview)
            overview.set_content()

    def on_resize(self, event):
        if self.state.workspaces:
            overview = self.query_one(Overview)
            overview.set_content()

    def on_create_resource_screen_resource_created(self, message: CreateResourceScreen.ResourceCreated):
        if message.resource_kind == ResourceKind.TASK:
            data_processor = TasksProcessor
        elif message.resource_kind == ResourceKind.WORKSPACE:
            data_processor = WorkspacesProcessor

        created_resource = data_processor.create(**message.creation_kwargs_dict)

        if message.resource_kind == ResourceKind.TASK:
            self.state.workspaces[self.state.current_workspace_name].task_dict[created_resource.id] = created_resource
        elif message.resource_kind == ResourceKind.WORKSPACE:
            self.state.workspaces[created_resource.name] = created_resource

        overview = self.query_one(Overview)
        overview.set_content()

    async def load_data(self) -> None:
        # task_1 = Task('✓ Update Kubernetes Version on preprod', due_datetime='2025/08/26', priority=1)
        # task_2 = Task('□ Develop PoC of YaruKoto', due_datetime='2025/08/28', priority=0)
        # task_3 = Task('□ Implement feature a and b to do', due_datetime='2025/09/26', priority=5)
        # tasks = [task_1, task_2, task_3]

        workspace = Workspace('default', dict())
        self.state.workspaces = {workspace.name: workspace}

        await sleep(0.5)


@dataclass
class AppState:
    workspaces: dict[str, Workspace]
    current_workspace_name: str
    data_processor: type[DataProcessor]


if __name__ == '__main__':
    app = Yarukoto()
    app.run(mouse=False)
