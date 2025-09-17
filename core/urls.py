from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [

    # Auth
    path("login/", views.loginView, name="login"),
    path("logout/", views.logoutView, name="logout"),

    path("register/student/", views.registerStudent, name="registerStudent"),
    path("register/company/", views.registerCompany, name="registerCompany"),
    path('activate/<int:uid>/<str:token>/', views.activateStudent, name='activate_student'),
    path('activate-company/<uid>/<token>/',views.activateCompany,name='activate_company'),
    path("student/profile/upload/", views.studentProfileUpload, name="studentProfileUpload"),
    path("student/settings/", views.student_settings, name="studentSettings"),
    path("company/settings/", views.companySettings, name="companySettings"),
    path("profile/upload/", views.profileUpload, name="profileUpload"),


    # Password change while logged in
    path("password/change/",
         auth_views.PasswordChangeView.as_view(
             template_name="student/change_password.html",
             success_url="/student/settings/"
         ),
         name="password_change"),
    
    # Password reset (forgot password) 
    path("password/reset/",
         auth_views.PasswordResetView.as_view(
             template_name="auth/password_reset.html",
             email_template_name="auth/password_reset_email.txt",
             html_email_template_name="auth/password_reset_email.html",    
             subject_template_name="auth/password_reset_subject.txt",
             success_url="/password/reset/done/"
         ),
         name="password_reset"),
    path("password/reset/done/",
         auth_views.PasswordResetDoneView.as_view(template_name="auth/password_reset_done.html"),
         name="password_reset_done"),
    path("password/reset/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(
             template_name="auth/password_reset_confirm.html",
         ), name="password_reset_confirm"),
    path("password/reset/complete/",
         auth_views.PasswordResetCompleteView.as_view(template_name="auth/password_reset_complete.html"),
         name="password_reset_complete"),


    # Dashboards
    path("", views.dashboardRedirect, name="dashboardRedirect"),
    path("dashboard/student/", views.studentDashboard, name="studentDashboard"),
    path("dashboard/company/", views.companyDashboard, name="companyDashboard"),
    path("dashboard/admin/", views.adminDashboard, name="adminDashboard"),
    path("dashboard/profile/", views.studentProfile, name="studentProfile"),

    # Jobs
    path("jobs/", views.jobList, name="jobsList"),  
    path("jobs/create/", views.jobCreate, name="jobCreate"),
    path("jobs/<int:jobId>/", views.jobDetail, name="jobDetail"),
    path("dashboard/job/", views.jobList, name="jobList"), 
    path("student/apply/<int:jobId>/", views.applyToJob, name="applyToJob"),
 

    # Company applications
    path("company/applications/", views.companyApplications, name="companyApplications"),    
    path("company/applications/<int:application_id>/", views.applicationDetail, name="applicationDetail"),
    path('company/application/update/<int:application_id>/', views.updateApplicationStatus, name='updateApplicationStatus'),


    # Resume
    path("resume/", views.resumeForm, name="resumeForm"),
    path("resume/<int:student_id>/download/", views.downloadResume, name="downloadResume"),


    # Company projects & tasks
    path("company/projects/", views.companyProjects, name="companyProjects"),
    path("company/projects/create/<int:application_id>/", views.createProject, name="createProject"),
    path("company/projects/<int:project_id>/", views.projectDetail, name="projectDetail"),
    path("company/projects/<int:project_id>/tasks/create/", views.createTask, name="createTask"),
    path("company/projects/<int:project_id>/submissions/", views.taskSubmissions, name="taskSubmissions"),



    # Student projects & tasks
    path("student/projects/", views.studentProjects, name="studentProjects"),
    path("student/task/<int:task_id>/submit/", views.submitTaskUpdate, name="submitTaskUpdate"),
    path("student/tasks/<int:task_id>/update/", views.submitTaskUpdate, name="submitTaskUpdate"),
    path('task/update/<int:update_id>/', views.reviewTaskUpdate, name='reviewTaskUpdate'),



] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
