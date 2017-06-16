# -*- coding: utf-8 -*-

{
    "name": "Project Issue Priority",
    "summary": "Adds Urgent and Crisis priorities to Issues",
    "version": "10.0.1.0.0",
    "author": "Dave Burkholder <dave@thinkwelldesigns.com>",
    "license": "AGPL-3",
    "category": "Project Management",
    "depends": ["project_issue"],
    "data": [
        'views/project_issue.xml',
    ],
    "installable": True,
    "uninstall_hook": "uninstall_hook"
}
