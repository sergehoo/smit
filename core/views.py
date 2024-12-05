from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import Group, User
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView

from core.models import Employee
from smit.forms import RoleForm, AssignRoleForm, EmployeeCreateForm


# Create your views here.


class RoleListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = "roles/role_list.html"
    context_object_name = "roles"

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     form = RoleForm()
    #     context['rolesform'] = form
    #     context['grouped_permissions'] = form.get_permissions_grouped_by_model()
    #     grouped_permissions = {}
    #
    #     # Grouper les permissions par content_type (fonctionnalité)
    #     for role in Group.objects.all():
    #         for perm in role.permissions.all():
    #             model_name = perm.content_type.model
    #             if model_name not in grouped_permissions:
    #                 grouped_permissions[model_name] = []
    #             grouped_permissions[model_name].append(perm)
    #
    #     context['grouped_permissions'] = grouped_permissions
    #     return context
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = RoleForm()
        context['rolesform'] = form
        context['grouped_permissions'] = form.get_permissions_grouped_by_model()  # Appel direct pour grouper
        return context


class RoleCreateView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = RoleForm
    success_url = reverse_lazy('user_role')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.permissions.set(form.cleaned_data['permissions'])
        self.object.save()
        return response


class RoleUpdateView(LoginRequiredMixin, UpdateView):
    model = Group
    form_class = RoleForm
    template_name = "roles/role_update.html"
    success_url = reverse_lazy('user_role')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.permissions.set(form.cleaned_data['permissions'])
        self.object.save()
        return response


class RoleDeleteView(LoginRequiredMixin, DeleteView):
    model = Group
    template_name = "roles/role_confirm_delete.html"
    success_url = reverse_lazy('user_role')

    def form_valid(self, form):
        # Créer l'employé
        response = super().form_valid(form)
        messages.success(self.request, "Role supprimer avec successfully")
        return response


class AssignRoleView(LoginRequiredMixin, FormView):
    form_class = AssignRoleForm
    template_name = "roles/assign_role.html"
    success_url = reverse_lazy("role_list")

    def form_valid(self, form):
        employee_id = self.kwargs.get("pk")
        employee = get_object_or_404(Employee, pk=employee_id)
        role = form.cleaned_data["role"]
        employee.user.groups.add(role)
        return super().form_valid(form)


class EmployeeListView(PermissionRequiredMixin, ListView):
    model = Employee
    template_name = "employees/employee_list.html"
    context_object_name = "employees"
    paginate_by = 10
    ordering = ['user__first_name', 'user__last_name']
    permission_required = 'core.can_view_employee'

    # def get_ordering(self):
    #     # Récupère l'ordre de tri à partir de l'URL ou utilise 'nom' par défaut
    #     return self.request.GET.get('ordering', 'nom')


class EmployeeCreateView(LoginRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeCreateForm
    template_name = "employees/employee_form.html"
    success_url = reverse_lazy("employee_list")
    permission_required = 'can_view_employee'

    def form_valid(self, form):
        # Créer l'utilisateur
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        email = form.cleaned_data['email']
        role = form.cleaned_data['role']

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email
        )

        # Associer le rôle à l'utilisateur
        user.groups.add(role)

        # Créer l'employé en associant l'utilisateur
        employee = form.save(commit=False)
        employee.user = user
        employee.save()
        messages.success(self.request, "Employee creer avec successfully")
        return super().form_valid(form)


class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeCreateForm
    template_name = "employees/employee_form.html"
    success_url = reverse_lazy("employee_list")

    def form_valid(self, form):
        # Créer l'employé
        response = super().form_valid(form)
        role = form.cleaned_data["role"]
        self.object.user.groups.add(role)
        return response


class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    model = Employee
    template_name = "roles/employee_confirm_delete.html"
    success_url = reverse_lazy('employee_list')

    def form_valid(self, form):
        # Créer l'employé
        response = super().form_valid(form)
        messages.success(self.request, "Employee supprimer avec successfully")
        return response
