from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import MinValueValidator


# ----------------- USER (login table) -----------------

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, role="student", **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("student", "Student"),
        ("company", "Company"),
        ("admin", "Admin"),
    ]
    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    email = models.EmailField(unique=True, db_column="email")
    role = models.CharField(max_length=20, null=True, blank=True, choices=ROLE_CHOICES, db_column="role")
    status = models.CharField(max_length=20, null=True, blank=True, choices=STATUS_CHOICES, default="active", db_column="status")

    createdAt = models.DateTimeField(auto_now_add=True, null=True, blank=True, db_column="createdAt")
    updatedAt = models.DateTimeField(auto_now=True, null=True, db_column="updatedAt")
    deletedAt = models.DateTimeField(null=True, blank=True, db_column="deletedAt")

    lastLogin = models.DateTimeField(null=True, blank=True, db_column="lastLogin")
    resetToken = models.CharField(max_length=255, null=True, blank=True, db_column="resetToken")
    tokenExpiry = models.DateTimeField(null=True, blank=True, db_column="tokenExpiry")
    failedAttempts = models.PositiveSmallIntegerField(default=0, db_column="failedAttempts")

    is_active = models.BooleanField(default=True, db_column="is_active")
    is_staff = models.BooleanField(default=False, db_column="is_staff")
    is_superuser = models.BooleanField(default=False, db_column="is_superuser")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "login"

    def __str__(self):
        return f"{self.email} ({self.role})"


# ----------------- STUDENT -----------------
class Student(models.Model):
    MAJOR_CHOICES = [
        ("cs", "Computer Science"),
        ("it", "Information Technology"),
        ("eng", "Engineering"), 
        ("bus", "Business"),
        ("edu",  "Education"),
    ]
    user = models.OneToOneField(User, on_delete=models.RESTRICT, db_column="loginId")
    fullName = models.CharField(max_length=100, null=True, blank=True, db_column="fullName")
    telephone = models.CharField(max_length=20, null=True, blank=True, db_column="telephone")
    university = models.CharField(max_length=100, db_column="university")
    dateOfBirth = models.DateField(null=True, blank=True, db_column="dateOfBirth")
    major = models.CharField(max_length=50, blank=True, null=True, choices=MAJOR_CHOICES, db_column="major")  
    yearOfStudy = models.PositiveSmallIntegerField( null=True, blank=True,db_column="yearOfStudy")
    studentId = models.ImageField(upload_to="studentIds/", null=True, blank=True, db_column="studentId")
    location = models.CharField(max_length=150, null=True, blank=True, db_column="location")  # 👈 Add this
    nationalId = models.ImageField(upload_to="nationalIds/", null=True, blank=True, db_column="nationalId")
    profilePicture = models.ImageField(upload_to="profiles/", null=True, blank=True, db_column="profilePicture")
    comments = models.TextField(null=True, blank=True, db_column="comments")
    isAccepted = models.BooleanField(default=False)


    class Meta:
        db_table = "student"

    def __str__(self):
        return f"{self.user.email} - {self.get_major_display()}"


# ----------------- COMPANY -----------------
class Company(models.Model):
    user = models.OneToOneField(User, on_delete=models.RESTRICT, db_column="loginId")
    companyName = models.CharField(max_length=150, null=True, blank=True,db_column="companyName")
    contactPerson = models.CharField(max_length=150, null=True, blank=True, db_column="contactPerson")
    contactNumber = models.CharField(max_length=20, null=True, blank=True, db_column="contactNumber")
    companyEmail = models.EmailField(null=True, blank=True, db_column="companyEmail")
    website = models.URLField(null=True, blank=True, db_column="website")
    industry = models.CharField(max_length=150, null=True, blank=True, db_column="industry")
    location = models.CharField(max_length=150, null=True, blank=True,  db_column="location")
    description = models.TextField(null=True, blank=True, db_column="description")
    companyLogo = models.ImageField(
        upload_to='company_logos/', blank=True, null=True
    )


    class Meta:
        db_table = "company"

    def __str__(self):
        return self.companyName


# ----------------- COMPANY DOCS -----------------
class CompanyDoc(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, db_column="companyId")
    documentType = models.CharField(max_length=50, null=True, blank=True, db_column="documentType")
    fileUrl = models.CharField(max_length=255,  null=True, blank= True, db_column="fileUrl")
    verificationStatus = models.CharField(max_length=20, null=True, blank=True, default="pending", db_column="verificationStatus")
    rejectionReason = models.TextField(null=True, blank=True, db_column="rejectionReason")

    class Meta:
        db_table = "companyDocs"
    
    def __str__(self):
        return self.company


# ----------------- JOB (attachment table) -----------------
class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ('fullTime', 'Full Time'),
        ('partTime', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('draft', 'Draft'),
    ]

    DURATION_CHOICES = [
        ('1-month', '1 Month'),
        ('3-months', '3 Months'),
        ('6-months', '6 Months'),
        ('1-year', '1 Year'),
        ('permanent', 'Permanent'),
    ]
    MAJOR_CHOICES = [
        ("cs", "Computer Science"),
        ("it", "Information Tecnology"),
        ("eng", "Engineering"), 
        ("bus", "Business"),
        ("edu",  "Education"),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, db_column="companyId")
    title = models.CharField(max_length=150,null=True, blank=True, db_column="title")
    description = models.TextField(max_length=800, blank=True, null=True, db_column="description")
    major = models.CharField(max_length=100, null=True, blank=True, choices=MAJOR_CHOICES, db_column="major")
    location = models.CharField(max_length=150, null=True, blank=True, db_column="location")
    deadline = models.DateField(blank=True, null=True, db_column="deadline")
    status = models.CharField(max_length=20, null=True, blank=True, choices=STATUS_CHOICES, default="open", db_column="status")
    openingsAvailable = models.PositiveSmallIntegerField(blank=True, null=True, validators=[MinValueValidator(1)], db_column="openingsAvailable")
    type = models.CharField(max_length=50, null=True, blank=True, choices=JOB_TYPE_CHOICES, db_column="type")
    duration = models.CharField(max_length=50, blank=True, null=True, choices=DURATION_CHOICES, db_column="duration")

    class Meta:
        db_table = "job"

    def __str__(self):
        return self.title


