#--------------------- Импорты -------------------------
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.forms import inlineformset_factory
from .models import *


#--------------------- Lecture Form -------------------------
from django import forms
from django.core.exceptions import ValidationError
from .models import Lecture, Category, Tag

class LectureForm(forms.ModelForm):
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Описание (необязательно)'
        }),
        label="Описание"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Делаем поля необязательными
        self.fields['content'].required = False
        self.fields['category'].required = False
        self.fields['tags'].required = False
        self.fields['image'].required = False

        # Для редактирования существующей лекции
        if self.instance and self.instance.pk:
            self.fields['file'].required = False

    def clean_file(self):
        uploaded_file = self.cleaned_data.get('file')
        
        # При редактировании разрешаем не загружать новый файл
        if self.instance and self.instance.pk:
            if not uploaded_file:
                return self.instance.file
        
        # Для новой лекции проверяем обязательность файла
        if not self.instance.pk and not uploaded_file:
            raise ValidationError("Необходимо загрузить файл лекции")
            
        return uploaded_file

    class Meta:
        model = Lecture
        fields = ['title', 'description', 'content', 'image', 'file', 'category', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название лекции'
            }),
            'content': forms.Textarea(attrs={
                'rows': 10, 
                'class': 'form-control',
                'placeholder': 'Дополнительный контент лекции'
            }),
            'file': forms.FileInput(attrs={
                'accept': '.doc,.docx', 
                'class': 'form-control'
            }),
            'image': forms.FileInput(attrs={
                'accept': 'image/*', 
                'class': 'form-control'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
                'data-placeholder': 'Выберите категорию'
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'data-placeholder': 'Выберите теги'
            }),
        }
        labels = {
            'title': 'Название лекции',
            'file': 'Файл лекции (DOC/DOCX)',
            'image': 'Обложка лекции',
            'content': 'Дополнительный контент',
            'category': 'Категория',
            'tags': 'Теги'
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Сохраняем автора только для новой лекции
        if not instance.pk:
            instance.author = self.initial.get('author')
        
        if commit:
            instance.save()
            self.save_m2m()
            
        return instance


#--------------------- Test Form -------------------------
class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'description', 'time_limit', 'password']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название теста'
            }),
            'password': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Пароль (Необязательно)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание теста'
            }),
            'time_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Время на прохождение (минуты)'
            })
        }
        labels = {
            'time_limit': 'Лимит времени (мин)'
        }


#--------------------- Test Password Form -------------------------
class TestPasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        }),
        label="Пароль"
    )


#--------------------- Question Form -------------------------
class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'image']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Текст вопроса'
            }),
            'image': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*'
            })
        }

    def __init__(self, *args, **kwargs):
        self.test = kwargs.pop('test', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.test:
            instance.test = self.test
        if commit:
            instance.save()
            self.save_m2m()
        return instance


#--------------------- Answer Form -------------------------
class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'image', 'is_correct']
        widgets = {
            'text': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Введите текст ответа'
            }),
            'image': forms.FileInput(attrs={
                'class': 'hidden',
                'accept': 'image/*'
            }),
            'is_correct': forms.CheckboxInput(attrs={
                'class': 'form-check-input h-5 w-5 rounded-full border-2 cursor-pointer',
            })
        }
        labels = {
            'is_correct': 'Правильный ответ'
        }


#--------------------- Answer FormSet -------------------------
class BaseAnswerFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
            
        correct_answers = 0
        for form in self.forms:
            if form.cleaned_data.get('is_correct', False):
                correct_answers += 1
        
        question_type = self.instance.question_type if self.instance else 'single'
        
        if question_type == 'single' and correct_answers != 1:
            raise forms.ValidationError("Должен быть ровно один правильный ответ для этого типа вопроса")
            
        if question_type == 'multiple' and correct_answers < 1:
            raise forms.ValidationError("Должен быть хотя бы один правильный ответ")
            
        if question_type == 'text' and correct_answers > 0:
            raise forms.ValidationError("Для текстовых вопросов не должно быть помеченных ответов")

AnswerFormSet = inlineformset_factory(
    Question,
    Answer,
    form=AnswerForm,
    formset=BaseAnswerFormSet,
    extra=5,
    min_num=5,
    max_num=5,
    validate_min=True,
    validate_max=True,
    can_delete=False,
    labels={
        'DELETE': 'Удалить ответ'
    }
)


#--------------------- Register Form -------------------------
class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        }),
        label="Электронная почта"
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Логин'
        }),
        label="Имя пользователя"
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пароль'
        }),
        label="Пароль"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Подтверждение пароля'
        }),
        label="Подтверждение пароля"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Этот email уже используется")
        return email


#--------------------- Login Form -------------------------
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Логин'
        }),
        label="Имя пользователя"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пароль'
        }),
        label="Пароль"
    )


#--------------------- VideoLecture Form -------------------------
class VideoLectureForm(forms.ModelForm):
    class Meta:
        model = VideoLecture
        fields = ['title', 'description', 'youtube_url', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название видеолекции'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Подробное описание видеолекции'
            }),
            'youtube_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.youtube.com/watch?v=...'
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'data-placeholder': 'Выберите теги'
            })
        }
        labels = {
            'youtube_url': 'YouTube ссылка',
        }
    
def clean_youtube_url(self):
    url = self.cleaned_data.get('youtube_url')
    
    if not url:
        raise ValidationError("Это поле обязательно для заполнения")
        
    if not ('youtube.com/watch?v=' in url or 'youtu.be/' in url):
        raise ValidationError("Пожалуйста, введите корректную ссылку на YouTube видео")
    
    return url


#--------------------- Presentation Form -------------------------
class PresentationForm(forms.ModelForm):
    class Meta:
        model = Presentation
        fields = ['title', 'description', 'file']

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            ext = file.name.split('.')[-1].lower()
            if ext != 'pdf':
                raise ValidationError("Разрешены только PDF-файлы")
            if file.size > 20 * 1024 * 1024:
                raise ValidationError("Максимальный размер файла 20MB")
        return file
    

#___________exercise form

from django import forms
from .models import Exercise

class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ['title', 'image', 'pdf_file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-green-500 focus:border-green-500',
                'placeholder': 'Введите название упражнения'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-sm text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-green-50 file:text-green-700 hover:file:bg-green-100',
                'accept': 'image/*'
            }),
            'pdf_file': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-sm text-gray-700 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-green-50 file:text-green-700 hover:file:bg-green-100',
                'accept': '.pdf'
            }),
        }


#dictionary______________________________________________

from django import forms
from .models import DictionaryEntry
class DictionaryEntryForm(forms.ModelForm):
    class Meta:
        model = DictionaryEntry
        fields = ['word', 'definition']
        widgets = {
            'word': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg mb-4',
                'placeholder': 'Введите слово'
            }),
            'definition': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg mb-4',
                'placeholder': 'Введите определение',
                'rows': 4
            }),
        }