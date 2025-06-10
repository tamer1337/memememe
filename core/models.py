#--------------------- Импорты -------------------------
from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator
import os
from django.utils.text import slugify
import subprocess
from django.contrib.auth.decorators import user_passes_test
from django.utils.text import get_valid_filename


#--------------------- User -------------------------
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import FileExtensionValidator

class User(AbstractUser):
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username

class Category(models.Model):
    name = models.CharField("Категория", max_length=100)
    icon = models.CharField("Иконка", max_length=50, blank=True)

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField("Тег", max_length=50)

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название предмета")
    
    def __str__(self):
        return self.name

def lecture_file_path(instance, filename):
    return f'lectures/{instance.id}/{filename}'

class Lecture(models.Model):
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")
    title = models.CharField("Название", max_length=200)
    description = models.TextField("Описание", blank=True, default="")
    content = models.TextField("Контент", blank=True)
    image = models.ImageField("Обложка", upload_to='lectures/', null=True, blank=True)
    file = models.FileField(
        "Файл лекции",
        upload_to=lecture_file_path,
        validators=[FileExtensionValidator(['pdf'])],  # ТОЛЬКО PDF
        default='default.pdf'  # Обновлено
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Автор")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    views = models.PositiveIntegerField("Просмотры", default=0)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Лекция"
        verbose_name_plural = "Лекции"
        ordering = ['-created_at']


#--------------------- Test -------------------------
class Test(models.Model):
    title = models.CharField(max_length=200, verbose_name="Название теста")
    description = models.TextField(verbose_name="Описание", blank=True)
    password = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name="Пароль для доступа"
    )
    time_limit = models.PositiveIntegerField(
        verbose_name="Лимит времени (мин)", 
        default=30,
        null=True,
        blank=True
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True, verbose_name="Опубликован")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Тест"
        verbose_name_plural = "Тесты"
        ordering = ['-created_at']


#--------------------- Question -------------------------
from django.db import models
from django.core.validators import MinValueValidator

class Question(models.Model):
    QUESTION_TYPES = [
        ('single', 'Один правильный ответ'),
        ('multiple', 'Несколько правильных ответов'),
        ('text', 'Текстовый ответ'),
    ]

    test = models.ForeignKey(
        'Test',  # Явное указание имени модели в строке, если она объявлена позже
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name="Тест"
    )
    text = models.TextField(verbose_name="Текст вопроса")
    question_type = models.CharField(
        max_length=10,
        choices=QUESTION_TYPES,
        default='single',
        verbose_name="Тип вопроса"
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
        help_text="Порядок отображения (0 - первый)"
    )
    points = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Баллы"
    )
    explanation = models.TextField(
        verbose_name="Объяснение",
        blank=True
    )
    image = models.ImageField(
        upload_to='questions/images/',
        blank=True,
        null=True,
        verbose_name="Изображение"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    def __str__(self):
        return f"Вопрос {self.id} ({self.test.title})"

    @property
    def correct_answers_count(self):
        return self.answers.filter(is_correct=True).count()

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ['order']
        indexes = [
            models.Index(fields=['order', 'test']),
        ]


#--------------------- Answer -------------------------
class Answer(models.Model):
    question = models.ForeignKey(
        Question, 
        on_delete=models.CASCADE, 
        related_name='answers',
        verbose_name="Вопрос"
    )
    text = models.CharField(
        max_length=500, 
        verbose_name="Текст ответа"
    )
    image = models.ImageField(
        upload_to='answers/images/',
        blank=True,
        null=True,
        verbose_name="Изображение"
    )
    is_correct = models.BooleanField(
        default=False, 
        verbose_name="Правильный ответ"
    )
    order = models.PositiveIntegerField(
        default=0, 
        verbose_name="Порядок"
    )

    def __str__(self):
        return f"Ответ {self.id} (вопрос {self.question.id})"

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"
        ordering = ['order']

    image = models.ImageField(upload_to='answers/', blank=True, null=True)


#--------------------- TestResult -------------------------
class TestResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(verbose_name="Баллы")
    max_score = models.PositiveIntegerField(verbose_name="Максимальный балл")
    completed_at = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(verbose_name="Детали результатов", default=dict)

    def __str__(self):
        return f"Результат {self.user} по тесту {self.test}"

    class Meta:
        verbose_name = "Результат теста"
        verbose_name_plural = "Результаты тестов"
        ordering = ['-completed_at']


#--------------------- VideoLecture -------------------------
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import timedelta
import re

def validate_youtube_url(value):
    regex = r'^https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|embed/|live/)|youtu\.be/)[\w-]+'
    if not re.match(regex, value):
        raise ValidationError("Некорректная YouTube ссылка")

class VideoLectureManager(models.Manager):
    def published(self):
        return self.filter(is_published=True)

class VideoLecture(models.Model):
    title = models.CharField("Название", max_length=200)
    youtube_id = models.CharField("YouTube ID", max_length=20, blank=True, editable=False, default='')
    description = models.TextField("Описание", blank=True)
    youtube_url = models.URLField("Ссылка на YouTube", validators=[validate_youtube_url])
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Автор"
    )
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)
    views = models.PositiveBigIntegerField("Просмотры", default=0)
    duration = models.PositiveIntegerField("Длительность (сек)", default=0)
    is_published = models.BooleanField("Опубликовано", default=True)
    tags = models.ManyToManyField(
        'Tag',
        blank=True,
        verbose_name="Теги"
    )

    objects = VideoLectureManager()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.youtube_id = self.extract_youtube_id()
        super().save(*args, **kwargs)

    def extract_youtube_id(self):
        pattern = r'(?:v=|be/|embed/|/v/|/e/|vi?/|v=)([^&?#]+)'
        match = re.search(pattern, self.youtube_url)
        return match.group(1) if match else None

    @property
    def duration_formatted(self):
        return str(timedelta(seconds=self.duration))

    class Meta:
        verbose_name = "Видеолекция"
        verbose_name_plural = "Видеолекции"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'is_published']),
            models.Index(fields=['author']),
        ]


