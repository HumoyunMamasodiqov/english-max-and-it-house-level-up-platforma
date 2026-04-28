from django.db import models
from django.contrib.auth.models import User


class Group(models.Model):
    """Guruh modeli"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Guruh nomi")
    teacher = models.CharField(max_length=200, verbose_name="O'qituvchi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yaratilgan")
    
    class Meta:
        verbose_name = "Guruh"
        verbose_name_plural = "Guruhlar"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class Student(models.Model):
    """Talaba modeli"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name="Guruh")
    
    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"
    
    def __str__(self):
        return self.user.get_full_name() if self.user.get_full_name() else self.user.username
    
    @property
    def full_name(self):
        return self.user.get_full_name() if self.user.get_full_name() else self.user.username


class Category(models.Model):
    """Kategoriya (Fan/Bo'lim)"""
    name = models.CharField(max_length=100, unique=True, verbose_name="Kategoriya nomi")
    description = models.TextField(blank=True, null=True, verbose_name="Tavsif")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class GroupCategory(models.Model):
    """Guruhga biriktirilgan kategoriyalar"""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_categories')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='group_categories')
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Guruh kategoriyasi"
        verbose_name_plural = "Guruh kategoriyalari"
        unique_together = ['group', 'category']
    
    def __str__(self):
        return f"{self.group.name} - {self.category.name}"


class QuizQuestion(models.Model):
    """Test savollari"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='quiz_questions', verbose_name="Kategoriya")
    question_text = models.TextField(verbose_name="Savol matni")
    correct_answer = models.CharField(max_length=255, verbose_name="To'g'ri javob")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"
        ordering = ['category__name', 'id']
    
    def __str__(self):
        return f"[{self.category.name}] {self.question_text[:50]}..."


class QuizSession(models.Model):
    """Quiz sessiyasi"""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='quiz_sessions')
    is_active = models.BooleanField(default=False, verbose_name="Faol")
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_quizzes')
    
    class Meta:
        verbose_name = "Quiz sessiyasi"
        verbose_name_plural = "Quiz sessiyalari"
    
    def __str__(self):
        return f"{self.group.name} - {'Faol' if self.is_active else 'Tugagan'}"


class QuizResult(models.Model):
    """Quiz natijalari - har bir urinish uchun alohida yozuv"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='quiz_results')
    quiz_session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name='results')
    score = models.IntegerField(default=0, verbose_name="Ball")
    total_questions = models.IntegerField(default=0, verbose_name="Jami savollar")
    answers = models.JSONField(default=dict, verbose_name="Javoblar")
    submitted_at = models.DateTimeField(auto_now_add=True)
    attempt_number = models.IntegerField(default=1, verbose_name="Urinish raqami")
    
    class Meta:
        verbose_name = "Quiz natijasi"
        verbose_name_plural = "Quiz natijalari"
        ordering = ['-submitted_at']
        # unique_together ni olib tashladik - talaba bir necha marta topshirishi mumkin
    
    def __str__(self):
        return f"{self.student.full_name} - {self.score}/{self.total_questions} (#{self.attempt_number})"
    
    @property
    def percentage(self):
        if self.total_questions > 0:
            return round((self.score / self.total_questions) * 100, 1)
        return 0


class GroupExamConfig(models.Model):
    """Guruh imtihon sozlamalari"""
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='exam_config')
    questions_per_student = models.IntegerField(default=5, verbose_name="Har bir talabaga savollar soni")
    random_order = models.BooleanField(default=True, verbose_name="Random tartib")
    show_correct_answer = models.BooleanField(default=False, verbose_name="To'g'ri javobni ko'rsatish")
    time_limit = models.IntegerField(default=0, verbose_name="Vaqt limiti (daqiqa)")
    max_attempts = models.IntegerField(default=1, verbose_name="Maksimal urinishlar")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Imtihon sozlamasi"
        verbose_name_plural = "Imtihon sozlamalari"
    
    def __str__(self):
        return f"{self.group.name}: {self.questions_per_student} savol/talaba"


class UserExamAttempt(models.Model):
    """Foydalanuvchi imtihon urinishi"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_attempts')
    exam_session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name='attempts')
    selected_questions = models.JSONField(default=list, verbose_name="Tanlangan savollar")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    attempt_number = models.IntegerField(default=1, verbose_name="Urinish raqami")
    
    class Meta:
        verbose_name = "Imtihon urinishi"
        verbose_name_plural = "Imtihon urinishlari"
        ordering = ['-started_at']
    
    def __str__(self):
        status = "Tugallangan" if self.is_completed else "Jarayonda"
        return f"{self.student.full_name} - {self.exam_session.group.name} (#{self.attempt_number}) - {status}"


class ExamControl(models.Model):
    """Imtihon boshqaruvi"""
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='exam_control')
    is_active = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Imtihon boshqaruvi"
        verbose_name_plural = "Imtihon boshqaruvlari"
    
    def __str__(self):
        return f"{self.group.name} - {'Faol' if self.is_active else 'Faol emas'}"


class ExamSession(models.Model):
    """Eski imtihon sessiyasi - backward compatibility uchun"""
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='exam_sessions')
    is_active = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_exams')
    
    class Meta:
        verbose_name = "Imtihon sessiyasi"
        verbose_name_plural = "Imtihon sessiyalari"
    
    def __str__(self):
        return f"{self.group.name} - {'Faol' if self.is_active else 'Tugagan'}"


class ExamResult(models.Model):
    """Eski imtihon natijasi - backward compatibility uchun"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_results')
    exam_session = models.ForeignKey(ExamSession, on_delete=models.CASCADE, related_name='results')
    score = models.IntegerField(default=0)
    answers = models.JSONField(default=dict)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Imtihon natijasi"
        verbose_name_plural = "Imtihon natijalari"


class AdminPassword(models.Model):
    """Admin paroli"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_password')
    plain_password = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Admin paroli"
        verbose_name_plural = "Admin parollari"
    
    def __str__(self):
        return f"{self.user.username} - Parol"


class Rules(models.Model):
    """Qonun va qoidalar"""
    video_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="Video URL")
    video_file = models.FileField(upload_to='rules_videos/', blank=True, null=True, verbose_name="Video fayl")
    image1 = models.ImageField(upload_to='rules_images/', blank=True, null=True, verbose_name="Rasm 1")
    image1_title = models.CharField(max_length=200, blank=True, default="Imtihon tartibi", verbose_name="Rasm 1 sarlavhasi")
    image1_description = models.TextField(blank=True, default="Imtihon vaqtida nimalarga e'tibor berish kerak", verbose_name="Rasm 1 tavsifi")
    image2 = models.ImageField(upload_to='rules_images/', blank=True, null=True, verbose_name="Rasm 2")
    image2_title = models.CharField(max_length=200, blank=True, default="Baholash mezonlari", verbose_name="Rasm 2 sarlavhasi")
    image2_description = models.TextField(blank=True, default="Qanday qilib yuqori ball olish mumkin", verbose_name="Rasm 2 tavsifi")
    rules_text = models.TextField(default="""1. Telefon va qurilmalardan foydalanish QAT'IY MAN ETILADI
2. Belgilangan vaqtda topshirish shart
3. Ko'chirish qat'iyan man etiladi
4. Texnik muammoda o'qituvchiga murojaat qiling
5. Natijalar tekshiruvdan keyin e'lon qilinadi""", verbose_name="Qoidalar matni")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Qonun va qoidalar"
        verbose_name_plural = "Qonun va qoidalar"
    
    def __str__(self):
        return "Qonun va qoidalar"