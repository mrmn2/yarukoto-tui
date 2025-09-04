from asyncio import sleep

from classes import BaseResource, ResourceKind, Task, Workspace
from data_processors import TasksProcessor, WorkspacesProcessor
from file_io import FileIO
from screens import CreateResourceScreen, DeleteResourceScreen, EditResourceScreen
from textual.app import App, ComposeResult
from textual.worker import Worker, WorkerState
from widgets import Header, Overview


class Yarukoto(App):
    """A Textual app to manage stopwatches."""

    TITLE = 'Yarukoto'
    ENABLE_COMMAND_PALETTE = False
    CSS_PATH = 'app.tcss'

    def __init__(self, *args, **kwargs):
        self.state = None

        super().__init__(*args, **kwargs)

    async def on_mount(self) -> None:
        self.run_worker(self._load_data())

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""

        yield Header()
        yield Overview(cursor_type='row')

    def _add_resource_to_state(self, resource: BaseResource) -> None:
        if isinstance(resource, Task):
            self.state.workspaces[self.state.workspace_id].task_dict[resource.id] = resource
        elif isinstance(resource, Workspace):
            self.state.workspaces[resource.id] = resource

    def _remove_resource_from_state(self, resource_id: str, resource_kind: ResourceKind):
        if resource_kind == ResourceKind.TASK:
            workspace_id = self.state.workspace_id
            current_workspace = self.state.workspaces[workspace_id]
            current_workspace.task_dict.pop(resource_id, None)
        elif resource_kind == ResourceKind.WORKSPACE:
            self.state.workspaces.pop(resource_id, None)

    def _get_resource_from_state(self, resource_kind: ResourceKind, resource_id: str) -> BaseResource:
        if resource_kind == ResourceKind.TASK:
            resource = self.state.workspaces[self.state.workspace_id].task_dict[resource_id]
        else:
            resource = self.state.workspaces[resource_id]

        return resource

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Called when the worker state changes."""

        if event.state == WorkerState.SUCCESS and event.worker.name == '_load_data':
            overview = self.query_one(Overview)
            overview.set_content()
            header = self.query_one(Header)
            header.set_info_content()

    def on_resize(self, _) -> None:
        if self.state:
            overview = self.query_one(Overview)
            overview.set_content()

    def on_create_resource_screen_resource_created(self, message: CreateResourceScreen.ResourceCreated) -> None:
        self._process_resource_created_edited(message.kwargs_dict, message.resource_kind)

    def on_edit_resource_screen_resource_edited(self, message: EditResourceScreen.ResourceEdited) -> None:
        resource_to_edit = self._get_resource_from_state(message.resource_kind, message.resource_id)
        kwargs_dict = message.kwargs_dict
        kwargs_dict['id'] = message.resource_id
        kwargs_dict['creation_datetime'] = resource_to_edit.get_creation_time_as_str()

        self._process_resource_created_edited(kwargs_dict, message.resource_kind)

    def on_overview_open_create_modal(self, message: Overview.OpenCreateModal) -> None:
        self.app.push_screen(CreateResourceScreen(resource_kind=message.resource_kind))

    def on_overview_open_edit_modal(self, message: Overview.OpenEditModal) -> None:
        resource = self._get_resource_from_state(message.resource_kind, message.resource_id)

        self.app.push_screen(EditResourceScreen(resource=resource))

    def on_overview_open_delete_modal(self, message: Overview.OpenDeleteModal) -> None:
        self.app.push_screen(
            DeleteResourceScreen(
                resource_id=message.resource_id,
                resource_name=message.resource_name,
                resource_kind=message.resource_kind,
            )
        )

    def on_delete_resource_screen_delete_resource(self, message: DeleteResourceScreen.DeleteResource) -> None:
        self._remove_resource_from_state(message.resource_id, message.resource_kind)
        FileIO.delete_resource(message.resource_id, message.resource_kind)

        overview = self.query_one(Overview)
        overview.set_content(highlighted_row=max(0, overview.cursor_row - 1))
        self.query_one(Header).set_info_content()

    async def _load_data(self) -> None:
        self.state = FileIO.load_data()

        # add minor delay, so that table gets mounted once and therefore the screen sice is set.
        await sleep(0.1)

    def _process_resource_created_edited(self, kwargs_dict: dict, resource_kind: ResourceKind):
        data_processor = self._get_data_processor(resource_kind)

        if resource_kind == ResourceKind.TASK:
            kwargs_dict['workspace_id'] = self.state.workspace_id

        created_resource = data_processor.create(**kwargs_dict)
        FileIO.write_resource(created_resource)
        self._add_resource_to_state(created_resource)

        overview = self.query_one(Overview)
        overview.set_content(highlighted_row=overview.cursor_row)
        self.query_one(Header).set_info_content()

    @staticmethod
    def _get_data_processor(resource_kind: ResourceKind):
        if resource_kind == ResourceKind.TASK:
            data_processor = TasksProcessor
        elif resource_kind == ResourceKind.WORKSPACE:
            data_processor = WorkspacesProcessor

        return data_processor


if __name__ == '__main__':
    app = Yarukoto()
    app.run(mouse=False)
