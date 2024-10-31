from datetime import date

from django.core.paginator import Paginator
from django_unicorn.components import UnicornView

from core.models import Service, Employee
from smit.models import Appointment


class AppointmentFilterView(UnicornView):
    appointments = []
    search_query = ""
    selected_status = ""
    selected_service = ""
    date_filter = "all"  # Options: "all", "past", "today", "upcoming"
    per_page = 10
    page_number = 1
    order_by = "desc"  # Options: "asc", "desc"
    total_pages = 1  # To hold total number of pages

    def mount(self):
        self.get_appointments()

    def get_appointments(self):
        query = Appointment.objects.all()

        # Apply search query
        if self.search_query:
            query = query.filter(patient__name__icontains=self.search_query)

        # Apply filters
        if self.selected_status:
            query = query.filter(status=self.selected_status)
        if self.selected_service:
            query = query.filter(service__name=self.selected_service)
        if self.date_filter == "past":
            query = query.filter(date__lt=date.today())
        elif self.date_filter == "today":
            query = query.filter(date=date.today())
        elif self.date_filter == "upcoming":
            query = query.filter(date__gt=date.today())

        # Order by date
        if self.order_by == "desc":
            query = query.order_by("-date")
        else:
            query = query.order_by("date")

        # Paginate results
        paginator = Paginator(query, self.per_page)
        page_obj = paginator.get_page(self.page_number)

        # Update appointments and pagination info
        self.appointments = list(page_obj.object_list.values())  # Convert queryset to list of dicts
        self.total_pages = paginator.num_pages  # Set total pages

    def change_order(self, order):
        self.order_by = order
        self.get_appointments()

    def change_per_page(self, per_page):
        self.per_page = per_page
        self.get_appointments()

    def filter_by_status(self, status):
        self.selected_status = status
        self.get_appointments()

    def filter_by_service(self, service):
        self.selected_service = service
        self.get_appointments()

    def filter_by_date(self, date_filter):
        self.date_filter = date_filter
        self.get_appointments()

    def update_search(self, search_query):
        self.search_query = search_query
        self.get_appointments()

    def next_page(self):
        if self.page_number < self.total_pages:
            self.page_number += 1
            self.get_appointments()

    def previous_page(self):
        if self.page_number > 1:
            self.page_number -= 1
            self.get_appointments()