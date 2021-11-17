from django import forms
from django.core.validators import RegexValidator
from .models import *


class SchoolClassForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SchoolClassForm, self).__init__(*args, **kwargs)
        self.fields['unique_code'].widget = forms.HiddenInput()
        self.fields['name'].widget = forms.TextInput(
            attrs={'placeholder': '(1-9, одна літера)', 'class': 'form-control input-sm'}
        )
        self.fields['year'].widget = forms.NumberInput(
            attrs={
                'placeholder': 'наприклад, 2021',
                'class': 'form-control input-sm'
            }
        )

    unique_code = forms.CharField(
        max_length=7,
        validators=[RegexValidator(r'^[1-9]{1}[а-я]{1}[0-9]{4}$')],
        help_text='Формат: назва класу + рік : 4в2019',
        required=False
    )

    class Meta:
        model = SchoolClass
        fields = ['name', 'year', 'unique_code']
        labels = {
            'name': 'назва класу',
            'unique_code': 'код класу',
            'year': 'рік навчання'
        }


class CreateStudentForm(forms.Form):
    name = forms.CharField(
        max_length=64,
        label='Ім\'я здобувача освіти:',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Введіть ім\'я',
                'class': 'form-control'
            }
        )
    )
    surname = forms.CharField(
        max_length=64,
        label='Прізвище здобувача освіти:',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Введіть прізвище',
                'class': 'form-control'
            }
        )
    )
    birthday = forms.DateField(
        label='Дата народження:',
        widget=forms.SelectDateWidget(
            attrs={
                'class': 'form-control'
            }
        )
    )
    first_parent_name = forms.CharField(
        max_length=64,
        label='Ім\'я мами чи тата:',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Введіть ім\'я',
                'class': 'form-control'
            }
        )
    )
    first_parent_surname = forms.CharField(
        max_length=64,
        label='Прізвище мами чи тата:',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Введіть прізвище',
                'class': 'form-control'
            }
        )
    )
    second_parent_name = forms.CharField(
        max_length=64,
        required=False,
        label='Ім\'я мами чи тата:',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Введіть ім\'я',
                'class': 'form-control'
            }
        )
    )
    second_parent_surname = forms.CharField(
        max_length=64,
        required=False,
        label='Прізвище мами чи тата:',
        widget=forms.TextInput(
            attrs={
                'placeholder':'Введіть прізвище',
                'class': 'form-control'
            }
        )
    )


class CreateTeacherForm(forms.Form):
    name = forms.CharField(
        max_length=64,
        label='Ім\'я:',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Введіть ім\'я',
                'class': 'form-control'
            }
        )
    )
    surname = forms.CharField(
        max_length=64,
        label='Прізвище:',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Введіть прізвище',
                'class': 'form-control'
            }
        )
    )


class CreateSubjectForm(forms.Form):
    name = forms.CharField(
        max_length=128,
        label='Назва',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Введіть назву',
                'class': 'form-control'
            }
        )
    )
    shortcut = forms.CharField(
        max_length=2,
        label='Скорочена назва',
        help_text='Скорочена назва предмету з двох букв',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Введіть скорочення',
                'class': 'form-control'
            }
        )
    )
    teachers = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={'class': ''}),
        queryset=Teacher.objects.filter(active=True),
        required=False,
        label='Вибір викладачів'
    )


class AddSubjectTeacherForm(forms.Form):
    teachers = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Teacher.objects.filter(active=True)
    )


class AddGradeForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AddGradeForm, self).__init__(*args, **kwargs)
        self.fields['grade'].widget = forms.NumberInput(
            attrs={'placeholder': 'Оцінка 1 - 5',
                   'class': 'form-control input-sm'}
        )

    class Meta:
        model = Grades
        fields = ['grade']
        labels = {'grade': 'Оцінка: '}


class MessageForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(MessageForm, self).__init__(*args, **kwargs)
        self.fields['subject'].widget = forms.TextInput(
            attrs={'placeholder': 'Введіть тему повідомлення',
                   'class': 'form-control input-sm'}
        )
        self.fields['text'].widget = forms.Textarea(
            attrs={'placeholder': 'Введіть текст повідомлення',
                   'class': 'form-control input-sm'}
        )

    class Meta:
        model = Message
        fields = {'subject', 'text'}
        labels = {'subject': 'Тема: ', 'text': 'Вміст повідомлення: '}


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Логін:',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Введіть логін',
                'class': 'form-control'
            }
        )
    )
    password = forms.CharField(
        label='Пароль:',
        min_length=5,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Введіть пароль',
                'class': 'form-control'
            }
        )
    )


class FirstLoginForm(forms.Form):
    username = forms.CharField(
        label='Логін',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Введіть логін',
                'class': 'form-control'
            }
        )
    )
    password = forms.CharField(
        label='Пароль',
        min_length=5,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Введіть пароль',
                'class': 'form-control'
            }
        )
    )
    password_confirm = forms.CharField(
        label=' Повторно введіть пароль',
        min_length=5,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'підтвердження',
                'class': 'form-control'
            }
        )
    )


class AddSubjectDateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AddSubjectDateForm, self).__init__(*args, **kwargs)
        self.fields['day'].widget.attrs['class'] = 'form-control input-sm'
        self.fields['lesson_number'].widget.attrs['class'] = \
            'form-control input-sm'

    class Meta:
        model = SubjectDate
        fields = ['day', 'lesson_number']
        labels = {'day': 'День тижня: ', 'lesson_number': 'Номер заняття: ', }
