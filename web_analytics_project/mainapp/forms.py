from django import forms

class ModelForm(forms.Form):
    title = forms.CharField(max_length=20)
    start_string = forms.CharField(max_length=20)
    length = forms.IntegerField()
    file = forms.FileField()