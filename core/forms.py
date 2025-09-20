from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from .models import User, Student, Company, Job, Application,StudentResume,TaskUpdate, StudentDoc

# ----------------- LOGIN -----------------
class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")


# ----------------- STUDENT REGISTER -----------------
class StudentRegisterForm(forms.ModelForm):
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    dateOfBirth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = Student
        fields = [
            "fullName", "telephone", "major", "university", "dateOfBirth",
            "yearOfStudy", "studentId", "nationalId"
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists. Please use a different one.")
        return email

    def clean(self):
        cleaned = super().clean()
        pwd1 = cleaned.get("password1")
        pwd2 = cleaned.get("password2")
        if pwd1 and pwd2 and pwd1 != pwd2:
            self.add_error("password2", "Passwords do not match")
        return cleaned

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["profilePicture"]


class StudentProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['profilePicture', 'studentId', 'nationalId']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make fields not required if you want to allow partial updates
        self.fields['profilePicture'].required = False
        self.fields['studentId'].required = False
        self.fields['nationalId'].required = False

UserModel = get_user_model()

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = UserModel
        fields = ["email"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"})
        }

class StudentUpdateForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "fullName", "telephone", "university", "dateOfBirth",
            "major", "yearOfStudy", "comments", "profilePicture", "studentId", "nationalId"
        ]
        widgets = {
            "fullName": forms.TextInput(attrs={"class": "form-control"}),
            "telephone": forms.TextInput(attrs={"class": "form-control"}),
            "university": forms.TextInput(attrs={"class": "form-control"}),
            "dateOfBirth": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "major": forms.Select(attrs={"class": "form-select"}),
            "yearOfStudy": forms.NumberInput(attrs={"class": "form-control"}),
            "comments": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # make file fields optional when editing
        for f in ("profilePicture", "studentId", "nationalId"):
            if f in self.fields:
                self.fields[f].required = False

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            "companyLogo",       
            "companyName",
            "contactPerson",
            "contactNumber",
            "companyEmail",
            "website",
            "industry",
            "location",
            "description",
        ]
        widgets = {
            "companyName": forms.TextInput(attrs={"class": "form-control"}),
            "contactPerson": forms.TextInput(attrs={"class": "form-control"}),
            "contactNumber": forms.TextInput(attrs={"class": "form-control"}),
            "companyEmail": forms.EmailInput(attrs={"class": "form-control"}),
            "website": forms.URLInput(attrs={"class": "form-control"}),
            "industry": forms.TextInput(attrs={"class": "form-control"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class AdminForm(forms.ModelForm):
    class Meta:
        fields = [
            "email",
            "fullName",
        
            
        ]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "fullName": forms.URLInput(attrs={"class": "form-control"}),
        }


# ----------------- COMPANY REGISTER -----------------
User = get_user_model()

class CompanyRegisterForm(forms.ModelForm):
    email = forms.EmailField(label="User Email")
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = Company
        fields = [
            "companyName", "contactPerson", "contactNumber",
            "companyEmail", "website", "industry", "location", "description"
        ]

    def clean(self):
        cleaned = super().clean()
        pwd1 = cleaned.get("password1")
        pwd2 = cleaned.get("password2")

        if pwd1 != pwd2:
            raise forms.ValidationError("Passwords do not match")

        email = cleaned.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists. Please use a different one.")

        return cleaned

    def save(self, commit=True):
        # Create the User first
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password1"]
        user = User.objects.create_user(email=email, password=password, role="company")

        # Create and link the Company
        company = super().save(commit=False)
        company.user = user
        if commit:
            company.save()

        return company


# ----------------- JOB FORM  (for the company to post)-----------------
class JobForm(forms.ModelForm):
 
    class Meta:
        model = Job
        fields = ["title", "description", "major", "location", "deadline",
                  "status", "openingsAvailable", "type", "duration"]
        widgets = {
            "deadline": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 5, "class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "type": forms.Select(attrs={"class": "form-select"}),
            "duration": forms.Select(attrs={"class": "form-select"}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ["status", "type", "duration"]:
                self.fields[field].widget.attrs.update({"class": "form-control"})



# ----------------- APPLICATION FORM -(for the student to apply)----------------
class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = []
    


class StudentResumeForm(forms.ModelForm):
    class Meta:
        model = StudentResume
        fields = ["fullName", "email", "phone", "location", "summary", "education", "experience", "skills", "hobbies"]
        widgets = {
            "fullName": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full Name"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone"}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "Location"}),
            "summary": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Short summary"}),
            "education": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "experience": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "skills": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "hobbies": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class TaskUpdateForm(forms.ModelForm):
    class Meta:
        model = TaskUpdate
        fields = ["progressPercent", "comments", "proof"]
        widgets = {
            "comments": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "progressPercent": forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 100}),
            "proof_file": forms.ClearableFileInput(attrs={"class": "form-control"}),  

        }

class TaskReviewForm(forms.ModelForm):
    feedback = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Add feedback (optional)"})
    )

    class Meta:
        model = TaskUpdate
        fields = ["status", "progressPercent","comments"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "comments": forms.Select(attrs={"class": "form-select"}),
            'progressPercent': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),

        }