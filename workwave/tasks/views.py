#tasks/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import HttpResponseForbidden
from .models import Profile
from .forms import ProfileForm
from django.shortcuts import render, get_object_or_404, redirect
from .models import Task
from .forms import TaskCommentForm
from .forms import TaskAttachmentForm
from .models import TaskAttachment
from django.db.models import Count
from django.db.models import Q
from django.utils import timezone
from .models import Project, Task, TaskCategory
from .forms import ProjectForm, TaskForm, ProfileForm, TaskCommentForm, TaskAttachmentForm
from django.template import engines
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth import login


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'tasks/home.html'

    def get(self, request, *args, **kwargs):
        if not hasattr(self, 'template_engine'):
            try:
                self.template_engine = engines['django'].engine
                print(self.template_engine.loaders[0].get_dirs())
            except AttributeError:
                pass

        return super().get(request, *args, **kwargs)


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

from django.shortcuts import redirect
from django.contrib.auth import logout

def custom_logout(request):
    logout(request)
    return redirect('login')

@login_required
def project_list(request):
    projects = Project.objects.filter(owner=request.user)
    return render(request, 'tasks/project_list.html', {'projects': projects})

def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    tasks = Task.objects.filter(project=project)

    # Task Due Notifications
    due_tasks = tasks.filter(due_date__lte=timezone.now(), status='To Do')
    upcoming_tasks = tasks.filter(due_date__gt=timezone.now(), status='To Do')

    # Task Filtering and Sorting
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    category_filter = request.GET.get('category')
    order_by = request.GET.get('order_by', '-due_date')

    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if category_filter:
        tasks = tasks.filter(category=category_filter)

    tasks = tasks.order_by(order_by)

    categories = TaskCategory.objects.all()

    return render(request, 'tasks/project_detail.html', {
        'project': project,
        'tasks': tasks,
        'due_tasks': due_tasks,
        'upcoming_tasks': upcoming_tasks,
        'categories': categories,
    })


@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            return redirect('project_list')
    else:
        form = ProjectForm()
    return render(request, 'tasks/project_form.html', {'form': form, 'action': 'Create'})

@login_required
def project_update(request, project_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect('project_list')
    else:
        form = ProjectForm(instance=project)
    return render(request, 'tasks/project_form.html', {'form': form, 'action': 'Update'})

@login_required
def project_delete(request, project_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    project.delete()
    return redirect('project_list')

class CustomProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'tasks/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        # Add more context data as needed based on your model structure
        return context

@login_required
def profile_view(request):
    return render(request, 'tasks/profile.html', {'user': request.user})


def profile_update(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'tasks/profile_update.html', {'form': form})



@login_required
def task_create(request, project_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)

    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.save()
            return redirect('project_detail', project_id=project.id)
    else:
        form = TaskForm()

    return render(request, 'tasks/task_form.html', {'form': form, 'action': 'Create', 'project': project})

@login_required
def task_update(request, project_id, task_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    task = get_object_or_404(Task, id=task_id, project=project)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('project_detail', project_id=project.id)
    else:
        form = TaskForm(instance=task)

    return render(request, 'tasks/task_form.html', {'form': form, 'action': 'Update', 'project': project})

@login_required
def task_delete(request, project_id, task_id):
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    task = get_object_or_404(Task, id=task_id, project=project)

    if request.method == 'POST':
        task.delete()
        return redirect('project_detail', project_id=project.id)

    return render(request, 'tasks/task_confirm_delete.html', {'task': task, 'project': project})

def add_comment(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        form = TaskCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.user = request.user
            comment.save()
    return redirect('task_detail', task_id=task_id)


def add_attachment(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        form = TaskAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.task = task
            attachment.save()
    return redirect('task_detail', task_id=task_id)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  # Redirect to the home page or any desired page after registration
    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})