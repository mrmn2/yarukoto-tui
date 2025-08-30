from classes import ResourceKind
from textual.app import Binding, ComposeResult
from textual.containers import Container, Grid
from textual.message import Message
from textual.screen import ModalScreen
from textual.validation import ValidationResult
from textual.widgets import Button, Input, Label
from widgets import CreateElementModal


class YarukotoModalScreen(ModalScreen):
    def action_limited_focus_next(self) -> None:
        current_index = self.focus_chain.index(self.focused)

        if current_index + 1 < len(self.focus_chain):
            self.focus_next()

    def action_limited_focus_previous(self) -> None:
        current_index = self.focus_chain.index(self.focused)

        if current_index > 0:
            self.focus_previous()


class CreateResourceScreen(YarukotoModalScreen):
    BINDINGS = [
        ('escape', 'cancel_create_resource', 'Cancel Resource Creation'),
        Binding('down', 'limited_focus_next', 'Focus Next', priority=True),
        Binding('up', 'limited_focus_previous', 'Focus Previous', priority=True),
        Binding('enter', 'submit_create_resource', 'Submit Resource Creation', priority=True),
    ]

    class ResourceCreated(Message):
        def __init__(self, creation_kwargs_dict: dict, resource_kind: ResourceKind) -> None:
            self.creation_kwargs_dict = creation_kwargs_dict
            self.resource_kind = resource_kind
            super().__init__()

    def __init__(self, create_modal_class: type[CreateElementModal], resource_kind: ResourceKind, id='creation_screen'):
        super().__init__(id=id)

        self.create_modal_class = create_modal_class
        self.resource_kind = resource_kind

    def compose(self) -> ComposeResult:
        # noinspection PyCallingNonCallable
        create_modal = self.create_modal_class()
        create_modal.border_title = f'CREATE {str(self.resource_kind)}'

        yield create_modal

    def action_cancel_create_resource(self) -> None:
        self.dismiss(True)

    def action_submit_create_resource(self) -> None:
        creation_inputs = self.query(Input)

        creation_kwargs_dict = {creation_input.id: creation_input.value for creation_input in creation_inputs}

        for creation_input in creation_inputs:
            input_value = creation_input.value.strip()
            validation_result = creation_input.validate(input_value)

            if validation_result and validation_result != ValidationResult.success():
                error_label = self.query_one('#error_label', Label)
                error_label.update(validation_result.failures[0].description)
                error_label.display = True
                return

        self.post_message(self.ResourceCreated(creation_kwargs_dict, self.resource_kind))
        self.dismiss(True)


class DeleteResourceScreen(YarukotoModalScreen):
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
            Label(f'Delete {str.lower(str(self.resource_kind))} "{self.resource_name[4:]}"?', id='question'),
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
