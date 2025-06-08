from django import forms  # Добавляем импорт
from django.db.models import Q
import django_filters
from .models import Lecture, Category, Tag

class LectureFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        method='filter_search',
        label='Поиск',
        widget=forms.TextInput(attrs={
            'placeholder': 'Поиск по названию и содержанию...',
            'class': 'form-control'
        })
    )
    
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all(),
        label='Категория',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        label='Теги',
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'data-placeholder': 'Выберите теги'
        })
    )

    class Meta:
        model = Lecture
        fields = ['category', 'tags']

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) | 
            Q(description__icontains=value) |
            Q(content__icontains=value)
        ).distinct()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['category'].label = 'Категория'
        self.filters['tags'].label = 'Теги'