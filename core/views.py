#--------------------- Импорты -------------------------
from django.views.generic import DetailView, CreateView, UpdateView, ListView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django_filters.views import FilterView
from .filters import LectureFilter
from .utils import docx_to_html  
from django.contrib.auth import login, logout
from .forms import *
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from django.contrib import messages
from django.db import models
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.forms import inlineformset_factory

# ===================== Authentication Views =====================
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
    else:
        form = RegisterForm()
    return render(request, 'user/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Вход выполнен успешно!')
            return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'user/login.html', {'form': form})

def custom_logout(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('home')

@login_required(login_url='/login/')
def home_view(request):
    return render(request, 'base/home.html')



#--------------------- Lectures Views -------------------------
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.admin.views.decorators import staff_member_required
from django_filters.views import FilterView
from .models import Lecture, Category, Tag
from .forms import LectureForm
from .filters import LectureFilter

class LectureListView(LoginRequiredMixin, FilterView):
    model = Lecture
    filterset_class = LectureFilter
    template_name = 'lectures/lectures.html'
    context_object_name = 'lectures'
    paginate_by = 12
    login_url = '/login/'

    def get_queryset(self):
        return super().get_queryset()\
            .filter(is_published=True)\
            .select_related('author', 'category')\
            .prefetch_related('tags')\
            .order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'categories': Category.objects.all(),
            'tags': Tag.objects.all(),
            'search_query': self.request.GET.get('search', '')
        })
        return context

class LectureDetailView(DetailView):
    model = Lecture
    template_name = 'lectures/lecture_detail.html'
    
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.views += 1
        obj.save(update_fields=['views'])
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lecture = self.object
        
        if lecture.file:
            # Проверка на PDF вместо конвертации DOCX
            if lecture.file.name.endswith('.pdf'):
                context['is_pdf'] = True
            else:
                context['file_error'] = "Файл должен быть в формате PDF"
        return context

class AddLectureView(LoginRequiredMixin, CreateView):
    model = Lecture
    form_class = LectureForm
    template_name = 'lectures/add.html'
    success_url = reverse_lazy('lectures_list')
    login_url = '/login/'

    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.save()
        form.save_m2m()
        messages.success(self.request, 'Лекция успешно создана!')
        return redirect(self.get_success_url())

class LectureUpdateView(LoginRequiredMixin, UpdateView):
    model = Lecture
    form_class = LectureForm
    template_name = 'lectures/add.html'
    success_url = reverse_lazy('lectures_list')
    login_url = '/login/'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['editing'] = True
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Лекция успешно обновлена!')
        return response

@staff_member_required
def delete_lecture(request, pk):
    lecture = get_object_or_404(Lecture, pk=pk)
    if request.method == 'POST':
        lecture.delete()
        messages.success(request, 'Лекция успешно удалена')
    return redirect('lectures_list')



#--------------------- Tests Views -------------------------
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.forms import inlineformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.http import HttpResponseForbidden
from .models import Test, Question, Answer
from .forms import TestForm, QuestionForm, AnswerForm

def is_teacher(user):
    return user.groups.filter(name='Teachers').exists() or user.is_staff

