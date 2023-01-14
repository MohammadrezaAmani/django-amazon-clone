from django import forms
# user create form
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings


class PaymentForm(forms.Form):
    Name = forms.CharField(max_length=100)
    Email = forms.EmailField()
    Address = forms.CharField(max_length=100)
    City = forms.CharField(max_length=100)
    State = forms.CharField(max_length=100)
    Zipcode = forms.CharField(max_length=100)


class LoginForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def exists(self):
        return User.objects.filter(email=self.cleaned_data['email']).exists()
    # if user exists, return true and login

    def login(self):
        if self.exists():
            return User.objects.get(email=self.cleaned_data['email'])
        return None


class SignUpForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super(SignUpForm, self).clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password != password2:
            raise forms.ValidationError(
                "password and confirm password does not match"
            )

    def exists(self):
        return User.objects.filter(email=self.cleaned_data['email']).exists()

    def login(self):
        if self.exists():
            return User.objects.get(email=self.cleaned_data['email'])
        return None

    def save(self):
        if not self.exists():
            user = User.objects.create_user(
                username=self.cleaned_data['name'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password']
            )
            user.save()
            return user
        return None
