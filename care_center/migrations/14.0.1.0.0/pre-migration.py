from openupgradelib import openupgrade


def migrate_task_parent_id_field(env):
    if openupgrade.column_exists(env.cr, 'project_task', 'parent_task_id'):
        openupgrade.logged_query(
            env.cr,
            'UPDATE project_task SET parent_id = parent_task_id WHERE parent_task_id IS NOT NULL',
        )


@openupgrade.migrate()
def migrate(env, version):
    migrate_task_parent_id_field(env)
