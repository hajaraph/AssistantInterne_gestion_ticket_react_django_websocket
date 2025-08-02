from django.urls import path

from .views import UserRegistrationView, CustomTokenObtainPairView, UserProfileView, ChangePasswordView, \
    CategorieListView, EquipementListView, TicketCreateView, MyTicketsView, DepartementListView, TicketDetailView, \
    TicketStatsView, TechnicianTicketsView, AssignTicketToSelfView, UpdateTicketStatusView, TicketCommentsView, \
    StartGuidanceView, SendInstructionView, EndGuidanceView, ConfirmInstructionView

urlpatterns = [
    # Auth URLs
    path('register', UserRegistrationView.as_view(), name='register'),
    path('login', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('profile', UserProfileView.as_view(), name='user_profile'),
    path('change-password', ChangePasswordView.as_view(), name='change_password'),

    # Reference data URLs
    path('categories/', CategorieListView.as_view(), name='categories'),
    path('equipments/', EquipementListView.as_view(), name='equipments'),
    path('departments/', DepartementListView.as_view(), name='departments'),

    # Ticket URLs - Employee
    path('tickets/create', TicketCreateView.as_view(), name='create_ticket'),
    path('tickets/my/', MyTicketsView.as_view(), name='my_tickets'),
    path('tickets/<int:pk>/', TicketDetailView.as_view(), name='ticket_detail'),
    path('tickets/stats/', TicketStatsView.as_view(), name='ticket_stats'),

    # Ticket URLs - Technician
    path('technician/tickets/', TechnicianTicketsView.as_view(), name='technician_tickets'),
    path('technician/tickets/<int:ticket_id>/assign/', AssignTicketToSelfView.as_view(), name='assign_ticket'),
    path('technician/tickets/<int:ticket_id>/status/', UpdateTicketStatusView.as_view(), name='update_ticket_status'),

    # Comments and Chat URLs
    path('tickets/<int:ticket_id>/comments/', TicketCommentsView.as_view(), name='ticket_comments'),

    # Guidance URLs - Remote assistance
    path('tickets/<int:ticket_id>/guidance/start/', StartGuidanceView.as_view(), name='start_guidance'),
    path('tickets/<int:ticket_id>/guidance/instruction/', SendInstructionView.as_view(), name='send_instruction'),
    path('tickets/<int:ticket_id>/guidance/end/', EndGuidanceView.as_view(), name='end_guidance'),
    path('comments/<int:comment_id>/confirm/', ConfirmInstructionView.as_view(), name='confirm_instruction'),
]
