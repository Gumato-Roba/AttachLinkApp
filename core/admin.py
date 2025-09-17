from django.contrib import admin
from .models import *

admin.site.register(User)
admin.site.register(Student)
admin.site.register(Company)
admin.site.register(Job)
admin.site.register(Application)
admin.site.register(StudentDoc)
admin.site.register(CompanyDoc)
admin.site.register(Project)
admin.site.register(Task)
admin.site.register(TaskUpdate)
admin.site.register(StudentResume)