# ----------------- APPLICATION -----------------
class Application(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, db_column="studentId")
    job = models.ForeignKey(Job, on_delete=models.RESTRICT, db_column="attachmentId")
    fullName = models.CharField(max_length=150, null=True, blank=True, db_column="fullName")
    email = models.EmailField(null=True, blank=True, db_column="email")
    telephone = models.CharField(max_length=20, blank=True, null=True, db_column="telephone")
    resume = models.ForeignKey("StudentResume", on_delete=models.SET_NULL, null=True, blank=True)

    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ], default="pending", db_column="status")
    appliedAt = models.DateTimeField(auto_now_add=True, null=True, blank=True, db_column="appliedAt")
    reviewedAt = models.DateTimeField(null=True, blank=True, db_column="reviewedAt")
    reviewedBy = models.CharField(max_length=150, null=True, blank=True, db_column="reviewedBy")
    applicationStage = models.CharField(max_length=50, null=True, blank=True, db_column="applicationStage")
    comments = models.TextField(null=True, blank=True, db_column="comments")

    class Meta:
        db_table = "application"

    def __str__(self):
        return f"{self.fullName} -> {self.job.title}"


# ----------------- STUDENT DOCS -----------------
class StudentDoc(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, db_column="studentId")
    application = models.ForeignKey(Application, on_delete=models.CASCADE, db_column="applicationId")
    documentType = models.CharField(max_length=20, null=True, blank=True, db_column="documentType")
    fileName = models.CharField(max_length=255, null=True, blank=True, db_column="fileName")
    fileUrl = models.CharField(max_length=255, null=True, blank=True, db_column="fileUrl")

    class Meta:
        db_table = "studentDocs"
    
    def __str__(self):
        return self.student
        


# ----------------- PROJECTS -----------------
class Project(models.Model):
    application = models.ForeignKey(Application, on_delete=models.RESTRICT, db_column="applicationId")
    title = models.CharField(max_length=150, blank=True, null=True, db_column="title")
    description = models.TextField(max_length=200, null=True, blank=True, db_column="description")
    plannedStartDate = models.DateField(null=True, blank=True, db_column="plannedStartDate")
    plannedEndDate = models.DateField(null=True, blank=True, db_column="plannedEndDate")
    actualStartDate = models.DateField(null=True, blank=True, db_column="actualStartDate")
    actualEndDate = models.DateField(null=True, blank=True, db_column="actualEndDate")
    status = models.CharField(max_length=20, default="active", db_column="status")
    comments = models.TextField(null=True, blank=True, db_column="comments")

    class Meta:
        db_table = "projects"
    
    def __str__(self):
        return self.title


# ----------------- TASKS -----------------
class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in-progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('completed', 'Completed'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, db_column="projectId")
    title = models.CharField(max_length=150, null=True, blank=True, db_column="title")
    description = models.TextField(max_length=200, null=True, blank=True, db_column="description")
    assignedBy = models.CharField(max_length=150, null=True, blank=True, db_column="assignedBy")
    status = models.CharField(max_length=20, default="pending", db_column="status")
    dueDate = models.DateField(null=True, blank=True, db_column="dueDate")
    

    class Meta:
        db_table = "task"
    
    def __str__(self):
        return self.title


# ----------------- TASK UPDATES -----------------
class TaskUpdate(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("submitted", "Submitted"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, db_column="taskId", related_name="updates")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, db_column="studentId")
    progressPercent = models.PositiveSmallIntegerField( null=True,blank=True, db_column="progressPercent")
    proof = models.FileField(upload_to="task_proofs/", null=True, blank=True, db_column="proof")  
    comments = models.TextField(null=True, blank=True, db_column="comments")

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        db_column="status"
    )
    description = models.TextField(null=True, blank=True)

    submittedAt = models.DateTimeField(auto_now_add=True, null=True, blank=True, db_column="submittedAt")
    reviewedAt = models.DateTimeField(null=True, blank=True, db_column="reviewedAt")
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)


    class Meta:
        db_table = "taskUpdate"

    def __str__(self):
        return f"{self.student.fullName} - {self.task.title} ({self.status})"


class StudentResume(models.Model):
    student = models.OneToOneField("Student", on_delete=models.CASCADE)
    fullName = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    location = models.CharField(max_length=150, blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    education = models.TextField(blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    hobbies = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_complete(self):
        return all([
            self.fullName,
            self.education,
            self.hobbies,
            self.location,
            self.phone,
            self.email,
            self.experience,
            self.skills,
            self.summary,
        ])
    
    class Meta:
      db_table = "studentResume"


    def __str__(self):
        return f"{self.student.fullName}"
    
    
    

