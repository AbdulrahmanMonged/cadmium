from quart_wtf import QuartForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class PrefixForm(QuartForm):
    prefix = StringField("Prefix", validators=[DataRequired()])