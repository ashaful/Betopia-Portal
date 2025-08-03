# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class InheritResUser(models.Model):
    _inherit = 'res.users'

    department_head = fields.Boolean()
    category = fields.Selection([
        ('it', 'It'),
        ('admin', 'Admin'),
    ])

    # For it dept. only
    it_department = fields.Boolean()

    # For all dept.
    admin_department = fields.Boolean()
    finance_department = fields.Boolean()
    scm_department = fields.Boolean()
    is_ceo = fields.Boolean()

    can_create_sale = fields.Boolean(string='Can Create Sale')
    is_project_manager = fields.Boolean(string='Project Manager')

# _________________________________________RAYTA____________________________________________________

    sale_leader = fields.Boolean(string='Sale Leader')
    sales_man = fields.Boolean(string='Sales Man')
    operation_leader = fields.Boolean(string='Operation Leader')
    operation_man = fields.Boolean(string='Operation Man')
    bus_dev = fields.Boolean(string='Business Development')

# _________________________________________MORSALIN____________________________________________________

    
    requisition_access = fields.Boolean(string='Requisition Access')
    is_hto=fields.Boolean(string="Head of Technical Operation")
    



class ServiceType(models.Model):
    _name = "service.type"
    _description = "Service Type"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(string="Active", default=True)
    name = fields.Char(string='Name', required=True)
    service_manager_ids = fields.Many2many('hr.employee','service_type_id', string='Manager', required=True)

    # service_manager_badge_id = fields.Char(
    #     string='Manager Badge ID',
    #      related='service_manager.barcode',
    #     store=False,
    #     readonly=True
    # )

    company_id = fields.Many2one('res.company', string='Company')
    assign_team_ids = fields.One2many('assign.team', 'service_type_id', string='Assign Teams')

    



class AssignTeam(models.Model):
    _name = 'assign.team'
    _description = 'Assign Team'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(string="Active", default=True)
    name = fields.Char(string='Name', required=True)
    team_leader = fields.Many2one('res.users', string='Team Leader')

    team_leader_badge_id = fields.Char(
        string='Leader Badge ID',
        related='team_leader.barcode',
        store=False,
        readonly=True
    )

    team_members = fields.Many2many(
        'hr.employee',
        'assign_team_id',
        string='Team Members'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='service_type_id.company_id',
        store=True,
        readonly=False
    )

    service_type_id = fields.Many2one('service.type', string='Service Type')

   

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    assign_team_id = fields.Many2one('assign.team', string='Assign Team', help='Team assigned to the employee')
    employee_types = fields.Many2one('hr.contract.type', string='Employee Type')
    leader_id = fields.Many2one('hr.employee', string='Team Leader')
    parent_ids = fields.Many2many(
    'hr.employee',
    'employee_manager_rel',     # This is the M2M relation table name
    'employee_id',              # This is the column for the current employee (source)
    'manager_id',               # This is the column for the related employee (target)
    string='Managers'
    )
    show_employee_details = fields.Boolean(
        string="Show Employee Details",
        default=False
    )

    service_type_id = fields.Many2one('service.type',string="Service Type")
    
    @api.constrains('assign_team_id', 'company_id')
    def _check_team_company(self):
        for employee in self:
            if employee.assign_team_id and employee.company_id and employee.assign_team_id.company_id != employee.company_id:
                raise ValidationError(_("The assigned team must belong to the same company as the employee."))
    
    


    @api.onchange('assign_team_id')
    def _onchange_assign_team_id(self):
        for emp in self:
            team = emp.assign_team_id

            # Reset defaults
            emp.leader_id = False
            emp.parent_ids = [(5, 0, 0)]  # clear many2many

            # Assign leader if team exists
            if team and team.team_leader:
                leader_employee = self.env['hr.employee'].search(
                    [('user_id', '=', team.team_leader.id)],
                    limit=1
                )
                emp.leader_id = leader_employee or False

            # Assign parent_ids if service managers exist
            if team and team.service_type_id and team.service_type_id.service_manager_ids:
                emp.parent_ids = team.service_type_id.service_manager_ids

    @api.model_create_multi
    def create(self, vals_list):
        employees = super().create(vals_list)
        for employee, vals in zip(employees, vals_list):
            team_id = vals.get('assign_team_id')
            if team_id:
                team = self.env['assign.team'].browse(team_id)
                if employee not in team.team_members:
                    team.team_members = [(4, employee.id)]
        return employees

    def write(self, vals):
        old_teams = {emp.id: emp.assign_team_id for emp in self}
        result = super(HrEmployee, self).write(vals)

        for emp in self:
            old_team = old_teams.get(emp.id)
            new_team = emp.assign_team_id

            if 'assign_team_id' in vals:
                if old_team and emp in old_team.team_members:
                    old_team.team_members = [(3, emp.id)]

                if new_team and emp not in new_team.team_members:
                    new_team.team_members = [(4, emp.id)]

        return result
    
    @api.depends('user_id')
    def _compute_show_employee_details(self):
        for emp in self:
            if emp.user_id.id == user_id.id:
                 emp.show_employee_details = True
                
            
            
            
