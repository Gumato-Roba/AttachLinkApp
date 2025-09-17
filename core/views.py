import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django.views.generic import ListView
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import HttpResponse, FileResponse
from django.db.models import Q
from reportlab.lib.pagesizes import A4
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from Attachlinkproject.settings import DEFAULT_FROM_EMAIL
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


from .forms import (
    LoginForm, StudentRegisterForm, CompanyRegisterForm,
    JobForm, StudentResumeForm, TaskUpdateForm, TaskReviewForm,ProfilePictureForm,StudentProfileUpdateForm,StudentUpdateForm,UserUpdateForm,CompanyForm
)
from .models import (
    User, Student, Company, Job, Application,
    StudentResume, Project, Task, TaskUpdate
)


# ---------------- AUTH ----------------
def loginView(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"]
            )
            if user and user.is_active:
                login(request, user)
                return redirect("dashboardRedirect")
        messages.error(request, "Invalid credentials.")
    else:
        form = LoginForm(request)
    return render(request, "auth/login.html", {"form": form})


def logoutView(request):
    logout(request)
    return redirect("login")

def registerStudent(request):
    if request.method == "POST":
        form = StudentRegisterForm(request.POST, request.FILES)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password1']

            if User.objects.filter(email=email).exists():
                messages.error(request, "Email is already registered. Try logging in.")
                return redirect("register_student")
            
            user = User.objects.create_user(email=email, password=password, is_active=False)  # <-- inactive until verified

            student = form.save(commit=False)
            student.user = user
            student.save()

            # Generate token
            token = default_token_generator.make_token(user)
            path = reverse('activate_student', kwargs={'uid': user.id, 'token': token})
            activation_link = request.build_absolute_uri(path)
           
            context = {
                'student': student,
                'protocol': 'http',  # or 'https'
                'domain': 'f25da801b5d8.ngrok-free.app',  #
                'activation_link': activation_link,
            }
            html_content = render_to_string('auth/activation_email.html', context)

            email_message = EmailMultiAlternatives(
                subject="Activate Your Account",
                body="",  # plain text fallback
                from_email=DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email_message.attach_alternative(html_content, "text/html")
            email_message.send()

            # Success message and redirect
            messages.success(request, "Registration successful! Please check your email to activate your account.")
            return redirect("login")
    else:
        form = StudentRegisterForm()

    return render(request, "auth/register_student.html", {"form": form})

def activateStudent(request, uid, token):
    user = get_object_or_404(User, id=uid)
    if default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account is activated! You can now log in.")
        return redirect("login")
    else:
        messages.error(request, "Activation link is invalid or expired.")
        return redirect("registerStudent")




def registerCompany(request):
    if request.method == "POST":
        form = CompanyRegisterForm(request.POST, request.FILES)  # include files if needed
        if form.is_valid():
            email = form.cleaned_data['companyEmail']   # or 'email' depending on your form field
            password = form.cleaned_data['password1']   # if you have password fields in the form

            # Check if email already used
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email is already registered. Try logging in.")
                return redirect("register_company")

            # Create inactive user
            user = User.objects.create_user(
                email=email,
                password=password,
                is_active=False  # inactive until verified
            )

            # Link Company model to this user
            company = form.save(commit=False)
            company.user = user
            company.save()

            # Generate token + activation link
            token = default_token_generator.make_token(user)
            path = reverse('activate_company', kwargs={'uid': user.id, 'token': token})
            activation_link = request.build_absolute_uri(path)

            # Send activation email
            send_mail(
                'Activate Your Company Account',
                f'Hi {company.companyName}, click the link to activate your account:\n{activation_link}',
                DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            messages.success(
                request,
                "Company account created! Please check your email to activate your account."
            )
            return redirect("login")
    else:
        form = CompanyRegisterForm()

    return render(request, "auth/register_company.html", {"form": form})

def activateCompany(request, uid, token):
    user = get_object_or_404(User, id=uid)
    if default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your company account has been activated. You can now log in.")
        return redirect('login')
    else:
        messages.error(request, "Invalid or expired activation link.")
        return redirect('registerCompany')



@login_required
def studentProfile(request):
    return render(request, "dashboards/profile.html")


# ---------------- DASHBOARD REDIRECT ----------------
@login_required
def dashboardRedirect(request):
    if request.user.role == "student":
        return redirect("studentDashboard")
    elif request.user.role == "company":
        return redirect("companyDashboard")
    return redirect("adminDashboard")


# ---------------- DASHBOARDS ----------------
@login_required
def studentDashboard(request):
    student = get_object_or_404(Student, user=request.user)

    resume = StudentResume.objects.filter(student=student).first()
    has_complete_resume = False

    projects = Project.objects.filter(application__student=student).prefetch_related("task_set")

    student_updates = {}
    updates = TaskUpdate.objects.filter(student=student).select_related("task")
    for u in updates:
        student_updates[u.task.id] = u
    
    # Attach form to each task
    task_forms = {} 

    for project in projects:
        for task in project.task_set.all():
            existing_update = TaskUpdate.objects.filter(
                task=task, student=student
            ).first()
            task_forms[task.id] = TaskUpdateForm(instance=existing_update)
            student_updates[task.id] = existing_update  


    availableJobs = Job.objects.filter( status="open",major=student.major).order_by("-id")[:3]
    for job in availableJobs:
        job.already_applied = Application.objects.filter(
            student=student, job=job
        ).exists()

    myApps = Application.objects.filter(student=student).select_related("student", "job")
    hasAccepted = myApps.filter(status="accepted").exists()

    context = {
        "student": student,
        "availableJobs": availableJobs,
        "myApps": myApps,
        "appliedCount": myApps.count(),
        "availableCount": Job.objects.filter(status="open", major=student.major).count(),
        "projects": projects,
        "projectCount": projects.count(),
        "resume": resume,
        "has_complete_resume": has_complete_resume,
        "pendingCount": myApps.filter(status="Pending").count(),
        "hasAccepted": hasAccepted,
        "student_updates": student_updates,
        "task_forms": task_forms,
    }
    return render(request, "dashboards/student.html", context)



@login_required
def companyDashboard(request):
    company = get_object_or_404(Company, user=request.user)
    myJobs = Job.objects.filter(company=company)
    applications = Application.objects.filter(job__in=myJobs).select_related("student", "job")

    totalJobs = myJobs.count()
    totalApplications = applications.count()
    pendingApplications = applications.filter(status="pending").count()
    acceptedApplications = applications.filter(status="accepted").count()
    company_projects = Project.objects.filter(application__job__company=company)
    pending_count = Application.objects.filter(job__company=company, status="pending").count()
    recentApplications = applications.order_by("-appliedAt")[:3]

    submitted_tasks = TaskUpdate.objects.filter(
        task__project__application__job__company=company,
        status="submitted"
    ).select_related("task", "student")

    for job in myJobs:
        job.applicationsCount = Application.objects.filter(job=job).count()

    context = {
        "company": company,
        "myJobs": myJobs,
        "applications": applications,
        "recentApplications": recentApplications,
        "totalJobs": totalJobs,
        "totalApplications": totalApplications,
        "pendingApplications": pending_count,
        "acceptedApplications": acceptedApplications,
        "submitted_tasks": submitted_tasks,
        "company_projects": company_projects,
    }
    return render(request, "dashboards/company.html", context)


@login_required
def adminDashboard(request):
    students = Student.objects.all()
    companies = Company.objects.all()
    return render(request, "dashboards/admin.html", {"students": students, "companies": companies})


# ---------------- JOBS ----------------
from core.models import StudentResume


@login_required
def jobList(request):
    student = get_object_or_404(Student, user=request.user)
    today = timezone.now().date()

    # First, get the jobs
    jobs = Job.objects.filter(status="open",major=student.major,deadline__gte=today).order_by("-id")

    # Exclude jobs already applied to
    jobs = jobs.exclude(application__student=student)

    # Search filter
    q = request.GET.get("q")
    if q:
        jobs = jobs.filter(
            Q(title__icontains=q) |
            Q(company__companyName__icontains=q) |
            Q(description__icontains=q) |
            Q(location__icontains=q) |
            Q(type__icontains=q)
        )

    # Check resume existence and completeness
    resume = StudentResume.objects.filter(student=student).first()
    has_complete_resume = resume.is_complete if resume else False

    # Mark which jobs have already been applied to (optional, may not be needed after exclude)
    for job in jobs:
        job.already_applied = Application.objects.filter(student=student, job=job).exists()

    return render(
        request,
        "jobs/list.html",
        {
            "jobs": jobs,
            "resume": resume,
            "has_complete_resume": has_complete_resume,
            "now": today
        },
    )

@user_passes_test(lambda u: u.role == "company")
def jobCreate(request):
    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = Company.objects.get(user=request.user)
            job.save()
            messages.success(request, "Job posted successfully!.")
            return redirect("companyDashboard")
    else:
        form = JobForm()
    return render(request, "jobs/create.html", {"form": form, "title": "Post New Job"})


# ---------------- RESUME ----------------
@login_required
@user_passes_test(lambda u: u.role == "student")
def resumeForm(request):
    student = get_object_or_404(Student, user=request.user)
    resume, created = StudentResume.objects.get_or_create(student=student)

    if request.method == "POST":
        form = StudentResumeForm(request.POST, instance=resume)
        if form.is_valid():
            form.save()
            messages.success(request, "Your resume has been saved successfully.")
            return redirect("studentDashboard")
    else:
        form = StudentResumeForm(instance=resume)  # <--- define form for GET requests

    return render(request, "jobs/resume_form.html", {"form": form, "resume": resume})


@login_required
def downloadResume(request, student_id):
    resume = get_object_or_404(StudentResume, student__id=student_id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Use fullName from the resume model
    if resume.fullName:
        elements.append(Paragraph(f"<b>{resume.fullName}</b>", styles["Title"]))
        elements.append(Spacer(1, 12))

    if resume.email:
        elements.append(Paragraph(f"Email: {resume.email}", styles["Normal"]))
        elements.append(Spacer(1, 6))

    if resume.phone:
        elements.append(Paragraph(f"Phone: {resume.phone}", styles["Normal"]))
        elements.append(Spacer(1, 6))

    if resume.location:
        elements.append(Paragraph(f"Location: {resume.location}", styles["Normal"]))
        elements.append(Spacer(1, 12))

    if resume.summary:
        elements.append(Paragraph(f"<b>Summary</b><br/>{resume.summary}", styles["Normal"]))
        elements.append(Spacer(1, 12))

    if resume.education:
        elements.append(Paragraph(f"<b>Education</b><br/>{resume.education}", styles["Normal"]))
        elements.append(Spacer(1, 12))

    if resume.experience:
        elements.append(Paragraph(f"<b>Experience</b><br/>{resume.experience}", styles["Normal"]))
        elements.append(Spacer(1, 12))

    if resume.skills:
        elements.append(Paragraph(f"<b>Skills</b><br/>{resume.skills}", styles["Normal"]))
        elements.append(Spacer(1, 12))

    if resume.hobbies:
        elements.append(Paragraph(f"<b>Hobbies</b><br/>{resume.hobbies}", styles["Normal"]))
        elements.append(Spacer(1, 12))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type="application/pdf")
    filename = f"{resume.fullName or 'resume'}_resume.pdf"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response



# ---------------- APPLICATIONS ----------------
@login_required
@user_passes_test(lambda u: u.role == "student")
def applyToJob(request, jobId):
    job = get_object_or_404(Job, id=jobId)
    student = get_object_or_404(Student, user=request.user)

    # Check if already applied
    if Application.objects.filter(student=student, job=job).exists():
        messages.warning(request, "You have already applied for this job.")
        return redirect("studentDashboard")

    # Get resume
    resume = StudentResume.objects.filter(student=student).first()
    if not resume or not resume.is_complete:
        messages.error(request, "You must complete your resume before applying.")
        return redirect("resumeForm")

    if request.method == "POST":
        # Create the application
        Application.objects.create(student=student, job=job)
        messages.success(request, f"You successfully applied to {job.title}.")
        return redirect("studentDashboard")

    # GET request → show resume preview before applying
    return render(request, "jobs/apply.html", {
        "job": job,
        "resume": resume
    })



@login_required
def jobDetail(request, jobId):
    job = get_object_or_404(Job, id=jobId)
    already_applied = False
    if hasattr(request.user, "student"): 
     student = request.user.student
     already_applied = Application.objects.filter(student=student, job=job).exists()

    return render(request, "jobs/job_detail.html", {
        "job": job,
        "already_applied": already_applied,
    })


@login_required
@user_passes_test(lambda u: u.role == "company")
def companyApplications(request):
    company = get_object_or_404(Company, user=request.user)
    jobs = Job.objects.filter(company=company)
    applications = Application.objects.filter(job__in=jobs).select_related("student", "job")
    return render(request, "company/application.html", {"applications": applications})


@login_required
@user_passes_test(lambda u: u.role == "company")
def applicationDetail(request, application_id):
    application = get_object_or_404(
        Application,
        id=application_id,
        job__company__user=request.user
    )
    student = application.student
    resume = getattr(student, "studentresume", None)

    if request.method == "POST":
        status = request.POST.get("status")
        comments = request.POST.get("comments", "")
        if status in ["accepted", "rejected"]:
            application.status = status
            application.comments = comments
            application.save()
            messages.success(request, f"Application {status.capitalize()} successfully.")
            return redirect("applicationDetail", application_id=application.id)

    return render(request, "company/application_detail.html", {
        "application": application,
        "student": student,
        "resume": resume,
    })


# ---------------- PROJECTS & TASKS ----------------
@login_required
@user_passes_test(lambda u: u.role == "company")
def companyProjects(request):
    company = get_object_or_404(Company, user=request.user)

    # All accepted applications
    accepted_applications = Application.objects.filter(
        job__company=company, status="accepted"
    ).select_related("student", "job")

    # Projects for accepted applications
    projects = Project.objects.filter(application__in=accepted_applications).select_related(
        "application", "application__student"
    )

    # Applications that do not yet have a project
    apps_without_projects = accepted_applications.exclude(
        id__in=projects.values_list("application_id", flat=True)
    )

    return render(request, "company/projects.html", {
        "projects": projects,
        "apps_without_projects": apps_without_projects,
    })

@login_required
@user_passes_test(lambda u: u.role == "company")
def createProject(request, application_id):
    application = get_object_or_404(
        Application,
        id=application_id,
        job__company__user=request.user,
        status="accepted"
    )
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        planned_start_date = request.POST.get("plannedStartDate")
        planned_end_date = request.POST.get("plannedEndDate")

        if title and description:
            Project.objects.create(
                application=application,
                title=title,
                description=description,
                plannedStartDate=planned_start_date,
                plannedEndDate=planned_end_date,
                actualStartDate=timezone.now().date(),
                status="active"
            )
            messages.success(request, "Project created successfully!")
            return redirect("companyProjects")
    return render(request, "company/create_project.html", {"application": application})


@login_required
@user_passes_test(lambda u: u.role == "company")
def projectDetail(request, project_id):
    project = get_object_or_404(
        Project,
        id=project_id,
        application__job__company__user=request.user
    )
    tasks = Task.objects.filter(project=project).prefetch_related("updates") 
    return render(request, "company/project_detail.html", {
        "project": project,
        "tasks": tasks,
        "student": project.application.student,
        "application": project.application,
    })


@login_required
@user_passes_test(lambda u: u.role == "company")
def createTask(request, project_id):
    project = get_object_or_404(
        Project,
        id=project_id,
        application__job__company__user=request.user
    )
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        due_date = request.POST.get("dueDate")

        if title:
            Task.objects.create(
                project=project,
                title=title,
                description=description,
                dueDate=due_date,
                assignedBy=request.user.email,
                status="pending"
            )
            messages.success(request, "Task created successfully!")
            return redirect("projectDetail", project_id=project.id)
    return render(request, "company/create_task.html", {"project": project})


@login_required
def studentProjects(request):
    student = get_object_or_404(Student, user=request.user)
    projects = Project.objects.filter(application__student=student).prefetch_related("task_set")
    updates = TaskUpdate.objects.filter(student=student)  
    student_updates = {update.task_id: update for update in updates}

    task_forms = {}
    for project in projects:
        for task in project.task_set.all():
            existing_update = TaskUpdate.objects.filter(task=task, student=student).first()
            task_forms[task.id] = TaskUpdateForm(instance=existing_update)
    return render(request, "student/projects.html", {
        "student": student,
        "projects": projects,
        "task_forms": task_forms,
        "student_updates": student_updates

    })


@login_required
def submitTaskUpdate(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    student = get_object_or_404(Student, user=request.user)

    if task.project.application.student != student:
        messages.error(request, "You cannot submit this task.")
        return redirect("studentDashboard")

    existing_update = TaskUpdate.objects.filter(task=task, student=student).first()

    if request.method == "POST":
        form = TaskUpdateForm(request.POST, request.FILES, instance=existing_update)
        if form.is_valid():
            update = form.save(commit=False)
            update.task = task
            update.student = student
            update.status = "submitted"
            update.save()
            messages.success(request, "Task submitted successfully.")
            return redirect("studentProjects")
    else:
        form = TaskUpdateForm(instance=existing_update)

    return render(request, "student/task_update.html", {"form": form, "task": task})


@login_required
@user_passes_test(lambda u: u.role == "company")
def reviewTaskUpdate(request, update_id):
    update = get_object_or_404(
        TaskUpdate,
        id=update_id,
        task__project__application__job__company__user=request.user
    )

    if request.method == "POST":
        form = TaskReviewForm(request.POST, instance=update)
        if form.is_valid():
            update = form.save(commit=False)
            update.reviewedAt = timezone.now()
            update.save()
            messages.success(request, "Task reviewed successfully.")
        else:
            messages.error(request, "There was an error submitting the review.")
        return redirect("projectDetail", project_id=update.task.project.id)

    return redirect("projectDetail", project_id=update.task.project.id)



@login_required
@user_passes_test(lambda u: u.role == "company")
def taskSubmissions(request, project_id):
    project = get_object_or_404(
        Project,
        id=project_id,
        application__job__company__user=request.user
    )

    # Get all submissions for tasks in this project
    submitted_tasks = TaskUpdate.objects.filter(
        task__project=project,
        status__in=["submitted", "approved", "rejected"]  # ignore pending
    ).select_related("task", "student").order_by("-created_at")

    return render(request, "company/task_submissions.html", {
        "project": project,
        "submitted_tasks": submitted_tasks,
    })

@login_required
def studentProfileUpload(request):
    student = get_object_or_404(Student, user=request.user)

    if request.method == "POST":
        form = ProfilePictureForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            return redirect("studentSettings")
    else:
        form = ProfilePictureForm(instance=student)

    return render(request, "student/profile_upload.html", {"form": form})

@login_required
def student_settings(request):
    user = request.user
    student = get_object_or_404(Student, user=user)

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=user)
        student_form = StudentUpdateForm(request.POST, request.FILES, instance=student)

        if user_form.is_valid() and student_form.is_valid():
            user_form.save()
            student_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("studentSettings")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        user_form = UserUpdateForm(instance=user)
        student_form = StudentUpdateForm(instance=student)

    return render(request, "student/settings.html", {
        "user_form": user_form,
        "student_form": student_form,
    })


@login_required
def profileUpload(request):
    if request.method == "POST" and request.FILES.get("profilePicture"):
        profile_picture = request.FILES["profilePicture"]

        # Check if user is a student
        if hasattr(request.user, "student"):
            request.user.student.profilePicture = profile_picture
            request.user.student.save()

        # Check if user is a company
        elif hasattr(request.user, "company"):
            request.user.company.companyLogo = profile_picture
            request.user.company.save()

        messages.success(request, "Profile picture updated successfully!")
        return redirect(request.META.get("HTTP_REFERER", "login"))  # stay on same page

    messages.error(request, "No file selected.")
    return redirect(request.META.get("HTTP_REFERER", "login"))

@login_required
def companySettings(request):
    company = request.user.company
    if request.method == "POST":
        form = CompanyForm(request.POST, request.FILES, instance=request.user.company)
        if form.is_valid():
            form.save()
            messages.success(request, "Company Profile updated successfully.")
            return redirect("companySettings")
    else:
        form = CompanyForm(instance=company)

    return render(request, "company/settings.html", {"form": form})


@login_required
@user_passes_test(lambda u: u.role == "company")
def updateApplicationStatus(request, application_id):
    application = get_object_or_404(Application, id=application_id)

    if request.method == "POST":
        status = request.POST.get("status")
        if status in ["accepted", "rejected", "reviewed"]:
            application.status = status
            application.save()
    return redirect("companyApplications") 