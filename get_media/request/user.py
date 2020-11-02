from django import forms


class UserRegister(forms.Form):
    firstname = forms.CharField(label='firstname', max_length=20)
    lastname = forms.CharField(label='lastname', max_length=20)
    birthday = forms.IntegerField(label='birthday', min_value=0)
    username = forms.CharField(label='username', max_length=50)
    password = forms.CharField(label='password', max_length=100)


class UserLogin(forms.Form):
    username = forms.CharField(label='username', max_length=50)
    password = forms.CharField(label='password', max_length=100)
    grant_type = forms.CharField(label='grant_type', max_length=20)


class UserRefresh(forms.Form):
    grant_type = forms.CharField(label='grant_type', max_length=20)
    refresh_token = forms.CharField(label='refresh_token')