class TestListView(ListView):
    model = Test
    template_name = 'test/index.html'
    context_object_name = 'tests'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().annotate(
            questions_count=models.Count('questions')
        )
        if search_query := self.request.GET.get('search'):
            queryset = queryset.filter(title__icontains=search_query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context

class TestCreateView(LoginRequiredMixin, CreateView):
    model = Test
    form_class = TestForm
    template_name = 'test/add_test.html'
    success_url = reverse_lazy('test_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Тест успешно создан!')
        return redirect('add_question', test_id=self.object.id)

class TestUpdateView(LoginRequiredMixin, UpdateView):
    model = Test
    form_class = TestForm
    template_name = 'test/add_test.html'
    success_url = reverse_lazy('test_list')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.is_staff and obj.author != request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        TestVariantFormSet = inlineformset_factory(
            Test, 
            Question, 
            fields=('text', 'image'), 
            extra=0
        )
        
        if self.request.POST:
            context['variant_formset'] = TestVariantFormSet(
                self.request.POST, 
                self.request.FILES, 
                instance=self.object
            )
        else:
            context['variant_formset'] = TestVariantFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        variant_formset = context['variant_formset']
        
        if form.is_valid() and variant_formset.is_valid():
            self.object = form.save()
            variant_formset.instance = self.object
            variant_formset.save()
            messages.success(self.request, 'Тест успешно обновлен!')
            return redirect(self.get_success_url())
        
        messages.error(self.request, 'Исправьте ошибки в форме')
        return self.render_to_response(context)

@login_required
@user_passes_test(is_teacher)
def add_question(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    
    if not (request.user.is_staff or test.author == request.user):
        raise PermissionDenied

    AnswerFormSet = inlineformset_factory(
        Question,
        Answer,
        form=AnswerForm,
        extra=5,
        max_num=5,
        min_num=5,
        validate_min=True
    )

    if request.method == 'POST':
        question_form = QuestionForm(request.POST, request.FILES)
        formset = AnswerFormSet(request.POST, request.FILES)

        if question_form.is_valid() and formset.is_valid():
            question = question_form.save(commit=False)
            question.test = test
            question.save()

            answers = formset.save(commit=False)
            correct_answers = 0
            
            for answer in answers:
                answer.question = question
                if answer.is_correct:
                    correct_answers += 1
                answer.save()

            if correct_answers == 0:
                question.delete()
                messages.error(request, 'Необходимо выбрать хотя бы один правильный ответ!')
                return render(request, 'test/add_question.html', {
                    'test': test,
                    'question_form': question_form,
                    'formset': formset,
                })

            messages.success(request, 'Вопрос успешно добавлен!')
            return redirect('test_detail', pk=test.id) if 'finish' in request.POST \
                else redirect('add_question', test_id=test.id)
        else:
            messages.error(request, 'Исправьте ошибки в форме')
    else:
        question_form = QuestionForm()
        formset = AnswerFormSet(queryset=Answer.objects.none())
    
    return render(request, 'test/add_question.html', {
        'test': test,
        'question_form': question_form,
        'formset': formset,
    })

@login_required
def test_detail(request, pk):
    test = get_object_or_404(Test, pk=pk)
    
    if is_teacher(request.user):
        questions = test.questions.prefetch_related('answers').annotate(
            correct_count=models.Count('answers', filter=models.Q(answers__is_correct=True))
        )  
        
        return render(request, 'test/test_detail.html', {
            'test': test,
            'questions': questions,
            'is_teacher': True
        })
    return redirect('take_test', pk=test.id)

@login_required
def select_variant(request, test_id):
    test = get_object_or_404(Test, pk=test_id)
    if not test.has_variants:
        return redirect('take_test', pk=test_id)
    
    if request.method == 'POST':
        variant_id = request.POST.get('variant')
        if variant_id:
            return redirect('take_test_variant', pk=test_id, variant_id=variant_id)
        messages.error(request, 'Выберите вариант теста')
    
    return render(request, 'test/select_variant.html', {
        'test': test,
        'variants': test.variants.all()
    })

@login_required
def take_test(request, pk):
    if is_teacher(request.user):
        return redirect('test_detail', pk=pk)
    
    test = get_object_or_404(Test, pk=pk)
    
    if test.password and not request.session.get(f'test_{test.id}_unlocked'):
        return redirect('enter_test_password', pk=test.id)
    
    if request.method == 'POST':
        score = 0
        total = test.questions.count()
        
        for question in test.questions.all():
            answer_id = request.POST.get(f'question_{question.id}')
            if answer_id:
                try:
                    answer = Answer.objects.get(id=answer_id, question=question)
                    if answer.is_correct:
                        score += 1
                except Answer.DoesNotExist:
                    continue
        
        messages.success(request, f'Результат: {score}/{total}')
        return redirect('test_results', pk=test.id, score=score)
    
    return render(request, 'test/take_test.html', {
        'test': test,
        'questions': test.questions.all()
    })

@login_required
def enter_test_password(request, pk):
    test = get_object_or_404(Test, pk=pk)
    
    if request.method == 'POST':
        entered_password = request.POST.get('password')
        if entered_password == test.password:
            request.session[f'test_{test.id}_unlocked'] = True
            return redirect('take_test', pk=pk)
        messages.error(request, 'Неверный пароль!')
    
    return render(request, 'test/enter_password.html', {'test': test})

@login_required
def test_results(request, pk, score):
    test = get_object_or_404(Test, pk=pk)
    total = test.questions.count()
    percentage = int((int(score) / total * 100) if total > 0 else 0)
    
    return render(request, 'test/results.html', {
        'test': test,
        'score': score,
        'total': total,
        'percentage': percentage
    })


@login_required
def delete_test(request, pk):
    test = get_object_or_404(Test, pk=pk)
    
    if not (request.user.is_staff or test.author == request.user):
        raise PermissionDenied

    test.delete()
    messages.success(request, 'Тест успешно удален')
    return redirect('test_list')

@login_required
def test_questions(request, pk):
    test = get_object_or_404(Test, pk=pk)
    questions = test.questions.all()
    
    if not (request.user.is_staff or test.author == request.user):
        return HttpResponseForbidden()
    
    return render(request, 'test/questions.html', {
        'test': test,
        'questions': questions,
    })

@login_required
def edit_test(request, pk):
    test = get_object_or_404(Test, pk=pk)
    
    if not (request.user.is_staff or request.user == test.author):
        raise PermissionDenied

    QuestionFormSet = inlineformset_factory(
        Test,
        Question,
        fields=('text', 'image', 'question_type', 'points'),
        extra=0,
        can_delete=True
    )
    
    AnswerFormSet = inlineformset_factory(
        Question,
        Answer,
        form=AnswerForm,
        extra=0,
        min_num=5,
        max_num=5,
        can_delete=False
    )

    if request.method == 'POST':
        test_form = TestForm(request.POST, instance=test)
        question_formset = QuestionFormSet(
            request.POST, 
            request.FILES, 
            instance=test,
            prefix='questions'
        )
        
        if test_form.is_valid() and question_formset.is_valid():
            test_form.save()
            questions = question_formset.save(commit=False)
            
            for question in questions:
                question.save()
                answer_formset = AnswerFormSet(
                    request.POST,
                    request.FILES,
                    instance=question,
                    prefix=f'answers_{question.id}'
                )
                if answer_formset.is_valid():
                    answer_formset.save()
            
            messages.success(request, 'Тест успешно обновлен!')
            return redirect('test_detail', pk=test.pk)
        else:
            messages.error(request, 'Исправьте ошибки в форме')
    else:
        test_form = TestForm(instance=test)
        question_formset = QuestionFormSet(instance=test, prefix='questions')
        
        for question in test.questions.all():
            question.answer_formset = AnswerFormSet(
                instance=question,
                prefix=f'answers_{question.id}'
            )

    return render(request, 'test/edit_test.html', {
        'test': test,
        'test_form': test_form,
        'question_formset': question_formset,
    })

#--------------------- Video Lectures Views -------------------------

def video_lecture_view(request):
    lectures = VideoLecture.objects.all().order_by('-created_at')
    
    # Добавляем пагинацию
    paginator = Paginator(lectures, 9)  # 9 элементов на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'video/videolecture.html', {
        'page_obj': page_obj,
        'lectures': lectures  # На всякий случай оставляем
    })

