import re
from django.db import models
from django.core.exceptions import ValidationError
import jdatetime
from typing import Any

class NajronoDateField(models.Field):
    description = "A custom field to store Jalali date as packed year, month, and day"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["max_length"] = kwargs.get("max_length", 10)
        super().__init__(*args, **kwargs)

    def db_type(self, connection):
        return "CHAR(10)"

    def get_internal_type(self):
        return "CharField"

    def to_python(self, value):
        if value is None:
            return None
        if self.validate_date_format(value):
            return value
        else:
            raise ValidationError('Invalid date format. Please use YYYY-MM-DD.')

    def get_prep_value(self, value):
        if isinstance(value, jdatetime.date):
            return f"{value.year:04d}-{value.month:02d}-{value.day:02d}"
        return super().get_prep_value(value)
    

    def get_prep_lookup(self, lookup_type, value):
        print(lookup_type)
        print(value)
        if isinstance(value, jdatetime.date):
            value = self.get_prep_value(value)
        return super().get_prep_lookup(lookup_type, value)

    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        if value is None:
            return
        if not self.validate_date_format(value):
            raise ValidationError('Invalid date format. Please use YYYY-MM-DD.')

    def validate_date_format(self, value):
        regex = r'^\d{4}-\d{2}-\d{2}$'
        return re.match(regex, value) is not None
