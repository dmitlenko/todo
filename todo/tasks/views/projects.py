from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.query import QuerySet
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from todo.core.utils.htmx import render_swap, reswap
from todo.core.utils.modal import HIDE_MODAL_EVENT, ModalMixin, hide_modal
from todo.tasks.forms import ProjectForm
from todo.tasks.models import Project


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "tasks/project/list.html"
    context_object_name = "projects"

    def get_queryset(self):
        return self.request.user.projects.all()


class ProjectCreateView(LoginRequiredMixin, ModalMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "tasks/project/create_modal.html"
    success_url = "/"

    def form_valid(self, form):
        # Set the user of the project to the current user
        form.instance.user = self.request.user

        # Run the parent form_valid method to save the form
        super().form_valid(form)

        # Return the rendered project item template
        # to be swapped into the project list and trigger
        # hide modal event to close the modal.
        return render_swap(
            self.request,
            "tasks/project/item.html",
            context={
                "project": form.instance,
            },
            params={
                "swap": "beforeend",
                "target": "[data-project-list]",
                "select": ".card",
            },
            trigger=[HIDE_MODAL_EVENT],
        )


class ProjectUpdateView(LoginRequiredMixin, ModalMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "tasks/project/update_modal.html"
    success_url = "/"

    def form_valid(self, form):
        # Run the parent form_valid method to save the form
        super().form_valid(form)

        # Return the rendered project item template
        # to be swapped into the project list and trigger
        # hide modal event to close the modal.
        return render_swap(
            self.request,
            "tasks/project/item.html",
            context={
                "project": form.instance,
            },
            params={
                "swap": "innerHTML",
                "target": f'[data-project="{form.instance.pk}"] .project-name',
                "select": ".project-name",
            },
            trigger=[HIDE_MODAL_EVENT],
        )


class ProjectDeleteView(LoginRequiredMixin, ModalMixin, DeleteView):
    model = Project
    template_name = "tasks/project/delete_modal.html"
    success_url = "/"

    def get_queryset(self) -> QuerySet[Any]:
        # Filter the queryset to only return tasks
        # that are owned by the user.
        return self.request.user.projects.all()

    def delete(self, *args, **kwargs):
        # Run the parent delete method to delete the task
        response = super().delete(*args, **kwargs)

        # Status code 200 is required by HTMX
        # to delete the item from the DOM.
        # See: https://htmx.org/attributes/hx-delete/ for more information.
        response.status_code = 200

        # Return the response object with the hide modal event
        # to close the modal after the project is deleted.
        return hide_modal(
            reswap(
                response,
                {"target": f'[data-project="{self.kwargs["pk"]}"]'},
            ),
            {},
        )
