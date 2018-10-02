.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

======================
Care Center Timesheets
======================

Add Start / Pause / Stop buttons to Tasks / Tickets, in Kanban and Form views,
so users can easily clock In / Out as they work on Tasks / Tickets.

Also adds Project and Task reports that include all the timesheets so that customers
can get a quick summary of the work that was done, for which they will be invoiced.


*Note!* This module includes the fuctionality of sale_timesheet_invoice_description.
Both cannot be installed at the same time.

Usage
=====

For initial setup:

#. Go to *Sales -> Sales Orders* and create a new Sales Orders.
#. Add line selecting a product with

   - *Invoicing Policy* -> **Delivered quantities**

   - *Track Service* -> **Timesheets on contract**

   e.g. *Support Contract (on timesheet)*
#. Confirm Sale
#. Create a Task and add Timesheets with Start / Pause / Stop buttons.
#. Finish Task and set to Invoiceable.
#. Go to Sales Orders and select *Other Information* -> **Timesheet invoice
   description**
#. Create Invoice.


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/thinkwell/care_center/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Imag
------

Contributors
------------

* Dave Burkholder <dave@thinkwelldesigns.com>