@login_required
def add_video_lecture_view(request):
    if request.method == 'POST':
        form = VideoLectureForm(request.POST)
        if form.is_valid():
            lecture = form.save(commit=False)
            lecture.author = request.user
            lecture.save()
            form.save_m2m()
            messages.success(request, 'Видеолекция успешно добавлена!')
            return redirect('video_lectures')
    else:
        form = VideoLectureForm()
    
    return render(request, 'video/add_video_lecture.html', {'form': form})

from django.contrib import messages

@login_required
def edit_video_lecture_view(request, lecture_id):
    lecture = get_object_or_404(VideoLecture, id=lecture_id)
    
    # Проверка прав доступа
    if request.user != lecture.author and not request.user.is_superuser:
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        form = VideoLectureForm(request.POST, instance=lecture)
        if form.is_valid():
            form.save()
            messages.success(request, 'Изменения успешно сохранены!')
            return redirect('video_lectures')
    else:
        form = VideoLectureForm(instance=lecture)
    
    return render(request, 'video/edit_video_lecture.html', {'form': form, 'lecture': lecture})

@login_required
def delete_video_lecture_view(request, lecture_id):
    lecture = get_object_or_404(VideoLecture, id=lecture_id)
    
    # Проверка прав доступа
    if request.user != lecture.author and not request.user.is_superuser:
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        lecture.delete()
        messages.success(request, 'Видеолекция успешно удалена!')
        return redirect('video_lectures')
    
    return redirect('video_lectures')

