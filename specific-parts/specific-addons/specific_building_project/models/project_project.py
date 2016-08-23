# -*- coding: utf-8 -*-
# © 2016 Cyril Gaudin (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models

from lxml import etree


class ProjectProject(models.Model):
    _inherit = 'project.project'

    department_id = fields.Many2one(
        comodel_name='hr.department',
        default=lambda self: self.user_id.department_id
    )

    building_project_id = fields.Many2one(
        comodel_name='building.project',
        compute='_compute_building_project_id'
    )

    @api.multi
    def _compute_building_project_id(self):
        building_obj = self.env['building.project']
        for record in self:
            record.building_project_id = building_obj.search(
                [('project_id', '=', record.id)],
                limit=1
            )[:1]

    @api.onchange('user_id')
    def onchange_user_id(self):
        """ Set department_id to user_id.department_id if empty
        """
        if not self.department_id:
            self.department_id = self.user_id.department_id

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        """ Modify search view to add a filter on connected user department.
        """

        result = super(ProjectProject, self).fields_view_get(
            cr, uid, view_id, view_type, context, toolbar, submenu
        )

        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        if view_type == 'search':
            eview = etree.fromstring(result['arch'])
            nodes = eview.xpath("//filter[@name='department']")
            if nodes:
                if user.department_id:
                    nodes[0].set(
                        'domain',
                        "['|', ('department_id', 'child_of', [%s]), "
                        "('department_id', 'parent_of', [%s])]"
                        % (user.department_id.id, user.department_id.id)
                    )
                else:
                    eview.remove(nodes[0])
            result['arch'] = etree.tostring(eview)

        return result