#--------------------- Admin Decorator -------------------------
def admin_required(view_func):
    """Декоратор для проверки прав администратора"""
    return user_passes_test(
        lambda u: u.is_active and u.is_staff,
        login_url='/admin/login/'
    )(view_func)


#--------------------- Presentation -------------------------
class Presentation(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='presentations/', verbose_name='Файл')

    @classmethod
    def get_upload_path(cls, instance, filename):
        """Генерирует путь для сохранения файлов"""
        return os.path.join('presentations', get_valid_filename(filename))

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']



#___________________________exercise form

from django.db import models
import uuid
import os

def image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f'exercise_images/{filename}'

def pdf_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f'exercises_pdfs/{filename}'

class Exercise(models.Model):
    title = models.CharField(max_length=255, verbose_name="Название упражнения")
    image = models.ImageField(
        upload_to=image_upload_path,
        verbose_name="Изображение",
        null=True, 
        blank=True
    )
    pdf_file = models.FileField(
        upload_to=pdf_upload_path,
        max_length=500,
        verbose_name="PDF-документ"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # При обновлении изображения - удаляем старое
        if self.pk:
            old_instance = Exercise.objects.get(pk=self.pk)
            if old_instance.image and old_instance.image != self.image:
                if os.path.isfile(old_instance.image.path):
                    os.remove(old_instance.image.path)
            if old_instance.pdf_file and old_instance.pdf_file != self.pdf_file:
                if os.path.isfile(old_instance.pdf_file.path):
                    os.remove(old_instance.pdf_file.path)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Удаление файлов при удалении объекта
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        if self.pdf_file:
            if os.path.isfile(self.pdf_file.path):
                os.remove(self.pdf_file.path)
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "Упражнение"
        verbose_name_plural = "Упражнения"
        ordering = ['-created_at']



#_________________________dictionary

class DictionaryEntry(models.Model):
    word = models.CharField('Слово', max_length=100, unique=True)
    definition = models.TextField('Определение')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.word


from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum
from django.core.exceptions import ValidationError
import logging
from datetime import timedelta
import random

logger = logging.getLogger(__name__)
User = get_user_model()

class UserPointsManager(models.Manager):
    def get_or_create_points(self, user):
        try:
            return self.get_or_create(user=user)[0]
        except Exception as e:
            logger.error(f"Error getting/creating UserPoints for {user}: {str(e)}")
            raise

    def get_user_points(self, user):
        try:
            return self.get(user=user).points
        except UserPoints.DoesNotExist:
            return 0

class UserPoints(models.Model):
    SLOW_CLICK_COOLDOWN = timedelta(minutes=15)
    MESSAGE_COST = 100
    UPGRADE_COST = 1000
    DAILY_FAST_CLICKS_LIMIT = 100
    FAST_CLICK_MIN = 5
    FAST_CLICK_MAX = 10
    FAST_CLICK_UPGRADED_MIN = 10
    FAST_CLICK_UPGRADED_MAX = 20

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='points_profile')
    points = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    total_points = models.PositiveIntegerField(default=0)
    is_upgraded = models.BooleanField(default=False)
    last_slow_click = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    fast_clicks_today = models.PositiveIntegerField(default=0)
    first_click_today = models.DateTimeField(null=True, blank=True)  # Новое поле для времени первого клика

    objects = UserPointsManager()

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['last_activity']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.points} баллов"

    @property
    def can_make_slow_click(self):
        if not self.last_slow_click:
            return True
        return timezone.now() - self.last_slow_click >= self.SLOW_CLICK_COOLDOWN

    @property
    def slow_click_cooldown(self):
        if not self.last_slow_click or self.can_make_slow_click:
            return timedelta(0)
        return (self.last_slow_click + self.SLOW_CLICK_COOLDOWN) - timezone.now()

    def get_daily_points(self, date=None):
        date = date or timezone.now().date()
        return self.history.filter(
            created_at__date=date,
            type__in=['slow_click', 'fast_click', 'bonus']
        ).aggregate(total=Sum('amount'))['total'] or 0

    def get_weekly_points(self):
        week_ago = timezone.now() - timedelta(days=7)
        return self.history.filter(
            created_at__gte=week_ago,
            type__in=['slow_click', 'fast_click', 'bonus']
        ).aggregate(total=Sum('amount'))['total'] or 0

    @transaction.atomic
    def add_points(self, amount, source='other'):
        if amount <= 0:
            raise ValidationError("Amount must be positive")
        
        self.points += amount
        self.total_points += amount
        self.save(update_fields=['points', 'total_points'])
        
        PointHistory.objects.create(
            user_points=self,
            amount=amount,
            type=source,
            reason=f"Начисление: {source}"
        )
        return True

    @transaction.atomic
    def spend_points(self, amount, reason=''):
        if amount <= 0:
            raise ValidationError("Amount must be positive")
        if self.points < amount:
            raise ValidationError("Not enough points")
            
        self.points -= amount
        self.save(update_fields=['points'])
        
        PointHistory.objects.create(
            user_points=self,
            amount=-amount,
            type='spend',
            reason=reason or f"Списание: {amount}"
        )
        return True

    @transaction.atomic
    def make_slow_click(self):
        if not self.can_make_slow_click:
            return False
            
        self.last_slow_click = timezone.now()
        return self.add_points(1, 'slow_click')

    @transaction.atomic
    def make_fast_click(self):
        self._reset_daily_counters_if_needed()
        
        # Устанавливаем время первого клика, если это первый клик за период
        if self.fast_clicks_today == 0:
            self.first_click_today = timezone.now()
            self.save(update_fields=['first_click_today'])
        
        if self.fast_clicks_today >= self.DAILY_FAST_CLICKS_LIMIT:
            return (False, 0)
            
        min_amount = self.FAST_CLICK_UPGRADED_MIN if self.is_upgraded else self.FAST_CLICK_MIN
        max_amount = self.FAST_CLICK_UPGRADED_MAX if self.is_upgraded else self.FAST_CLICK_MAX
        amount = random.randint(min_amount, max_amount)
        
        if self.add_points(amount, 'fast_click'):
            self.fast_clicks_today += 1
            self.save(update_fields=['fast_clicks_today'])
            return (True, amount)
        return (False, 0)

    @transaction.atomic
    def upgrade_account(self):
        if self.is_upgraded:
            raise ValidationError("Already upgraded")
        if self.points < self.UPGRADE_COST:
            raise ValidationError("Not enough points")
            
        self.spend_points(self.UPGRADE_COST, "Account upgrade")
        self.is_upgraded = True
        self.save(update_fields=['is_upgraded'])
        return True

    def _reset_daily_counters_if_needed(self):
        now = timezone.now()
        # Если поле first_click_today не установлено, но fast_clicks_today > 0,
        # это означает, что запись была создана до добавления этого поля
        if self.first_click_today is None and self.fast_clicks_today > 0:
            self.fast_clicks_today = 0
            self.save(update_fields=['fast_clicks_today'])
            return
        
        # Если first_click_today установлено, проверяем, нужно ли сбросить счетчик
        if self.first_click_today:
            # Сбрасываем счетчик, если прошло более 24 часов
            if now - self.first_click_today >= timedelta(days=1):
                self.fast_clicks_today = 0
                self.first_click_today = None
                self.save(update_fields=['fast_clicks_today', 'first_click_today'])
        # Если счетчик кликов больше 0, но время первого клика не установлено,
        # это означает новый день (или ошибка состояния)
        elif self.fast_clicks_today > 0:
            self.fast_clicks_today = 0
            self.save(update_fields=['fast_clicks_today'])

class PointHistory(models.Model):
    TYPE_CHOICES = [
        ('slow_click', 'Медленный клик'),
        ('fast_click', 'Быстрый клик'),
        ('spend', 'Списание'),
        ('chat', 'Чат'),
        ('upgrade', 'Улучшение'),
        ('bonus', 'Бонус'),
        ('other', 'Другое'),
    ]
    
    user_points = models.ForeignKey(UserPoints, on_delete=models.CASCADE, related_name='history')
    amount = models.IntegerField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user_points']),
        ]

    def __str__(self):
        return f"{self.user_points.user.username}: {self.amount} ({self.type})"

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    content = models.TextField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True)
    points_spent = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user']),
        ]

    def save(self, *args, **kwargs):
        if not self.content.strip():
            raise ValidationError("Message cannot be empty")
        super().save(*args, **kwargs)

    @transaction.atomic
    def soft_delete(self):
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])
        if self.points_spent > 0:
            try:
                user_points = UserPoints.objects.get(user=self.user)
                user_points.add_points(self.points_spent, 'refund')
            except UserPoints.DoesNotExist:
                pass