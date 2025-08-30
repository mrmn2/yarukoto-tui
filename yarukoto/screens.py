from classes import ResourceKind
from textual.app import Binding, ComposeResult
from textual.message import Message
from textual.screen import ModalScreen
from textual.validation import ValidationResult
from textual.widgets import Input, Label
from widgets import CreateElementModal


class CreateResourceScreen(ModalScreen):
    BINDINGS = [
        ('escape', 'cancel_create_resource', 'Cancel Resource Creation'),
        Binding('down', 'app.focus_next', 'Focus Next', priority=True),
        Binding('up', 'app.focus_previous', 'Focus Previous', priority=True),
        Binding('enter', 'submit_create_resource', 'Submit Resource Creation', priority=True),
    ]

    # to be changed
    def __init__(self, create_modal_class: type[CreateElementModal], resource_kind: ResourceKind, id: str):
        super().__init__(id=id)

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