#--------------------- Presentations Views -------------------------
class PresentationListView(ListView):
    model = Presentation
    template_name = 'presentations/presentation_list.html'
    context_object_name = 'presentations'

class PresentationDetailView(DetailView):
    model = Presentation
    template_name = 'presentations/presentation_detail.html'
    context_object_name = 'presentation'

class PresentationCreateView(LoginRequiredMixin, CreateView):
    model = Presentation
    form_class = PresentationForm
    template_name = 'presentations/presentation_form.html'
    success_url = reverse_lazy('presentation-list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class PresentationDeleteView(UserPassesTestMixin, DeleteView):
    model = Presentation
    template_name = 'presentations/presentation_confirm_delete.html'
    success_url = reverse_lazy('presentation-list')

    def test_func(self):
        return self.request.user.is_staff
    

#________________________________________________mathsolver

def math_solver_base_view(request):
    return render(request, 'mathsolver/math_solver_base.html')

def linear_algebra_base_view(request):
    return render(request, 'mathsolver/linear_algebra/linear_algebra_base.html')

def conic_view(request):
    return render(request, 'mathsolver/conic/index.html')

def calculus_view(request):
    return render(request, 'mathsolver/calculus/index.html')

def trigonometry_view(request):
    return render(request, 'mathsolver/trigonometry/index.html')

def general_maths_view(request):
    return render(request, 'mathsolver/general_maths/index.html')

def basic_converters_view(request):
    return render(request, 'mathsolver/basic_converters/index.html')

def graphs_shapes_view(request):
    return render(request, 'mathsolver/graphs_shapes/index.html')

def equations_view(request):
    return render(request, 'mathsolver/equations/index.html')

def binary_view(request):
    return render(request, 'mathsolver/binary/index.html')

def complex_view(request):
    return render(request, 'mathsolver/complex/index.html')

def probability_view(request):
    return render(request, 'mathsolver/probability/index.html')

def statistics_view(request):
    return render(request, 'mathsolver/statistics/index.html')

def mensuration_view(request):
    return render(request, 'mathsolver/mensuration/index.html')

def shapes3d_view(request):
    return render(request, 'mathsolver/mensuration/3dshapes.html')

def shapes2d_view(request):
    return render(request, 'mathsolver/mensuration/shapes2d.html')

def introduction_view(request):
    return render(request, 'mathsolver/mensuration/introduction.html')

def roots(request):
    return render(request, 'mathsolver/equations/roots.html')

def static_analys(request):
    return render(request, 'mathsolver/statistics/static_analys.html')

def weight_mean(request):
    return render(request, 'mathsolver/statistics/weight_mean.html')

def moments(request):
    return render(request, 'mathsolver/statistics/moments.html')

def sensitivity(request):
    return render(request, 'mathsolver/statistics/sensitivity.html')

def deviation(request):
    return render(request, 'mathsolver/statistics/deviation.html')

def ttest(request):
    return render(request, 'mathsolver/statistics/ttest.html')


#-----------------------Упражнения


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Exercise
from .forms import ExerciseForm
from django.core.paginator import Paginator
import os

def is_staff(user):
    return user.is_staff

def exercise_list(request):
    exercises = Exercise.objects.all().order_by('-created_at')
    paginator = Paginator(exercises, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'exercises/list.html', {
        'exercises': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    })

def exercise_detail(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk)
    return render(request, 'exercises/detail.html', {'exercise': exercise})

@login_required
@user_passes_test(is_staff)
def add_exercise(request):
    form_errors = None
    if request.method == 'POST':
        form = ExerciseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('exercise')
        else:
            form_errors = form.errors
    else:
        form = ExerciseForm()
    return render(request, 'exercises/add.html', {
        'form': form, 
        'is_edit': False,
        'form_errors': form_errors
    })

@login_required
@user_passes_test(is_staff)
def edit_exercise(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk)
    delete_requested = 'delete' in request.GET
    form_errors = None
    
    if request.method == 'POST':
        if 'delete' in request.POST:
            # Удаление упражнения
            if exercise.image:
                if os.path.isfile(exercise.image.path):
                    os.remove(exercise.image.path)
            if exercise.pdf_file:
                if os.path.isfile(exercise.pdf_file.path):
                    os.remove(exercise.pdf_file.path)
            exercise.delete()
            return redirect('exercise')
        
        form = ExerciseForm(request.POST, request.FILES, instance=exercise)
        if form.is_valid():
            # Обработка удаления изображения
            if 'image-clear' in request.POST:
                if exercise.image:
                    if os.path.isfile(exercise.image.path):
                        os.remove(exercise.image.path)
                    exercise.image = None
            
            # Обработка удаления PDF
            if 'pdf_file-clear' in request.POST:
                if exercise.pdf_file:
                    if os.path.isfile(exercise.pdf_file.path):
                        os.remove(exercise.pdf_file.path)
                    exercise.pdf_file = None
            
            # Сохраняем форму без коммита, чтобы обработать файлы
            exercise_obj = form.save(commit=False)
            
            # Обработка загрузки новых файлов
            if 'image' in request.FILES:
                # Сохраняем новое изображение
                exercise_obj.image = request.FILES['image']
            
            if 'pdf_file' in request.FILES:
                exercise_obj.pdf_file = request.FILES['pdf_file']
            
            # Сохраняем объект в БД
            exercise_obj.save()
            return redirect('exercise_detail', pk=exercise.pk)
        else:
            form_errors = form.errors
    else:
        form = ExerciseForm(instance=exercise)
    
    context = {
        'form': form,
        'exercise': exercise,
        'is_edit': True,
        'delete_requested': delete_requested,
        'form_errors': form_errors
    }
    return render(request, 'exercises/add.html', context)

#________________________________dictionary


from django.db.models import Q
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from .models import DictionaryEntry
from .forms import DictionaryEntryForm

class DictionaryView(ListView):
    model = DictionaryEntry
    template_name = 'dictionary/dictionary.html'
    context_object_name = 'entries'
    paginate_by = 20
    ordering = ['word']

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            query = query.strip()
            return queryset.filter(
                Q(word__icontains=query) | 
                Q(definition__icontains=query)
            ).order_by('word')
        return queryset

class AddWordView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = DictionaryEntry
    form_class = DictionaryEntryForm
    template_name = 'dictionary/add_word.html'
    success_url = reverse_lazy('dictionary')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, 'Слово успешно добавлено!')
        return super().form_valid(form)

