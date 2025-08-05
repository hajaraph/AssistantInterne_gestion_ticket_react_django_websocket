from django.urls import path

from .views import (
    UserRegistrationView, CustomTokenObtainPairView, UserProfileView, ChangePasswordView,
    CategorieListView, EquipementListView, TicketCreateView, MyTicketsView, DepartementListView,
    TicketDetailView, TicketStatsView, TechnicianTicketsView, AssignTicketToSelfView,
    UpdateTicketStatusView, TicketCommentsView, StartGuidanceView, SendInstructionView,
    EndGuidanceView, ConfirmInstructionView,
    # Vues de diagnostic existantes
    DiagnosticCategoriesView, SessionDiagnosticCreateView, SessionDiagnosticDetailView,
    ProchaineQuestionView, RepondreDiagnosticView, DiagnosticSystemeView,
    HistoriqueDiagnosticsView, CreerTicketDepuisDiagnosticView,
    # Nouvelles vues avancées
    TemplatesDiagnosticView, SessionStatistiquesView, SessionReprendreView,
    SessionPauseView, ReponseAvanceeView, QuestionAvanceeView,
    DiagnosticAnalyticsView, DiagnosticAccueilView, DiagnosticEtapesView, ExecuterEtapeView, PasserEtapeView,
    # Vues du tableau de bord
    DashboardDataView
)

urlpatterns = [
    # Auth URLs
    path('register', UserRegistrationView.as_view(), name='register'),
    path('login', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('profile', UserProfileView.as_view(), name='user_profile'),
    path('change-password', ChangePasswordView.as_view(), name='change_password'),

    # Reference data URLs
    path('categories', CategorieListView.as_view(), name='categories'),
    path('equipments', EquipementListView.as_view(), name='equipments'),
    path('departments', DepartementListView.as_view(), name='departments'),

    # Ticket URLs - Employee
    path('tickets/create', TicketCreateView.as_view(), name='create_ticket'),
    path('tickets/my', MyTicketsView.as_view(), name='my_tickets'),
    path('tickets/<int:pk>', TicketDetailView.as_view(), name='ticket_detail'),
    path('tickets/stats', TicketStatsView.as_view(), name='ticket_stats'),

    # Ticket URLs - Technician
    path('technician/tickets', TechnicianTicketsView.as_view(), name='technician_tickets'),
    path('technician/tickets/<int:ticket_id>/assign', AssignTicketToSelfView.as_view(), name='assign_ticket'),
    path('technician/tickets/<int:ticket_id>/status', UpdateTicketStatusView.as_view(), name='update_ticket_status'),

    # Dashboard URL
    path('dashboard', DashboardDataView.as_view(), name='dashboard_data'),

    # Comments and Chat URLs
    path('tickets/<int:ticket_id>/comments', TicketCommentsView.as_view(), name='ticket_comments'),

    # Guidance URLs - Remote assistance
    path('tickets/<int:ticket_id>/guidance/start', StartGuidanceView.as_view(), name='start_guidance'),
    path('tickets/<int:ticket_id>/guidance/instruction', SendInstructionView.as_view(), name='send_instruction'),
    path('tickets/<int:ticket_id>/guidance/end', EndGuidanceView.as_view(), name='end_guidance'),
    path('comments/<int:comment_id>/confirm', ConfirmInstructionView.as_view(), name='confirm_instruction'),

    # URLs pour le système de diagnostic intelligent de base
    path('diagnostic/categories', DiagnosticCategoriesView.as_view(), name='diagnostic_categories'),
    path('diagnostic/session/create', SessionDiagnosticCreateView.as_view(), name='create_diagnostic_session'),
    path('diagnostic/session/<int:session_id>', SessionDiagnosticDetailView.as_view(), name='diagnostic_session_detail'),
    path('diagnostic/session/<int:session_id>/next-question', ProchaineQuestionView.as_view(), name='next_question'),
    path('diagnostic/session/<int:session_id>/answer', RepondreDiagnosticView.as_view(), name='answer_diagnostic'),
    path('diagnostic/session/<int:session_id>/system-check', DiagnosticSystemeView.as_view(), name='system_diagnostic'),
    path('diagnostic/session/<int:session_id>/create-ticket', CreerTicketDepuisDiagnosticView.as_view(), name='create_ticket_from_diagnostic'),
    path('diagnostic/history', HistoriqueDiagnosticsView.as_view(), name='diagnostic_history'),

    # URLs pour les fonctionnalités avancées du diagnostic
    path('diagnostic/accueil', DiagnosticAccueilView.as_view(), name='diagnostic_accueil'),
    path('diagnostic/templates', TemplatesDiagnosticView.as_view(), name='diagnostic_templates'),
    path('diagnostic/session/<int:session_id>/stats', SessionStatistiquesView.as_view(), name='session_statistics'),
    path('diagnostic/session/<int:session_id>/resume', SessionReprendreView.as_view(), name='resume_session'),
    path('diagnostic/session/<int:session_id>/pause', SessionPauseView.as_view(), name='pause_session'),
    path('diagnostic/session/<int:session_id>/answer-advanced', ReponseAvanceeView.as_view(), name='answer_advanced'),
    path('diagnostic/session/<int:session_id>/question-advanced', QuestionAvanceeView.as_view(), name='question_advanced'),
    # path('diagnostic/session/<int:session_id>/export/', ExportDiagnosticView.as_view(), name='export_diagnostic'),
    path('diagnostic/analytics', DiagnosticAnalyticsView.as_view(), name='diagnostic_analytics'),

    # URLs pour le diagnostic par étapes
    path('diagnostic/etapes/start', DiagnosticEtapesView.as_view(), name='start_diagnostic_etapes'),
    path('diagnostic/etapes/<int:session_id>', DiagnosticEtapesView.as_view(), name='get_diagnostic_etapes'),
    path('diagnostic/etapes/<int:session_id>/execute', ExecuterEtapeView.as_view(), name='execute_etape'),
    path('diagnostic/etapes/<int:session_id>/navigate', PasserEtapeView.as_view(), name='navigate_etape'),
]
