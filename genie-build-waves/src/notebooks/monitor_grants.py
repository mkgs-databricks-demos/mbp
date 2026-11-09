"""Least-privilege Unity Catalog grants that let an external monitor read the monitor skill.

Pure helpers (no SDK calls) for the setup notebook's "Grant monitor read access" cell.

UC Skills use the volume privileges (docs: AI Gateway > Govern skills). Reading one skill needs:

* USE CATALOG on the catalog and USE SCHEMA on the schema (traversal only), and
* READ VOLUME on that one skill (read its metadata and download SKILL.md).

READ VOLUME is granted on the skill, never on the schema: a schema grant would also cover
every other skill and volume in it. The runner and integrator skills are not shared: the
monitor reads the build's files and job runs, not the session prompts.

The build job grant is not here: `build_waves.job.yml` declares it (`monitor_principal` at
`monitor_job_level`), and `monitor_var_problems` checks those variables before a deploy.
"""

import json

# Privilege names as the Grants API spells them.
USE_CATALOG = "USE_CATALOG"
USE_SCHEMA = "USE_SCHEMA"
READ_VOLUME = "READ_VOLUME"
ALL_PRIVILEGES = "ALL_PRIVILEGES"

# Build job levels a monitor may get: report (level 1) or repair (levels 2-3). Never CAN_MANAGE
# or IS_OWNER: setup, deploys and permission changes stay with the instance owner.
MONITOR_JOB_LEVELS = ("CAN_VIEW", "CAN_MANAGE_RUN")


def monitor_grant_plan(catalog: str, schema: str, skill_id: str) -> list[tuple[str, str, str]]:
    """(securable_type, full_name, privilege) the monitor principal needs, outermost first."""
    schema_fqn = f"{catalog}.{schema}"
    return [
        ("catalog", catalog, USE_CATALOG),
        ("schema", schema_fqn, USE_SCHEMA),
        ("skill", f"{schema_fqn}.{skill_id}", READ_VOLUME),
    ]


def held_privileges(assignments) -> set[str]:
    """Privileges a principal holds on one securable, from a get_effective response.

    `assignments` is `privilege_assignments` as dicts or SDK objects: every entry counts,
    because effective permissions list grants held through groups and parents too.
    """
    held = set()
    for a in assignments or []:
        privs = a.get("privileges") if isinstance(a, dict) else getattr(a, "privileges", None)
        for p in privs or []:
            value = p.get("privilege") if isinstance(p, dict) else getattr(p, "privilege", p)
            value = getattr(value, "value", value)
            if value:
                held.add(str(value))
    return held


def has_privilege(held: set[str], privilege: str) -> bool:
    """ALL PRIVILEGES covers every privilege that applies to the securable."""
    return privilege in held or ALL_PRIVILEGES in held


def missing_grants(plan, held_by_securable: dict) -> list[tuple[str, str, str]]:
    """Plan entries the principal does not hold yet. `held_by_securable` maps
    (securable_type, full_name) to the held privilege set; a missing key counts as nothing held."""
    return [g for g in plan if not has_privilege(held_by_securable.get(g[:2], set()), g[2])]


def principal_problem(principal: str) -> str:
    """Why `principal` cannot be used, or "". Accepts a service principal application ID,
    a user name or a group name; rejects values that look like unresolved placeholders."""
    p = (principal or "").strip()
    if not p:
        return "monitor_principal is empty"
    if p != principal:
        return "monitor_principal has leading or trailing whitespace"
    if any(ch in p for ch in "{}<>`'\""):
        return f"monitor_principal {p!r} looks like a placeholder or contains quotes"
    return ""


def monitor_var_problems(variables: dict) -> list[str]:
    """Problems with the monitor bundle variables in a vars file (deploy_instance.py)."""
    variables = variables or {}
    problems = []
    principal = variables.get("monitor_principal") or ""
    level = variables.get("monitor_job_level", "CAN_VIEW")
    if principal and principal_problem(principal):
        problems.append(principal_problem(principal))
    if "@" in principal:
        problems.append("monitor_principal must be a service principal application ID, not a user name")
    if level not in MONITOR_JOB_LEVELS:
        problems.append(f"monitor_job_level {level!r} must be one of {', '.join(MONITOR_JOB_LEVELS)}")
    return problems


def grant_command(securable_type: str, full_name: str, privilege: str, principal: str) -> str:
    """Databricks CLI command an owner (or MANAGE holder) of the securable can run by hand."""
    body = json.dumps({"changes": [{"principal": principal, "add": [privilege]}]})
    return f"databricks grants update {securable_type} {full_name} --json '{body}'"
