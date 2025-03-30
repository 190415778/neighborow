from allauth.account.forms import LoginForm
from django import forms
# smg widgets
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

class CustomLoginForm(LoginForm):
    # optional email address for login
    email = forms.EmailField(required=False, label="Email (optional)")

    def login(self, *args, **kwargs):
        return super().login(*args, **kwargs)

# my form    
class MyForm(forms.Form):
    name = forms.CharField(label="Name", max_length=100)
    email = forms.EmailField(label="Email")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Absenden'))