"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from apps.workflows.views import (
    trigger_workflow_api, list_workflows,
    workflow_detail_api, workflow_clone_api, workflow_export_api,
    workflow_import_api, workflow_publish_api, workflow_archive_api,
    execution_cancel_api, execution_resume_api, execution_search_api,
    execution_stats_api, workflow_templates_api,
)
from apps.accounts.views import (
    api_key_create, api_key_revoke, api_key_rotate, api_key_list,
    organization_create, organization_detail, organization_invite,
    organization_members, audit_log_list,
    role_assign, role_revoke, user_permissions,
)
from apps.monitoring.views import (
    dashboard_metrics_api, health_check_api, system_metrics_api,
    alerts_list_api, alert_acknowledge_api,
)
from apps.events.views import (
    event_list_api, event_replay_api, event_replay_status_api,
)
from apps.ai.views import (
    ai_generate_workflow_api, ai_classify_api, ai_extract_entities_api,
)
from apps.integrations.views import (
    webhook_receive_api, webhook_register_api,
    integration_list_api, integration_connect_api,
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # =========================
    # Workflows API
    # =========================
    path('api/trigger-workflow/', trigger_workflow_api, name='trigger_workflow'),
    path('api/workflows/', list_workflows, name='list_workflows'),
    path('api/workflows/<uuid:workflow_id>/', workflow_detail_api, name='workflow_detail'),
    path('api/workflows/<uuid:workflow_id>/clone/', workflow_clone_api, name='workflow_clone'),
    path('api/workflows/<uuid:workflow_id>/export/', workflow_export_api, name='workflow_export'),
    path('api/workflows/import/', workflow_import_api, name='workflow_import'),
    path('api/workflows/<uuid:workflow_id>/publish/', workflow_publish_api, name='workflow_publish'),
    path('api/workflows/<uuid:workflow_id>/archive/', workflow_archive_api, name='workflow_archive'),
    path('api/workflow-templates/', workflow_templates_api, name='workflow_templates'),
    
    # =========================
    # Executions API
    # =========================
    path('api/executions/<uuid:execution_id>/cancel/', execution_cancel_api, name='execution_cancel'),
    path('api/executions/<uuid:execution_id>/resume/', execution_resume_api, name='execution_resume'),
    path('api/executions/search/', execution_search_api, name='execution_search'),
    path('api/executions/stats/', execution_stats_api, name='execution_stats'),
    
    # =========================
    # Accounts / Auth API
    # =========================
    path('api/api-keys/', api_key_list, name='api_key_list'),
    path('api/api-keys/create/', api_key_create, name='api_key_create'),
    path('api/api-keys/<uuid:key_id>/revoke/', api_key_revoke, name='api_key_revoke'),
    path('api/api-keys/<uuid:key_id>/rotate/', api_key_rotate, name='api_key_rotate'),
    
    path('api/organizations/create/', organization_create, name='organization_create'),
    path('api/organizations/<slug:org_slug>/', organization_detail, name='organization_detail'),
    path('api/organizations/<slug:org_slug>/invite/', organization_invite, name='organization_invite'),
    path('api/organizations/<slug:org_slug>/members/', organization_members, name='organization_members'),
    
    path('api/audit-logs/', audit_log_list, name='audit_log_list'),
    path('api/roles/assign/', role_assign, name='role_assign'),
    path('api/roles/revoke/', role_revoke, name='role_revoke'),
    path('api/permissions/', user_permissions, name='user_permissions'),
    
    # =========================
    # Events API
    # =========================
    path('api/events/', event_list_api, name='event_list'),
    path('api/events/replay/', event_replay_api, name='event_replay'),
    path('api/events/replay/<uuid:job_id>/', event_replay_status_api, name='event_replay_status'),
    
    # =========================
    # Integrations API
    # =========================
    path('api/integrations/', integration_list_api, name='integration_list'),
    path('api/integrations/connect/', integration_connect_api, name='integration_connect'),
    path('api/webhooks/<path:url_path>/', webhook_receive_api, name='webhook_receive'),
    path('api/webhooks/register/', webhook_register_api, name='webhook_register'),
    
    # =========================
    # Monitoring API
    # =========================
    path('api/monitoring/dashboard/', dashboard_metrics_api, name='dashboard_metrics'),
    path('api/monitoring/health/', health_check_api, name='health_check'),
    path('api/monitoring/system-metrics/', system_metrics_api, name='system_metrics'),
    path('api/monitoring/alerts/', alerts_list_api, name='alerts_list'),
    path('api/monitoring/alerts/<uuid:alert_id>/acknowledge/', alert_acknowledge_api, name='alert_acknowledge'),
    
    # =========================
    # AI API
    # =========================
    path('api/ai/generate-workflow/', ai_generate_workflow_api, name='ai_generate_workflow'),
    path('api/ai/classify/', ai_classify_api, name='ai_classify'),
    path('api/ai/extract-entities/', ai_extract_entities_api, name='ai_extract_entities'),
]