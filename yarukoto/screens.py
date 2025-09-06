from classes import BaseResource, ResourceKind, Task, Workspace
from textual.app import Binding, ComposeResult
from textual.containers import Container, Grid
from textual.message import Message
from textual.screen import ModalScreen
from textual.validation import ValidationResult
from textual.widgets import Button, Input, Label
from widgets import TaskModal, WorkspaceModal


class TaskNomiModalScreen(ModalScreen):
    def action_limited_focus_next(self) -> None:
        current_index = self.focus_chain.index(self.focused)

        if current_index + 1 < len(self.focus_chain):
            self.focus_next()

    def action_limited_focus_previous(self) -> None:
        current_index = self.focus_chain.index(self.focused)

        if current_index > 0:
            self.focus_previous()


class BaseResourceScreen(TaskNomiModalScreen):
    BINDINGS = [
        ('escape', 'cancel', 'Cancel'),
        Binding('down', 'limited_focus_next', 'Focus Next', priority=True),
        Binding('up', 'limited_focus_previous', 'Focus Previous', priority=True),
        Binding('ctrl+s', 'submit', 'Submit', priority=True),
    ]

    def _process_modal_inputs(self) -> dict:
        modal_inputs = self.query(Input)

        input_kwargs_dict = {modal_input.id: modal_input.value for modal_input in modal_inputs}

        for modal_input in modal_inputs:
            input_value = modal_input.value.strip()
            validation_result = modal_input.validate(input_value)

            if validation_result and validation_result != ValidationResult.success():
                error_label = self.query_one('#error_label', Label)
                error_label.update(validation_result.failures[0].description)
                error_label.display = True
                return dict()

        return input_kwargs_dict

    def _submit(self):
        pass

    def action_cancel(self) -> None:
        self.dismiss(True)

    def action_submit(self) -> None:
        self._submit()

    def on_button_pressed(self, _) -> None:
        self._submit()


class CreateResourceScreen(BaseResourceScreen):
    class ResourceCreated(Message):
        def __init__(self, kwargs_dict: dict, resource_kind: ResourceKind) -> None:
            self.kwargs_dict = kwargs_dict
            self.resource_kind = resource_kind
            super().__init__()

    def __init__(self, resource_kind: ResourceKind, id: str = 'creation_screen'):
        super().__init__(id=id)
        self.resource_kind = resource_kind

    def compose(self) -> ComposeResult:
        if self.resource_kind == ResourceKind.TASK:
            create_modal = TaskModal()
        else:
            create_modal = WorkspaceModal()
        create_modal.border_title = f'CREATE {str(self.resource_kind)}'

        yield create_modal

    def _submit(self) -> None:
        input_kwargs_dict = self._process_modal_inputs()

        self.post_message(self.ResourceCreated(input_kwargs_dict, self.resource_kind))
        self.dismiss(True)


class EditResourceScreen(BaseResourceScreen):
    class ResourceEdited(Message):
        def __init__(self, kwargs_dict: dict, resource_kind: ResourceKind, resource_id: str) -> None:
            self.kwargs_dict = kwargs_dict
            self.resource_kind = resource_kind
            self.resource_id = resource_id
            super().__init__()

    def __init__(self, resource: BaseResource, id: str = 'edit_screen'):
        super().__init__(id=id)
        self.resource = resource

    def compose(self) -> ComposeResult:
        if isinstance(self.resource, Task):
            create_modal = TaskModal(self.resource)
            create_modal.border_title = 'EDIT TASK'
        elif isinstance(self.resource, Workspace):
            create_modal = WorkspaceModal(self.resource)
            create_modal.border_title = 'EDIT WORKSPACE'
        else:
            create_modal = None

        yield create_modal

    def _submit(self) -> None:
        input_kwargs_dict = self._process_modal_inputs()

        if isinstance(self.resource, Task):
            resource_kind = ResourceKind.TASK
        else:
            resource_kind = ResourceKind.WORKSPACE

        self.post_message(self.ResourceEdited(input_kwargs_dict, resource_kind, self.resource.id))
        self.dismiss(True)


class DeleteResourceScreen(TaskNomiModalScreen):
    BINDINGS = [
        ('escape', 'cancel_delete_resource', 'Cancel Resource Creation'),
        Binding('right', 'limited_focus_next', 'Focus Next', priority=True),
        Binding('left', 'limited_focus_previous', 'Focus Previous', priority=True),
    ]

    class DeleteResource(Message):
        def __init__(self, resource_id: str, resource_kind: ResourceKind) -> None:
            self.resource_id = resource_id
            self.resource_kind = resource_kind
            super().__init__()

    def __init__(self, resource_kind: ResourceKind, resource_id: str, resource_name: str, id='delete_resource'):
        super().__init__(id=id)
        self.resource_kind = resource_kind
        self.resource_id = resource_id
        self.resource_name = resource_name

    def compose(self) -> ComposeResult:
        grid = Grid(
            Label(f'Delete {str.lower(str(self.resource_kind))} "{self.resource_name}"?', id='question'),
            Container(),
            # spaces needed for correct coloring
            Button("   Cancel   ", id="cancel", compact=True),
            Button("     OK     ", id="delete", compact=True),
            Container(),
            id="dialog",
        )

        grid.border_title = '<Delete>'
        yield grid

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "delete":
            self.post_message(self.DeleteResource(self.resource_id, self.resource_kind))

        self.dismiss(True)

    def action_cancel_delete_resource(self) -> None:
        self.dismiss(True)
