from django import forms

class ModelForm(forms.Form):
    title = forms.CharField(max_length=20)
    file = forms.FileField()