@method_decorator(staff_member_required, name='dispatch')
class UpdateWordView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = DictionaryEntry
    form_class = DictionaryEntryForm
    template_name = 'dictionary/edit_word.html'
    success_url = reverse_lazy('dictionary')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        messages.success(self.request, 'Изменения сохранены!')
        return super().form_valid(form)

@method_decorator(staff_member_required, name='dispatch')
class DeleteWordView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = DictionaryEntry
    template_name = 'dictionary/delete_word.html'
    success_url = reverse_lazy('dictionary')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Слово успешно удалено!')
        return super().delete(request, *args, **kwargs)



from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import UserPoints, PointHistory, ChatMessage
from django.utils import timezone
from datetime import timedelta

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import UserPoints, PointHistory, ChatMessage
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

import json
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import escape

# ===================== Utility Functions =====================
def json_response(success=True, **kwargs):
    """Универсальный JSON-ответ"""
    response = {'success': success}
    response.update(kwargs)
    return JsonResponse(response)

def json_error(message, status=400):
    """Возвращает JSON с ошибкой"""
    return json_response(success=False, error=message, status=status)

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils.html import escape
import json
from datetime import timedelta

from .models import UserPoints, ChatMessage
from .forms import RegisterForm, LoginForm

# ===================== Utility Functions =====================
def json_response(success=True, **kwargs):
    """Унифицированный JSON-ответ"""
    response = {'success': success}
    response.update(kwargs)
    return JsonResponse(response)

