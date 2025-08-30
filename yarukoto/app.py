from asyncio import sleep

from classes import ResourceKind
from data_processors import TasksProcessor, WorkspacesProcessor
from file_io import FileIO
from screens import CreateResourceScreen
from textual.app import App, ComposeResult
from textual.worker import Worker, WorkerState
from widgets import CreateTaskModal, Overview


class Yarukoto(App):
    """A Textual app to manage stopwatches."""

    TITLE = 'Yarukoto'
    ENABLE_COMMAND_PALETTE = False
    CSS_PATH = 'app.tcss'

    BINDINGS = [('ctrl+t', 'create_task', 'Create Task')]

    def __init__(self, *args, **kwargs):
        self.state = None

        super().__init__(*args, **kwargs)

    async def on_mount(self) -> None:
        self.run_worker(self.load_data())

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""

        yield Overview(cursor_type='row')

    def action_create_task(self) -> None:
        """An action to toggle dark mode."""

        if self.screen.id == "_default":
            self.push_screen(CreateResourceScreen(CreateTaskModal, ResourceKind.TASK, id='creation_screen'))

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Called when the worker state changes."""

        if event.state == WorkerState.SUCCESS and event.worker.name == 'load_data':
            overview = self.query_one(Overview)
            overview.set_content()

    def on_resize(self, event):
        if self.state:
            overview = self.query_one(Overview)
            overview.set_content()

    def on_create_resource_screen_resource_created(self, message: CreateResourceScreen.ResourceCreated):
        creation_kwargs_dict = message.creation_kwargs_dict

        if message.resource_kind == ResourceKind.TASK:
            data_processor = TasksProcessor
            creation_kwargs_dict['workspace_id'] = self.state.current_workspace_id
        elif message.resource_kind == ResourceKind.WORKSPACE:
            data_processor = WorkspacesProcessor

        created_resource = data_processor.create(**creation_kwargs_dict)
        FileIO.write_resource(created_resource)

        if message.resource_kind == ResourceKind.TASK:
            self.state.workspaces[self.state.current_workspace_id].task_dict[created_resource.id] = created_resource
        elif message.resource_kind == ResourceKind.WORKSPACE:
            self.state.workspaces[created_resource.name] = created_resource

        overview = self.query_one(Overview)
        overview.set_content()

    async def load_data(self) -> None:
        self.state = FileIO.load_data()

        # add minor delay, so that table gets mounted once and therefore the screen sice is set.
        await sleep(0.1)


if __name__ == '__main__':
    app = Yarukoto()
    app.run(mouse=False)
