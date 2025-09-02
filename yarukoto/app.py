from asyncio import sleep

from classes import BaseResourceClass, ResourceKind, Task, Workspace
from data_processors import TasksProcessor, WorkspacesProcessor
from file_io import FileIO
from screens import CreateResourceScreen, DeleteResourceScreen
from textual.app import App, ComposeResult
from textual.worker import Worker, WorkerState
from widgets import CreateTaskModal, Header, Overview


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

        yield Header()
        yield Overview(cursor_type='row')

    def add_resource_to_state(self, resource: BaseResourceClass) -> None:
        if isinstance(resource, Task):
            self.state.workspaces[self.state.workspace_id].task_dict[resource.id] = resource
        elif isinstance(resource, Workspace):
            self.state.workspaces[resource.id] = resource

    def remove_resource_from_state(self, resource_id: str, resource_kind: ResourceKind):
        if resource_kind == ResourceKind.TASK:
            workspace_id = self.state.workspace_id
            current_workspace = self.state.workspaces[workspace_id]
            current_workspace.task_dict.pop(resource_id, None)
        elif resource_kind == ResourceKind.WORKSPACE:
            self.state.workspaces.pop(resource_id, None)

    def action_create_task(self) -> None:
        """An action to toggle dark mode."""

        if self.screen.id == "_default":
            self.push_screen(CreateResourceScreen(CreateTaskModal, ResourceKind.TASK))

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Called when the worker state changes."""

        if event.state == WorkerState.SUCCESS and event.worker.name == 'load_data':
            overview = self.query_one(Overview)
            overview.set_content()
            header = self.query_one(Header)
            header.set_info_content()

    def on_resize(self, event) -> None:
        if self.state:
            overview = self.query_one(Overview)
            overview.set_content()

    def on_create_resource_screen_resource_created(self, message: CreateResourceScreen.ResourceCreated) -> None:
        creation_kwargs_dict = message.creation_kwargs_dict

        if message.resource_kind == ResourceKind.TASK:
            data_processor = TasksProcessor
            creation_kwargs_dict['workspace_id'] = self.state.workspace_id
        elif message.resource_kind == ResourceKind.WORKSPACE:
            data_processor = WorkspacesProcessor

        created_resource = data_processor.create(**creation_kwargs_dict)
        FileIO.write_resource(created_resource)
        self.add_resource_to_state(created_resource)

        overview = self.query_one(Overview)
        overview.set_content()
        header = self.query_one(Header)
        header.set_info_content()

    def on_overview_open_delete_modal(self, message: Overview.OpenDeleteModal) -> None:
        self.app.push_screen(
            DeleteResourceScreen(
                resource_id=message.resource_id,
                resource_name=message.resource_name,
                resource_kind=message.resource_kind,
                id='delete_resource',
            )
        )

    def on_delete_resource_screen_delete_resource(self, message: DeleteResourceScreen.DeleteResource) -> None:
        self.remove_resource_from_state(message.resource_id, message.resource_kind)
        FileIO.delete_resource(message.resource_id, message.resource_kind)
        overview = self.query_one(Overview)
        overview.set_content()
        header = self.query_one(Header)
        header.set_info_content()

    async def load_data(self) -> None:
        self.state = FileIO.load_data()

        # add minor delay, so that table gets mounted once and therefore the screen sice is set.
        await sleep(0.1)


if __name__ == '__main__':
    app = Yarukoto()
    app.run(mouse=False)