def json_error(message, status=400):
    """JSON-ответ с ошибкой"""
    return JsonResponse({'success': False, 'error': message}, status=status)

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from .models import ChatMessage, UserPoints, PointHistory
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import json
import logging
from django.db.models import Sum

logger = logging.getLogger(__name__)

def json_response(**kwargs):
    """Утилита для создания JSON-ответов"""
    return JsonResponse({'status': 'success', **kwargs})

def json_error(message, status=400):
    """Утилита для создания JSON-ошибок"""
    return JsonResponse({'status': 'error', 'message': message}, status=status)

# ===================== Grind Views =====================
@login_required
def grind_main(request):
    """Основная страница Grind режима"""
    try:
        user_points = UserPoints.objects.get(user=request.user)
        context = {
            'user_points': user_points,
            'is_upgraded': user_points.is_upgraded,
            'daily_limit': user_points.DAILY_FAST_CLICKS_LIMIT
        }
        return render(request, 'grind/grind.html', context)
    except ObjectDoesNotExist:
        user_points = UserPoints.objects.create(user=request.user)
        return redirect('grind_main')

@login_required
def profile_view(request):
    """Страница профиля пользователя"""
    try:
        user_points = UserPoints.objects.get(user=request.user)
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        
        context = {
            'user_points': user_points,
            'daily_points': user_points.get_daily_points(),
            'weekly_points': user_points.get_weekly_points(),
            'remaining_points': max(0, 1000 - user_points.points),
            'point_history': user_points.history.all().order_by('-created_at')[:10],
            'start_of_week': start_of_week.strftime('%d.%m.%Y'),
            'today': today.strftime('%d.%m.%Y')
        }
        return render(request, 'user/profile.html', context)
    except ObjectDoesNotExist:
        user_points = UserPoints.objects.create(user=request.user)
        return redirect('profile')

@login_required
@csrf_protect
def get_points_state(request):
    """Получение текущего состояния баллов (AJAX)"""
    try:
        user_points = UserPoints.objects.get(user=request.user)
        return json_response(
            points=user_points.points,
            total_points=user_points.total_points,
            fast_clicks_today=user_points.fast_clicks_today,
            is_upgraded=user_points.is_upgraded,
            slow_cooldown=user_points.slow_click_cooldown.total_seconds(),
            daily_limit=user_points.DAILY_FAST_CLICKS_LIMIT
        )
    except ObjectDoesNotExist:
        return json_error('Профиль баллов не найден', status=404)

