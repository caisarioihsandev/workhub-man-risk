# =========================================================
# WORKHUB RISK MANAGEMENT
# ACCESS CONTROL
# =========================================================

ROLE_PERMISSIONS = {

    "superadmin": {
        "dashboard",
        "work_progress",
        "risk_monitoring",
        "risk_assessment",
        "team_tasks",
        "documents",
        "user_management",
    },

    "user": {
        "dashboard",
        "work_progress",
        "risk_monitoring",
        "risk_assessment",
        "team_tasks",
        "documents",
    },

    "vice_president": {
        "dashboard",
        "work_progress",
        "risk_monitoring",
        "risk_assessment",
        "team_tasks",
        "documents",
    },

}


def has_permission(role, permission):
    return permission in ROLE_PERMISSIONS.get(
        role,
        set()
    )