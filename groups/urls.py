from django.urls import path
from . import views

urlpatterns = [
    # ASOSIY SAHIFALAR
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),

    # ADMIN PANEL
    path('admin-panel/', views.admin_panel, name='admin_panel'),

    # GROUP
    path('group/<int:pk>/', views.group_detail, name='group_detail'),
    path('group/add/', views.group_add, name='group_add'),
    path('group/edit/<int:pk>/', views.group_edit, name='group_edit'),
    path('group/delete/<int:pk>/', views.group_delete, name='group_delete'),

    # KATEGORIYALAR
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # GURUH KATEGORIYALARI
    path('groups/<int:group_id>/categories/', views.group_categories_manage, name='group_categories_manage'),
    path('groups/<int:group_id>/categories/add/', views.group_category_add, name='group_category_add'),
    path('groups/categories/remove/<int:group_category_id>/', views.group_category_remove, name='group_category_remove'),

    # KATEGORIYA SAVOLLARI
    path('categories/<int:category_id>/questions/', views.category_questions_list, name='category_questions_list'),
    path('categories/<int:category_id>/questions/add/', views.category_question_add, name='category_question_add'),
    path('questions/<int:question_id>/edit/', views.category_question_edit, name='category_question_edit'),
    path('questions/<int:question_id>/delete/', views.category_question_delete, name='category_question_delete'),

    # STUDENTLAR
    path('users/', views.student_list, name='student_list'),
    path('user/add/', views.student_add, name='student_add'),
    path('user/edit/<int:pk>/', views.student_edit, name='student_edit'),
    path('user/delete/<int:pk>/', views.student_delete, name='student_delete'),

    # STUDENT PANEL
    path('student-panel/', views.student_panel, name='student_panel'),
  path('users/bulk-delete/', views.student_bulk_delete, name='student_bulk_delete'),
    # ADMIN BOSHQARUVI
    path('make-admin/', views.make_admin, name='make_admin'),
    path('admin-list/', views.admin_list, name='admin_list'),
    path('admin-add/', views.admin_add, name='admin_add'),
    path('admin-edit/<int:admin_id>/', views.admin_edit, name='admin_edit'),
    path('admin-delete/<int:user_id>/', views.admin_delete, name='admin_delete'),
    # QUIZ ADMIN
    path('quiz/admin/', views.quiz_admin, name='quiz_admin'),
    path('quiz/add/', views.quiz_add_question, name='quiz_add_question'),
    path('quiz/edit/<int:question_id>/', views.quiz_edit_question, name='quiz_edit_question'),
    path('quiz/delete/<int:question_id>/', views.quiz_delete_question, name='quiz_delete_question'),

    # QUIZ SESSION
    path('quiz/start/', views.start_exam_api, name='start_exam_api'),
    path('quiz/stop/', views.stop_exam_api, name='stop_exam_api'),
   path('quiz/check/', views.check_exam_api, name='check_exam_api'), 
     path('quiz/check-status/', views.quiz_check_status, name='quiz_check_status'),
    # STUDENT QUIZ
    path('quiz/take/<int:group_id>/', views.quiz_take, name='quiz_take'),
    path('quiz/submit/', views.quiz_submit, name='quiz_submit'),
    path('quiz/results/<int:group_id>/', views.quiz_results, name='quiz_results'),

    # IMTIHON BOSHQARUVI
    path('exam/control/<int:group_id>/', views.exam_control, name='exam_control'),

    # GURUH IMTIHON SOZLAMALARI
    path('group/exam-config/<int:group_id>/', views.group_exam_config, name='group_exam_config'),
    path('group/questions-preview/<int:group_id>/', views.group_questions_preview, name='group_questions_preview'),

    # QOIDALAR
    path('rules-edit/', views.rules_edit, name='rules_edit'),

    # API
    path('api/admin-detail/<int:admin_id>/', views.admin_detail_api, name='admin_detail_api'),
    path('api/admin-update/', views.admin_update, name='admin_update'),
    path('api/admin-get-plain-password/<int:admin_id>/', views.admin_get_plain_password, name='admin_get_plain_password'),
    path('api/admin-update-password/', views.admin_update_password, name='admin_update_password'),
]