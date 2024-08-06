class ByContextAdmissionFormMixin:
    """
    Hide and disable the fields that are not in the current context.
    """

    def __init__(self, current_context, fields_by_context, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields_by_context = fields_by_context
        self.current_context_fields = self.fields_by_context[current_context]

        self.disable_fields_other_contexts()

    def disable_fields_other_contexts(self):
        """Disable and hide fields specific to other contexts."""
        for field in self.fields:
            if field not in self.current_context_fields:
                self.fields[field].disabled = True
                self.fields[field].widget = self.fields[field].hidden_widget()

    def add_error(self, field, error):
        if field and self.fields[field].disabled:
            return
        super().add_error(field, error)
