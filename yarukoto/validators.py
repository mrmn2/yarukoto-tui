from datetime import datetime

from textual.validation import ValidationResult, Validator


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
