from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Count
import json
import random

from .models import (
    Group, Student, ExamSession, ExamResult, ExamControl, 
    AdminPassword, Rules, QuizQuestion, QuizSession, QuizResult,
    Category, GroupCategory, GroupExamConfig, UserExamAttempt
)
from .forms import GroupForm, RegisterForm, LoginForm


# ============ YORDAMCHI FUNKSIYALAR ============
def is_admin_user(user):
    return user.is_staff or user.is_superuser


def is_superuser(user):
    return user.is_superuser


# ============ ASOSIY SAHIFALAR ============
def home(request):
    return render(request, 'groups/home.html')


def user_login(request):
    if request.user.is_authenticated:
        if is_admin_user(request.user):
            return redirect('admin_panel')
        else:
            return redirect('student_panel')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Xush kelibsiz, {user.get_full_name() or user.username}!')
                if is_admin_user(user):
                    return redirect('admin_panel')
                else:
                    return redirect('student_panel')
            else:
                messages.error(request, 'Username yoki parol xato!')
        else:
            messages.error(request, 'Username yoki parol xato!')
    else:
        form = LoginForm()
    
    return render(request, 'groups/login.html', {'form': form, 'title': 'Tizimga kirish'})


def user_register(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )
            group = form.cleaned_data['group']
            student, created = Student.objects.get_or_create(user=user)
            student.group = group
            student.save()
            messages.success(request, f'Tabriklaymiz! Siz muvaffaqiyatli ro\'yxatdan o\'tdingiz!')
            messages.info(request, f'Siz {group.name} guruhiga qo\'shildingiz!')
            login(request, user)
            return redirect('student_panel')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = RegisterForm()
    
    return render(request, 'groups/register.html', {'form': form, 'title': 'Ro\'yxatdan o\'tish'})


def user_logout(request):
    logout(request)
    messages.info(request, 'Tizimdan chiqdingiz!')
    return redirect('home')


# ============ ADMIN PANEL ============
@login_required
@user_passes_test(is_admin_user)
def admin_panel(request):
    groups = Group.objects.all()
    students = Student.objects.all().select_related('user', 'group')
    admins = User.objects.filter(is_staff=True)
    
    for group in groups:
        if not hasattr(group, 'exam_config'):
            GroupExamConfig.objects.create(group=group)
        if not hasattr(group, 'exam_control'):
            ExamControl.objects.create(group=group)
    
    context = {
        'groups': groups,
        'students': students,
        'total_groups': groups.count(),
        'total_students': students.count(),
        'total_admins': admins.count(),
        'admins': admins,
        'total_categories': Category.objects.count(),
        'total_questions': QuizQuestion.objects.count(),
    }
    return render(request, 'groups/admin_panel.html', context)


# ============ GROUP FUNKSIYALARI ============
@login_required
def group_detail(request, pk):
    group = get_object_or_404(Group, pk=pk)
    students = group.students.all().select_related('user')
    exam_control, created = ExamControl.objects.get_or_create(group=group)
    
    context = {
        'group': group,
        'students': students,
        'exam_control': exam_control,
    }
    return render(request, 'groups/group_detail.html', context)


@login_required
@user_passes_test(is_admin_user)
def group_add(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Guruh qo\'shildi!')
            return redirect('admin_panel')
    else:
        form = GroupForm()
    return render(request, 'groups/group_form.html', {'form': form, 'title': 'Guruh qo\'shish'})


@login_required
@user_passes_test(is_admin_user)
def group_edit(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, 'Guruh tahrirlandi!')
            return redirect('admin_panel')
    else:
        form = GroupForm(instance=group)
    return render(request, 'groups/group_form.html', {'form': form, 'title': 'Guruhni tahrirlash'})


@login_required
@user_passes_test(is_admin_user)
def group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    if request.method == 'POST':
        group.delete()
        messages.success(request, 'Guruh o\'chirildi!')
        return redirect('admin_panel')
    return render(request, 'groups/group_confirm_delete.html', {'group': group})


# ============ STUDENT/USER FUNKSIYALARI ============
@login_required
@user_passes_test(is_admin_user)
def student_list(request):
    students = Student.objects.all().select_related('user', 'group')
    return render(request, 'groups/student_list.html', {'students': students})