@login_required
@require_POST
@csrf_protect
def add_slow_click(request):
    """Обработка медленного клика"""
    try:
        with transaction.atomic():
            user_points = UserPoints.objects.select_for_update().get(user=request.user)
            
            if not user_points.can_make_slow_click:
                remaining = user_points.slow_click_cooldown
                mins = int(remaining.total_seconds() // 60)
                secs = int(remaining.total_seconds() % 60)
                return json_response(
                    success=False,
                    message=f'Подождите еще {mins} мин {secs} сек',
                    cooldown=remaining.total_seconds()
                )
            
            user_points.make_slow_click()
            return json_response(
                success=True,
                points=user_points.points,
                total_points=user_points.total_points,
                cooldown=user_points.SLOW_CLICK_COOLDOWN.total_seconds(),
                message='Медленный клик засчитан'
            )
    except ObjectDoesNotExist:
        return json_error('Профиль баллов не найден', status=404)
    except Exception as e:
        logger.error(f"Ошибка медленного клика: {str(e)}")
        return json_error('Внутренняя ошибка сервера', status=500)

@login_required
@require_POST
@csrf_protect
def add_fast_click(request):
    """Обработка быстрого клика"""
    try:
        with transaction.atomic():
            user_points = UserPoints.objects.select_for_update().get(user=request.user)
            success, amount = user_points.make_fast_click()
            
            return json_response(
                success=success,
                points=user_points.points,
                total_points=user_points.total_points,
                amount=amount,
                fast_clicks_today=user_points.fast_clicks_today,
                remaining=user_points.DAILY_FAST_CLICKS_LIMIT - user_points.fast_clicks_today,
                message=f'Быстрый клик: +{amount} очков' if success else 'Достигнут дневной лимит'
            )
    except ObjectDoesNotExist:
        return json_error('UserPoints не найден', status=404)
    except Exception as e:
        return json_error(str(e), status=500)

@login_required
@require_POST
@csrf_protect
def upgrade(request):
    """Обработка улучшения аккаунта"""
    try:
        with transaction.atomic():
            user_points = UserPoints.objects.select_for_update().get(user=request.user)
            success = user_points.upgrade_account()
            
            return json_response(
                success=success,
                points=user_points.points,
                is_upgraded=user_points.is_upgraded,
                message='Улучшение активировано!' if success else 'Недостаточно очков для улучшения'
            )
    except ObjectDoesNotExist:
        return json_error('UserPoints не найден', status=404)
    except Exception as e:
        return json_error(str(e), status=500)

# ===================== Chat Views =====================
@login_required
def chat_view(request):
    try:
        points = UserPoints.objects.get(user=request.user).points
    except UserPoints.DoesNotExist:
        points = 0
        UserPoints.objects.create(user=request.user, points=0)
    
    return render(request, 'chat/chat.html', {
        'user_points': points
    })

@csrf_exempt
@login_required
@require_POST
def send_message(request):
    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()
        
        if not content:
            return JsonResponse({'error': 'Сообщение не может быть пустым'}, status=400)
        
        if len(content) > 500:
            return JsonResponse({'error': 'Сообщение слишком длинное (макс. 500 символов)'}, status=400)
        
        user_points, created = UserPoints.objects.get_or_create(
            user=request.user,
            defaults={'points': 0}
        )
        
        points_needed = 100
        
        if not request.user.is_staff and user_points.points < points_needed:
            return JsonResponse({
                'error': f'Недостаточно очков. Требуется: {points_needed}, доступно: {user_points.points}'
            }, status=403)
        
        message = ChatMessage.objects.create(
            user=request.user,
            content=content,
            points_spent=points_needed if not request.user.is_staff else 0
        )
        
        if not request.user.is_staff:
            user_points.spend_points(points_needed, f"Отправка сообщения: {content[:50]}...")
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'username': request.user.username,
                'content': message.content,
                'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'points_spent': message.points_spent,
                'points_left': user_points.points
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Внутренняя ошибка сервера'}, status=500)

@login_required
@require_GET
def get_messages(request):
    try:
        last_id = int(request.GET.get('last_id', 0))
    except ValueError:
        last_id = 0
    
    try:
        messages = ChatMessage.objects.filter(id__gt=last_id).select_related('user').order_by('timestamp')[:50]
        
        messages_data = [{
            'id': msg.id,
            'username': msg.user.username,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'points_spent': msg.points_spent
        } for msg in messages]
        
        return JsonResponse({
            'status': 'success',
            'messages': messages_data,
            'server_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        logger.error(f"Ошибка загрузки сообщений: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Внутренняя ошибка сервера'
        }, status=500)

@login_required
@require_GET
def get_points(request):
    try:
        user_points = UserPoints.objects.get(user=request.user)
        return JsonResponse({
            'points': user_points.points,
            'is_upgraded': user_points.is_upgraded
        })
    except UserPoints.DoesNotExist:
        return JsonResponse({'points': 0, 'is_upgraded': False})

@login_required
@require_GET
def online_users(request):
    try:
        online_count = UserPoints.objects.filter(
            last_activity__gte=timezone.now() - timedelta(minutes=5)
        ).exclude(user=request.user).count()
        
        return JsonResponse({
            'online_count': online_count,
            'server_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        logger.error(f"Ошибка получения онлайн пользователей: {str(e)}", exc_info=True)
        return JsonResponse({
            'online_count': 0,
            'error': 'Ошибка сервера'
        }, status=500)