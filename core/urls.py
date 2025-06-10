from django.urls import path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.admin.views.decorators import staff_member_required
from .views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),

    # URL для лекций
    path('lectures/', LectureListView.as_view(), name='lectures_list'),
    path('lectures/add/', staff_member_required(AddLectureView.as_view()), name='add_lecture'),
    path('lectures/<int:pk>/', LectureDetailView.as_view(), name='lecture_detail'),
    path('lectures/<int:pk>/delete/', staff_member_required(delete_lecture), name='delete_lecture'),
    path('lectures/<int:pk>/edit/', staff_member_required(LectureUpdateView.as_view()), name='edit_lecture'),
    
    #упражнения
    path('exercise/', exercise_list, name='exercise'),
    path('add/', add_exercise, name='add_exercise'),
    path('<int:pk>/', exercise_detail, name='exercise_detail'),
    path('<int:pk>/edit/', edit_exercise, name='edit_exercise'),


    # URL для тестов
    path('tests/', TestListView.as_view(), name='test_list'),
    path('tests/add/', TestCreateView.as_view(), name='add_test'),
    path('tests/<int:pk>/', test_detail, name='test_detail'),
    path('tests/<int:test_id>/add-question/', add_question, name='add_question'),
    path('tests/<int:pk>/questions/', test_questions, name='test_questions'),
    path('tests/<int:pk>/take/', take_test, name='take_test'),
    path('tests/<int:pk>/results/<int:score>/', test_results, name='test_results'),
    path('tests/<int:pk>/delete/', staff_member_required(delete_test), name='delete_test'),
    path('tests/<int:pk>/enter-password/', enter_test_password, name='enter_test_password'),
    path('tests/<int:pk>/edit/', staff_member_required(edit_test), name='edit_test'),


    # Аутентификация
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', custom_logout, name='logout'),
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='user/password_reset.html',
             email_template_name='user/password_reset_email.html',
             html_email_template_name='user/password_reset_email.html',  # Добавлено для HTML-писем
             subject_template_name='user/password_reset_subject.txt',
         ), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='user/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='user/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='user/password_reset_complete.html'
         ), 
         name='password_reset_complete'),

    


    path('video-lectures/', video_lecture_view, name='video_lectures'),
    path('video-lectures/add/', login_required(add_video_lecture_view), name='add_video_lecture'),
    path('video-lectures/<int:lecture_id>/edit/', login_required(edit_video_lecture_view), name='edit_video_lecture'),
    path('video-lectures/<int:lecture_id>/delete/', login_required(delete_video_lecture_view), name='delete_video_lecture'),

    #Презентации
    path('presentations/', PresentationListView.as_view(), name='presentation-list'),
    path('presentations/create/', PresentationCreateView.as_view(), name='presentation-create'),
    path('presentations/<int:pk>/', PresentationDetailView.as_view(), name='presentation-detail'),
    path('presentations/<int:pk>/delete/', PresentationDeleteView.as_view(), name='presentation-delete'),


    #Mathsolver
    path('math-solver/', math_solver_base_view, name='math_solver_base'),
    path('math-solver/linear_algebra/', linear_algebra_base_view, name='linear_algebra_base'),
    path('math-solver/conic/', conic_view, name='conic'),
    path('math-solver/calculus/', calculus_view, name='calculus'),
    path('math-solver/trigonometry/', trigonometry_view, name='trigonometry'),
    path('math-solver/general_maths/', general_maths_view, name='general_maths'),
    path('math-solver/basic_converters/', basic_converters_view, name='basic_converters'),
    path('math-solver/graphs_shapes/', graphs_shapes_view, name='graphs_shapes'),
    path('math-solver/equations/', equations_view, name='equations'),
    path('math-solver/binary/', binary_view, name='binary'),
    path('math-solver/complex/', complex_view, name='complex'),
    path('math-solver/probability/', probability_view, name='probability'),
    path('math-solver/statistics/', statistics_view, name='statistics'),
    path('math-solver/mensuration/', mensuration_view, name='mensuration'),
    path('math-solver/mensuration/3dshapes', shapes3d_view, name='3dshape'),
    path('math-solver/mensuration/shapes2d', shapes2d_view, name='shapes2d'),
    path('math-solver/mensuration/introduction', introduction_view, name='introduction'),
    path('math-solver/equation/roots/', roots, name='roots'),
    path('math-solver/statistics/static_analys', static_analys, name='static_analys'),
    path('math-solver/statistics/weight_mean', weight_mean, name='weight_mean'),
    path('math-solver/statistics/moments', moments, name='moments'),
    path('math-solver/statistics/sensitivity', sensitivity, name='sensitivity'),
    path('math-solver/statistics/deviation', deviation, name='deviation'),
    path('math-solver/statistics/ttest', ttest, name='ttest'),


    # Основной список
    path('dictionary/', DictionaryView.as_view(), name='dictionary-list'),
    path('dictionary/', DictionaryView.as_view(), name='dictionary'),
    path('dictionary/add/', AddWordView.as_view(), name='dictionary-add'),
    path('dictionary/edit/<int:pk>/', UpdateWordView.as_view(), name='edit-word'),
    path('dictionary/delete/<int:pk>/', DeleteWordView.as_view(), name='delete-word'),

    # Grind URLs
    path('grind/', grind_main, name='grind_main'),
    path('grind/slow-click/', add_slow_click, name='slow_click'),
    path('grind/fast-click/', add_fast_click, name='fast_click'),
    path('grind/upgrade/', upgrade, name='upgrade'),
    path('grind/points-state/', get_points_state, name='points_state'),
    
    # Profile URLs
    path('profile/', profile_view, name='profile'),
    
    # Chat URLs
    path('chat/', chat_view, name='chat'),
    path('send/', send_message, name='send_message'),
    path('messages/', get_messages, name='get_messages'),
    path('online/', online_users, name='online_users'),

    #converter

    path('converter/', ConverterView.as_view(), name='converter'),

    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)