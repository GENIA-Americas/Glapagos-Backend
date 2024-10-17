from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from api.datasets.models import Table


class ChartSerializer(serializers.Serializer):
    x = serializers.CharField(required=False, allow_blank=True)
    y = serializers.CharField(required=False, allow_blank=True)
    limit = serializers.IntegerField(required=False, min_value=0)

    def validate_column(self, column: str):
        """Validate if the column exists in the table schema."""
        if not column:
            return column

        table: Table = self.context.get('table')
        column_type = table.get_column_type(column)

        if not column_type:
            raise serializers.ValidationError(
                _("Column '{column}' not found in the table schema.").format(column=column)
            )

        return column_type

    def validate(self, attrs):
        x = attrs.get('x')
        y = attrs.get('y')

        if not x and not y:
            raise serializers.ValidationError(_("Chart must have at least one coordinate."))

        x_type = self.validate_column(x)
        y_type = self.validate_column(y)

        if not x and y_type != 'STRING':
            raise serializers.ValidationError(
                _("Column '{column}' should be a category of type string.").format(column=y)
            )

        if not y and x_type != 'STRING':
            raise serializers.ValidationError(
                _("Column '{column}' should be a category of type string.").format(column=x)
            )

        return attrs

