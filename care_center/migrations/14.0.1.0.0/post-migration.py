from openupgradelib import openupgrade


def drop_unused_field(env):
    openupgrade.drop_columns(env.cr, [('project_task', 'parent_task_id')])


@openupgrade.migrate()
def migrate(env, version):
    drop_unused_field(env)