@login_required
@user_passes_test(is_admin_user)
def student_add(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )
            group = form.cleaned_data['group']
            Student.objects.create(user=user, group=group)
            messages.success(request, f'{user.get_full_name()} foydalanuvchi qo\'shildi!')
            return redirect('student_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = RegisterForm()
    return render(request, 'groups/student_form.html', {'form': form, 'title': 'Foydalanuvchi qo\'shish'})


@login_required
@user_passes_test(is_admin_user)
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        user = student.user
        user.username = request.POST.get('username')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.save()
        
        group_id = request.POST.get('group')
        if group_id:
            student.group = Group.objects.get(id=group_id)
            student.save()
        
        messages.success(request, 'Foydalanuvchi tahrirlandi!')
        return redirect('student_list')
    
    context = {
        'student': student,
        'groups': Group.objects.all(),
    }
    return render(request, 'groups/student_edit.html', context)


@login_required
@user_passes_test(is_admin_user)
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        user = student.user
        student.delete()
        user.delete()
        messages.success(request, 'Foydalanuvchi o\'chirildi!')
        return redirect('student_list')
    return render(request, 'groups/student_confirm_delete.html', {'student': student})


@login_required
def student_panel(request):
    try:
        student = request.user.student_profile
        rules = Rules.objects.first()
        
        exam_active = False
        if student.group:
            exam_control, created = ExamControl.objects.get_or_create(group=student.group)
            exam_active = exam_control.is_active
        
        context = {
            'student': student,
            'rules': rules,
            'exam_active': exam_active,
        }
        return render(request, 'groups/student_panel.html', context)
    except Exception as e:
        messages.error(request, 'Profil topilmadi!')
        return redirect('home')


# ============ ADMIN BOSHQARUVI ============
@login_required
@user_passes_test(is_superuser)
def make_admin(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        is_superuser_val = request.POST.get('is_superuser') == 'on'
        
        try:
            user = User.objects.get(id=user_id)
            user.is_staff = True
            if is_superuser_val:
                user.is_superuser = True
            user.save()
            
            if is_superuser_val:
                messages.success(request, f'{user.get_full_name()} muvaffaqiyatli SUPERUSER qilindi!')
            else:
                messages.success(request, f'{user.get_full_name()} muvaffaqiyatli ADMIN qilindi!')
        except User.DoesNotExist:
            messages.error(request, 'Foydalanuvchi topilmadi!')
        
        return redirect('admin_panel')
    
    return redirect('admin_panel')


@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_list(request):
    admins = User.objects.filter(is_staff=True).select_related('student_profile__group')
    
    context = {
        'admins': admins,
        'total_admins': admins.count(),
    }
    return render(request, 'groups/admin_list.html', context)


@login_required
@user_passes_test(is_superuser)
def remove_admin(request, user_id):
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            if user.is_superuser and request.user.id == user.id:
                messages.error(request, "O'zingizni superuserlikdan chiqara olmaysiz!")
            else:
                user.is_staff = False
                user.is_superuser = False
                user.save()
                messages.success(request, f'{user.get_full_name()} admin huquqidan mahrum qilindi!')
        except User.DoesNotExist:
            messages.error(request, 'Foydalanuvchi topilmadi!')
    
    return redirect('admin_list')


@login_required
@user_passes_test(is_superuser)
def admin_add(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        is_superuser_val = request.POST.get('is_superuser') == 'on'
        email = request.POST.get('email', '').strip()
        
        errors = []
        if not first_name:
            errors.append("Ism kiritilishi shart!")
        if not last_name:
            errors.append("Familiya kiritilishi shart!")
        if not username:
            errors.append("Username kiritilishi shart!")
        if not password:
            errors.append("Parol kiritilishi shart!")
        if password != password_confirm:
            errors.append("Parollar mos kelmadi!")
        if User.objects.filter(username=username).exists():
            errors.append(f"'{username}' username allaqachon mavjud!")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'groups/admin_add.html')
        
        admin_user = User.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=make_password(password),
            is_staff=True,
            is_superuser=is_superuser_val,
            is_active=True
        )
        
        AdminPassword.objects.create(
            user=admin_user,
            plain_password=password
        )
        
        if is_superuser_val:
            messages.success(request, f'{first_name} {last_name} SUPERUSER sifatida qo\'shildi!')
        else:
            messages.success(request, f'{first_name} {last_name} ADMIN sifatida qo\'shildi!')
        
        messages.info(request, f'Login: {username} | Parol: {password}')
        return redirect('admin_list')
    
    return render(request, 'groups/admin_add.html')


@login_required
@user_passes_test(is_superuser)
def admin_edit(request, admin_id):
    admin = get_object_or_404(User, id=admin_id)
    
    try:
        admin_pass = AdminPassword.objects.get(user=admin)
        plain_password = admin_pass.plain_password
    except AdminPassword.DoesNotExist:
        plain_password = ''
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        is_superuser_val = request.POST.get('is_superuser') == 'on'
        
        errors = []
        
        if not username:
            errors.append("Username kiritilishi shart!")
        
        if User.objects.filter(username=username).exclude(id=admin.id).exists():
            errors.append(f"'{username}' username allaqachon mavjud!")
        
        if password and password != password_confirm:
            errors.append("Parollar mos kelmadi!")
        
        if password and len(password) < 4:
            errors.append("Parol kamida 4 ta belgidan iborat bo'lishi kerak!")
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            admin.first_name = first_name
            admin.last_name = last_name
            admin.username = username
            admin.email = email
            admin.is_superuser = is_superuser_val
            admin.is_staff = True
            
            if password:
                admin.set_password(password)
                admin_pass, created = AdminPassword.objects.get_or_create(user=admin)
                admin_pass.plain_password = password
                admin_pass.save()
            
            admin.save()
            messages.success(request, f'{admin.get_full_name()} ma\'lumotlari yangilandi!')
            return redirect('admin_list')
    
    context = {
        'admin': admin,
        'plain_password': plain_password,
    }
    return render(request, 'groups/admin_edit.html', context)


@login_required
@user_passes_test(is_superuser)
def admin_delete(request, user_id):
    try:
        admin_user = User.objects.get(id=user_id)
        
        if request.user.id == admin_user.id:
            messages.error(request, "O'zingizni o'chira olmaysiz!")
            return redirect('admin_panel')
        
        full_name = admin_user.get_full_name()
        admin_user.delete()
        messages.success(request, f'{full_name} admin o\'chirildi!')
    except User.DoesNotExist:
        messages.error(request, 'Admin topilmadi!')
    
    return redirect('admin_panel')


@login_required
@user_passes_test(is_superuser)
def admin_get_plain_password(request, admin_id):
    try:
        admin = User.objects.get(id=admin_id)
        
        try:
            admin_pass = AdminPassword.objects.get(user=admin)
            plain_password = admin_pass.plain_password
        except AdminPassword.DoesNotExist:
            plain_password = "Parol saqlanmagan"
        
        return JsonResponse({
            'success': True,
            'admin_id': admin.id,
            'admin_name': admin.get_full_name(),
            'username': admin.username,
            'password': plain_password,
            'is_superuser': admin.is_superuser,
        })
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Admin topilmadi!'})


@login_required
@user_passes_test(is_superuser)
def admin_update_password(request):
    if request.method == 'POST':
        admin_id = request.POST.get('admin_id')
        new_password = request.POST.get('password')
        
        try:
            admin = User.objects.get(id=admin_id)
            
            if new_password and len(new_password) >= 4:
                admin.set_password(new_password)
                admin.save()
                
                admin_pass, created = AdminPassword.objects.get_or_create(user=admin)
                admin_pass.plain_password = new_password
                admin_pass.save()
                
                return JsonResponse({'success': True, 'message': 'Parol yangilandi!'})
            else:
                return JsonResponse({'success': False, 'message': 'Parol kamida 4 belgi bo\'lishi kerak!'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Admin topilmadi!'})
    
    return JsonResponse({'success': False, 'message': 'Xato so\'rov!'})


# ============ QUIZ ADMIN FUNKSIYALARI ============
@login_required
@user_passes_test(is_admin_user)
def quiz_admin(request):
    questions = QuizQuestion.objects.all().select_related('category').order_by('-created_at')
    categories = Category.objects.all()
    groups = Group.objects.all()
    
    context = {
        'questions': questions,
        'categories': categories,
        'groups': groups,
    }
    return render(request, 'groups/quiz_admin.html', context)


@login_required
@user_passes_test(is_admin_user)
def quiz_add_question(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        question_text = request.POST.get('question_text', '').strip()
        correct_answer = request.POST.get('correct_answer', '').strip().lower()
        
        if not question_text or not correct_answer:
            messages.error(request, 'Savol matni va to\'g\'ri javob kiritilishi shart!')
            return redirect('quiz_admin')
        
        if category_id and category_id != '':
            category = get_object_or_404(Category, id=category_id)
            QuizQuestion.objects.create(
                category=category,
                question_text=question_text,
                correct_answer=correct_answer
            )
            messages.success(request, f'Savol "{category.name}" kategoriyasiga qo\'shildi!')
        else:
            messages.error(request, 'Kategoriya tanlash shart!')
        
        return redirect('quiz_admin')
    
    return redirect('quiz_admin')


@login_required
@user_passes_test(is_admin_user)
def quiz_edit_question(request, question_id):
    question = get_object_or_404(QuizQuestion, id=question_id)
    
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        question_text = request.POST.get('question_text', '').strip()
        correct_answer = request.POST.get('correct_answer', '').strip().lower()
        
        if not question_text or not correct_answer:
            messages.error(request, 'Savol matni va to\'g\'ri javob kiritilishi shart!')
        else:
            question.question_text = question_text
            question.correct_answer = correct_answer
            
            if category_id and category_id != '':
                question.category = get_object_or_404(Category, id=category_id)
            
            question.save()
            messages.success(request, 'Savol tahrirlandi!')
        
        return redirect('quiz_admin')
    
    categories = Category.objects.all()
    context = {
        'question': question,
        'categories': categories,
    }
    return render(request, 'groups/quiz_edit.html', context)


@login_required
@user_passes_test(is_admin_user)
def quiz_delete_question(request, question_id):
    question = get_object_or_404(QuizQuestion, id=question_id)
    question.delete()
    messages.success(request, 'Savol o\'chirildi!')
    return redirect('quiz_admin')


# ============ QUIZ SESSION BOSHQARUV ============
@csrf_exempt
@login_required
@user_passes_test(is_admin_user)
def start_exam_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        group_id = data.get('group_id')
        
        try:
            group = Group.objects.get(id=group_id)
            
            group_categories = GroupCategory.objects.filter(group=group).values_list('category_id', flat=True)
            questions_count = QuizQuestion.objects.filter(category_id__in=group_categories).count()
            
            if questions_count == 0:
                return JsonResponse({
                    'success': False, 
                    'message': 'Avval guruhga kategoriya va savollar qo\'shing!'
                })
            
            exam_control, created = ExamControl.objects.get_or_create(group=group)
            exam_control.is_active = True
            exam_control.started_at = timezone.now()
            exam_control.save()
            
            QuizSession.objects.filter(group=group, is_active=True).update(is_active=False, ended_at=timezone.now())
            
            session = QuizSession.objects.create(
                group=group,
                is_active=True,
                started_at=timezone.now(),
                created_by=request.user
            )
            
            config, created = GroupExamConfig.objects.get_or_create(group=group)
            
            return JsonResponse({
                'success': True,
                'session_id': session.id,
                'message': f'✅ Test boshlandi! {questions_count} ta savol mavjud. Har bir talaba {config.questions_per_student} ta random savol oladi.'
            })
        except Group.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Guruh topilmadi!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Xatolik: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Xato so\'rov!'})


@csrf_exempt
@login_required
@user_passes_test(is_admin_user)
def stop_exam_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        group_id = data.get('group_id')
        
        try:
            group = Group.objects.get(id=group_id)
            session = QuizSession.objects.filter(group=group, is_active=True).first()
            
            if session:
                session.is_active = False
                session.ended_at = timezone.now()
                session.save()
            
            exam_control, created = ExamControl.objects.get_or_create(group=group)
            exam_control.is_active = False
            exam_control.save()
            
            return JsonResponse({
                'success': True,
                'message': f'⛔ Test to\'xtatildi!'
            })
        except Group.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Guruh topilmadi!'})
    
    return JsonResponse({'success': False, 'message': 'Xato so\'rov!'})


@login_required
def quiz_take(request, group_id):
    try:
        student = request.user.student_profile
    except:
        messages.error(request, 'Student profili topilmadi!')
        return redirect('home')
    
    group = get_object_or_404(Group, id=group_id)
    
    if student.group != group:
        messages.error(request, 'Siz bu guruhga tegishli emassiz!')
        return redirect('student_panel')
    
    # Test faolligini tekshirish
    active_session = QuizSession.objects.filter(group=group, is_active=True).first()
    exam_control, created = ExamControl.objects.get_or_create(group=group)
    is_exam_active = active_session is not None or exam_control.is_active
    
    if not is_exam_active:
        context = {
            'group': group,
            'student': student,
            'is_exam_active': False,
        }
        return render(request, 'groups/quiz_take.html', context)
    
    # Guruh sozlamalari
    config, created = GroupExamConfig.objects.get_or_create(group=group)
    
    # Urinishlarni tekshirish
    attempts_count = UserExamAttempt.objects.filter(
        student=student, exam_session=active_session, is_completed=True
    ).count() if active_session else 0
    
    if attempts_count >= config.max_attempts:
        messages.warning(request, f"Siz testni {config.max_attempts} marta topshirgansiz!")
        return redirect('student_panel')
    
    # Urinish yaratish
    attempt, created = UserExamAttempt.objects.get_or_create(
        student=student,
        exam_session=active_session,
        defaults={'is_completed': False, 'selected_questions': []}
    ) if active_session else (None, False)
    
    if attempt and attempt.is_completed:
        messages.info(request, "Siz testni topshirgansiz!")
        return redirect('student_panel')
    
    # Random savol tanlash
    group_categories = GroupCategory.objects.filter(group=group).values_list('category_id', flat=True)
    all_questions = list(QuizQuestion.objects.filter(category_id__in=group_categories))
    
    if len(all_questions) == 0:
        messages.error(request, 'Savol mavjud emas!')
        return redirect('student_panel')
    
    if attempt and (not attempt.selected_questions or len(attempt.selected_questions) == 0):
        question_count = min(config.questions_per_student, len(all_questions))
        selected_questions = random.sample(all_questions, question_count)
        
        if config.random_order:
            random.shuffle(selected_questions)
        
        attempt.selected_questions = [q.id for q in selected_questions]
        attempt.save()
        selected = selected_questions
    elif attempt:
        selected = list(QuizQuestion.objects.filter(id__in=attempt.selected_questions))
        if config.random_order:
            random.shuffle(selected)
    else:
        selected = []
    
    context = {
        'group': group,
        'active_session': active_session,
        'student': student,
        'questions': selected,
        'total_questions': len(selected),
        'time_limit': config.time_limit,
        'is_exam_active': True,
    }
    return render(request, 'groups/quiz_take.html', context)


@csrf_exempt
@login_required
def quiz_submit(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            group_id = data.get('group_id')
            answers = data.get('answers', {})
            
            student = request.user.student_profile
            group = Group.objects.get(id=group_id)
            active_session = QuizSession.objects.filter(group=group, is_active=True).first()
            
            if not active_session:
                return JsonResponse({'success': False, 'message': 'Test faol emas!'})
            
            attempt = UserExamAttempt.objects.filter(
                student=student, exam_session=active_session, is_completed=False
            ).first()
            
            if not attempt:
                return JsonResponse({'success': False, 'message': 'Urinish topilmadi!'})
            
            selected_questions = QuizQuestion.objects.filter(id__in=attempt.selected_questions)
            
            score = 0
            total = selected_questions.count()
            
            for question in selected_questions:
                user_answer = None
                for key, value in answers.items():
                    if str(question.id) in key:
                        user_answer = value.strip().lower()
                        break
                
                if user_answer and user_answer == question.correct_answer.lower().strip():
                    score += 1
            
            QuizResult.objects.create(
                student=student,
                quiz_session=active_session,
                score=score,
                total_questions=total,
                answers=answers
            )
            
            attempt.is_completed = True
            attempt.completed_at = timezone.now()
            attempt.save()
            
            percentage = round((score / total) * 100, 1) if total > 0 else 0
            
            return JsonResponse({
                'success': True,
                'score': score,
                'total': total,
                'percentage': percentage,
                'message': f'Test yakunlandi! Natija: {score}/{total} ({percentage}%)'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Faqat POST so\'rov!'})


@login_required
def quiz_results(request, group_id):
    if not is_admin_user(request.user):
        return redirect('home')
    
    group = get_object_or_404(Group, id=group_id)
    sessions = QuizSession.objects.filter(group=group).order_by('-started_at')
    
    last_session = sessions.first()
    results = []
    if last_session:
        results = QuizResult.objects.filter(quiz_session=last_session).select_related('student')
    
    context = {
        'group': group,
        'sessions': sessions,
        'last_session': last_session,
        'results': results,
    }
    return render(request, 'groups/quiz_results.html', context)


# ============ GURUH IMTIHON SOZLAMALARI ============
@login_required
@user_passes_test(is_admin_user)
def group_exam_config(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    config, created = GroupExamConfig.objects.get_or_create(group=group)
    
    group_categories = GroupCategory.objects.filter(group=group).select_related('category')
    category_ids = [gc.category.id for gc in group_categories]
    total_questions = QuizQuestion.objects.filter(category_id__in=category_ids).count()
    
    if request.method == 'POST':
        questions_per_student = int(request.POST.get('questions_per_student', 5))
        random_order = request.POST.get('random_order') == 'on'
        show_correct_answer = request.POST.get('show_correct_answer') == 'on'
        time_limit = int(request.POST.get('time_limit', 0))
        max_attempts = int(request.POST.get('max_attempts', 1))
        
        if questions_per_student > total_questions and total_questions > 0:
            messages.warning(request, f'Diqqat! {total_questions} ta savol bor, siz {questions_per_student} ta so\'rayapsiz!')
            questions_per_student = total_questions
        
        config.questions_per_student = questions_per_student
        config.random_order = random_order
        config.show_correct_answer = show_correct_answer
        config.time_limit = time_limit
        config.max_attempts = max_attempts
        config.save()
        
        messages.success(request, f'✅ Sozlamalar saqlandi! Har bir talaba {questions_per_student} ta random savol oladi.')
        return redirect('group_exam_config', group_id=group.id)
    
    context = {
        'group': group,
        'config': config,
        'total_questions': total_questions,
        'group_categories': group_categories,
    }
    return render(request, 'groups/group_exam_config.html', context)


@login_required
@user_passes_test(is_admin_user)
def group_questions_preview(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    config, created = GroupExamConfig.objects.get_or_create(group=group)
    
    group_categories = GroupCategory.objects.filter(group=group).values_list('category_id', flat=True)
    all_questions = list(QuizQuestion.objects.filter(category_id__in=group_categories))
    
    question_count = min(config.questions_per_student, len(all_questions))
    random_questions = random.sample(all_questions, question_count) if question_count > 0 else []
    
    context = {
        'group': group,
        'config': config,
        'random_questions': random_questions,
        'total_available': len(all_questions),
    }
    return render(request, 'groups/group_questions_preview.html', context)


# ============ KATEGORIYALAR BOSHQARUVI ============
@login_required
@user_passes_test(is_admin_user)
def category_list(request):
    categories = Category.objects.all().annotate(
        questions_count=Count('quiz_questions'),
        groups_count=Count('group_categories')
    )
    
    context = {
        'categories': categories,
        'total_categories': categories.count(),
    }
    return render(request, 'groups/category_list.html', context)


@login_required
@user_passes_test(is_admin_user)
def category_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, 'Kategoriya nomi kiritilishi shart!')
        elif Category.objects.filter(name__iexact=name).exists():
            messages.error(request, f'"{name}" nomli kategoriya allaqachon mavjud!')
        else:
            Category.objects.create(name=name, description=description)
            messages.success(request, f'✅ "{name}" kategoriyasi qo\'shildi!')
            return redirect('category_list')
    
    return render(request, 'groups/category_form.html', {'title': 'Kategoriya qo\'shish'})


@login_required
@user_passes_test(is_admin_user)
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            messages.error(request, 'Kategoriya nomi kiritilishi shart!')
        elif Category.objects.filter(name__iexact=name).exclude(pk=pk).exists():
            messages.error(request, f'"{name}" nomli kategoriya allaqachon mavjud!')
        else:
            category.name = name
            category.description = description
            category.save()
            messages.success(request, f'✅ "{name}" kategoriyasi yangilandi!')
            return redirect('category_list')
    
    context = {'category': category, 'title': 'Kategoriyani tahrirlash'}
    return render(request, 'groups/category_form.html', context)


@login_required
@user_passes_test(is_admin_user)
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        questions_count = category.quiz_questions.count()
        category_name = category.name
        category.delete()
        
        if questions_count > 0:
            messages.warning(request, f'🗑️ "{category_name}" kategoriyasi va unga tegishli {questions_count} ta savol o\'chirildi!')
        else:
            messages.success(request, f'🗑️ "{category_name}" kategoriyasi o\'chirildi!')
        return redirect('category_list')
    
    context = {'category': category}
    return render(request, 'groups/category_confirm_delete.html', context)


# ============ GURUHGA KATEGORIYA BIRIKTIRISH ============
@login_required
@user_passes_test(is_admin_user)
def group_categories_manage(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    assigned_categories = GroupCategory.objects.filter(group=group).select_related('category')
    assigned_ids = [gc.category.id for gc in assigned_categories]
    available_categories = Category.objects.exclude(id__in=assigned_ids)
    
    context = {
        'group': group,
        'assigned_categories': assigned_categories,
        'available_categories': available_categories,
    }
    return render(request, 'groups/group_categories_manage.html', context)


@login_required
@user_passes_test(is_admin_user)
def group_category_add(request, group_id):
    if request.method == 'POST':
        group = get_object_or_404(Group, id=group_id)
        category_id = request.POST.get('category_id')
        category = get_object_or_404(Category, id=category_id)
        
        if not GroupCategory.objects.filter(group=group, category=category).exists():
            GroupCategory.objects.create(group=group, category=category)
            messages.success(request, f'✅ "{category.name}" kategoriyasi qo\'shildi!')
        else:
            messages.warning(request, f'"{category.name}" allaqachon mavjud!')
    
    return redirect('group_categories_manage', group_id=group_id)


@login_required
@user_passes_test(is_admin_user)
def group_category_remove(request, group_category_id):
    group_category = get_object_or_404(GroupCategory, id=group_category_id)
    group = group_category.group
    category_name = group_category.category.name
    
    if request.method == 'POST':
        group_category.delete()
        messages.success(request, f'🗑️ "{category_name}" kategoriyasi olib tashlandi!')
    
    return redirect('group_categories_manage', group_id=group.id)


# ============ KATEGORIYA BO'YICHA SAVOLLAR ============
@login_required
@user_passes_test(is_admin_user)
def category_questions_list(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    questions = QuizQuestion.objects.filter(category=category).order_by('id')
    groups_using = Group.objects.filter(group_categories__category=category)
    
    context = {
        'category': category,
        'questions': questions,
        'total_questions': questions.count(),
        'groups_using': groups_using,
    }
    return render(request, 'groups/category_questions_list.html', context)


@login_required
@user_passes_test(is_admin_user)
def category_question_add(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        question_text = request.POST.get('question_text', '').strip()
        correct_answer = request.POST.get('correct_answer', '').strip().lower()
        
        if not question_text or not correct_answer:
            messages.error(request, 'Savol matni va to\'g\'ri javob kiritilishi shart!')
        else:
            QuizQuestion.objects.create(
                category=category,
                question_text=question_text,
                correct_answer=correct_answer
            )
            messages.success(request, f'✅ "{category.name}" kategoriyasiga yangi savol qo\'shildi!')
            return redirect('category_questions_list', category_id=category.id)
    
    context = {
        'category': category,
        'is_edit': False,
    }
    return render(request, 'groups/category_question_form.html', context)


@login_required
@user_passes_test(is_admin_user)
def category_question_edit(request, question_id):
    question = get_object_or_404(QuizQuestion, id=question_id)
    category = question.category
    
    if request.method == 'POST':
        question_text = request.POST.get('question_text', '').strip()
        correct_answer = request.POST.get('correct_answer', '').strip().lower()
        
        if not question_text or not correct_answer:
            messages.error(request, 'Savol matni va to\'g\'ri javob kiritilishi shart!')
        else:
            question.question_text = question_text
            question.correct_answer = correct_answer
            question.save()
            messages.success(request, '✅ Savol tahrirlandi!')
            return redirect('category_questions_list', category_id=category.id)
    
    context = {
        'question': question,
        'category': category,
        'is_edit': True,
    }
    return render(request, 'groups/category_question_form.html', context)


@login_required
@user_passes_test(is_admin_user)
def category_question_delete(request, question_id):
    question = get_object_or_404(QuizQuestion, id=question_id)
    category = question.category
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, f'🗑️ Savol o\'chirildi!')
        return redirect('category_questions_list', category_id=category.id)
    
    context = {
        'question': question,
        'category': category,
    }
    return render(request, 'groups/category_question_confirm_delete.html', context)


# ============ IMTIHON BOSHQARUV ============
@login_required
def exam_control(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    exam_control, created = ExamControl.objects.get_or_create(group=group)
    students = group.students.all().select_related('user')
    config, _ = GroupExamConfig.objects.get_or_create(group=group)
    
    group_categories = GroupCategory.objects.filter(group=group).values_list('category_id', flat=True)
    questions_count = QuizQuestion.objects.filter(category_id__in=group_categories).count()
    
    context = {
        'group': group,
        'exam_control': exam_control,
        'students': students,
        'questions_count': questions_count,
        'config': config,
    }
    return render(request, 'groups/exam_control.html', context)


# ============ QONUN VA QOIDALAR ============
@login_required
@user_passes_test(is_admin_user)
def rules_edit(request):
    rules, created = Rules.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        video_url = request.POST.get('video_url', '')
        rules.video_url = video_url
        
        if request.FILES.get('video_file'):
            rules.video_file = request.FILES['video_file']
        
        if request.FILES.get('image1'):
            rules.image1 = request.FILES['image1']
        rules.image1_title = request.POST.get('image1_title', 'Imtihon tartibi')
        rules.image1_description = request.POST.get('image1_description', '')
        
        if request.FILES.get('image2'):
            rules.image2 = request.FILES['image2']
        rules.image2_title = request.POST.get('image2_title', 'Baholash mezonlari')
        rules.image2_description = request.POST.get('image2_description', '')
        
        rules.rules_text = request.POST.get('rules_text', '')
        rules.save()
        messages.success(request, 'Qonun va qoidalar saqlandi!')
        return redirect('rules_edit')
    
    context = {
        'rules': rules,
    }
    return render(request, 'groups/rules_edit.html', context)


# ============ API FUNKSIYALARI ============
@login_required
@user_passes_test(is_superuser)
def admin_detail_api(request, admin_id):
    try:
        admin = User.objects.get(id=admin_id)
        data = {
            'success': True,
            'admin': {
                'id': admin.id,
                'first_name': admin.first_name,
                'last_name': admin.last_name,
                'username': admin.username,
                'email': admin.email,
                'is_superuser': admin.is_superuser,
            }
        }
        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Admin topilmadi!'})


@login_required
@user_passes_test(is_superuser)
def admin_update(request):
    if request.method == 'POST':
        admin_id = request.POST.get('admin_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        is_superuser_val = request.POST.get('is_superuser') == 'on'
        
        try:
            admin = User.objects.get(id=admin_id)
            
            if admin.id == request.user.id and not is_superuser_val:
                return JsonResponse({'success': False, 'message': 'O\'zingizni superuserlikdan chiqara olmaysiz!'})
            
            admin.first_name = first_name
            admin.last_name = last_name
            admin.username = username
            admin.email = email
            
            if password and len(password) >= 4:
                admin.password = make_password(password)
            
            if request.user.is_superuser:
                admin.is_superuser = is_superuser_val
                admin.is_staff = True
            
            admin.save()
            
            return JsonResponse({'success': True, 'message': 'Admin ma\'lumotlari yangilandi!'})
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Admin topilmadi!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Xato so\'rov!'})