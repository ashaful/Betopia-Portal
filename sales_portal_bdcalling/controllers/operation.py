
# -*- coding: utf-8 -*-

import json

from odoo import http
from odoo.http import request, request as req
from odoo import Command
from datetime import datetime, time, date, timedelta
import math
from werkzeug.utils import redirect
import base64
from collections import defaultdict
import pytz
from odoo import models, fields, api
import calendar
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.exceptions import AccessError
import logging
_logger = logging.getLogger(__name__)

# class PortalProjectOperation(http.Controller):

#     @http.route(['/my/project/operations'], type='http', auth="user", website=True)
#     def portal_project_operations(self, **kwargs):
#         user = request.env.user
#         employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

#         if not employee:
#             raise AccessError("No employee record found for current user.")

#         # 1. Directly assigned operations
#         domain_employee = [('employee_id', '=', employee.id)]

#         # 2. Operations where user is team leader
#         team_ids = request.env['assign.team'].sudo().search([('team_leader', '=', user.id)]).ids
#         domain_team_leader = [('assigned_team_id', 'in', team_ids)]

#         # 3. Operations where user is a service manager
#         service_type_ids = request.env['service.type'].sudo().search([
#             ('service_manager_ids', 'in', employee.id)
#         ]).ids
#         manager_team_ids = request.env['assign.team'].sudo().search([
#             ('service_type_id', 'in', service_type_ids)
#         ]).ids
#         domain_service_manager = [('assigned_team_id', 'in', manager_team_ids)]

#         # Combine domains using OR logic
#         domain = ['|', '|'] + domain_employee + domain_team_leader + domain_service_manager

#         # Fetch project operations
#         operations = request.env['project.operation'].sudo().search(domain)

#         # Return to a QWeb template for portal display
#         return request.render('sales_portal_bdcalling.portal_project_operations_template', {
#             'operations': operations,
#         })
class PortalWebsite(http.Controller):   
        
    @http.route(['/sale/operation'], type='http', auth="user", website=True)
    def operation_form(self, **kw):
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([
            ('user_id', '=', user.id)
        ], limit=1)

        if not employee or not (user.operation_leader or user.is_hto):
            return request.redirect('/my')

        team_ids = None
        if user.operation_leader:
            team_id = request.env['assign.team'].sudo().search([('team_leader', '=', user.id)],limit=1)
            if team_id:
                team_ids=team_id
    
        
        if user.is_hto:
            ServiceType = request.env['service.type']

            # Find all service types where the current user is a service manager
            service_types = ServiceType.search([
                ('service_manager_ids.user_id', '=', user.id)
            ])

            # Fetch all assign teams linked to these service types
            assign_teams = request.env['assign.team'].search([
                ('service_type_id', 'in', service_types.ids)
            ])
            if assign_teams:
                team_ids =assign_teams



        today = fields.Date.today().strftime('%Y-%m-%d')
        values = {
            'team_id': team_ids,
            'employee': employee,
            # 'team_members': team_members,
            'today': today,
        }
       
  
        return request.render('sales_portal_bdcalling.operation_form_template', values, {'datetime': datetime})

        #team = request.env['assign.team'].sudo().search([
        #    ('team_leader', '=', user.id)
        #], limit=1)
        #team_members = False
        #if team:
        #    team_members = request.env['hr.employee'].sudo().search([
        #        ('assign_team_id', '=', team.id)
         #   ], limit=1)
            
        #team_id = request.env['assign.team'].sudo().search([('company_id', '=', user.company_id.id)])
        #today = fields.Date.today().strftime('%Y-%m-%d')
        #values = {
         #   'team_id': team_id,
         #   'employee': employee,
        #    'team_members': team_members,
         #   'today': today,
       # }
      

    @http.route(['/operation/details'], type='http', auth="user", website=True)
    def operation_form_update(self, **kw):
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

        if not employee or not (user.operation_leader or user.is_hto):
            return request.redirect('/my')
        teams = None
        if user.is_hto:
            service_type_ids = request.env['service.type'].sudo().search([
                ('service_manager_ids', 'in', employee.id)
            ]).ids
            manager_teams = request.env['assign.team'].sudo().search([
                ('service_type_id', 'in', service_type_ids)
            ])
            teams = manager_teams
        if user.operation_leader:
            team_id = request.env['assign.team'].sudo().search([('team_leader', '=', user.id)])
            teams = team_id
       
        order_id = kw.get('order_id')
        if not order_id:
            return 'order_id not found'

        order_id = int(order_id)

        order = req.env['project.operation'].sudo().search(
            [('id', '=', order_id)])

        if not order:
            return {'error': 'Order not found'}
        team_members = False

        team = request.env['assign.team'].sudo().search([
            ('team_leader', '=', user.id)
        ], limit=1)
        if team:
            team_members = team.team_members
            
        
       
        today = fields.Date.today().strftime('%Y-%m-%d')
        values = {
            'team_id': teams,
            'employee': employee,
            'team_members': team_members,
            'today': today,
            'order': order,
        }
        return request.render('sales_portal_bdcalling.operation_update_form_template', values)

    @http.route(['/sale/create_operation'], type='json', auth="user", website=True)
    def create_operation(self, **kw):
        try:
            data = kw
            user = request.env.user
            _logger.info("User: %s", user)
            employee = request.env['hr.employee'].sudo().search([
                ('user_id', '=', user.id)
            ], limit=1)
            _logger.info("Employee: %s", employee)
            if not employee:
                return {'success': False, 'error': 'Invalid user'}
            _logger.info("Received all data: %s", data)
            order_no = kw.get('order_id')
            _logger.info('order_id %s', order_no)
        
            assign_team =  kw.get('team_id')
            # if assign_team:
            #     return {'success': False, 'error': ' Please update Assign Team.'}
           
            
            order_vals = {
                'employee_id': kw.get('employee_id'),
                'order_id': kw.get('order_id') if kw.get('order_id') else False,
                'project': kw.get('profile_name') if kw.get('profile_name') else False,
                'instruction_sheet_link': kw.get('instruction_sheet_link') if kw.get('instruction_sheet_link') else False,
                'date': kw.get('date'),
                'percentage': kw.get('percentage'),
                'monetary_value': kw.get('monetary_value'),
                'delivery_amount': kw.get('delivery_amount'),
                'so_id': kw.get('so_id') if kw.get('so_id') else False,
                'special_remarks': kw.get('special_remarks') if kw.get('special_remarks') else False,
                'order_status': kw.get('order_status') if kw.get('order_status') else 'draft',
                'assigned_team_id': kw.get('team_id') if kw.get('team_id') else False,
                'order_link':kw.get('order_link') if kw.get('order_link') else "N/A",
                'client_name':kw.get('partner_id') if kw.get('partner_id') else "",
                'assign_employee_id':employee.id,
                # 'employee_id_barcode':employee.barcode,
            }

            _logger.info("Order values: %s", order_vals)
            print("Partner",kw.get('partner_id') if kw.get('partner_id') else "")
           
            order = request.env['project.operation'].sudo().create(order_vals)
            
            if order:
                return {
                    'success': True,
                    'message': 'Operation created successfully',
                    'order_id': order.id,
                }
            else:
                return {
                    'success': False,
                    'message': 'Please fill the form correctly.',
                }

        except Exception as e:
            _logger.error("Error Creating Operation: %s",
                          str(e), exc_info=True)
            return {'success': False, 'error': str(e)}

    @http.route('/sale/get_order_info', type='json', auth='user')
    def get_order_info(self, order_number):
        sale_order = request.env['sale.order'].sudo().search(
            [('order_number', '=', order_number)], limit=1)

        if not sale_order:
            return {"success": False, "message": "Order not found"}
        _logger.info('partner_id______________________ %s', sale_order.partner_id.name)
        values= {
            "success": True,
            'so_id': sale_order.id,
            "delivery_amount": sale_order.delivery_amount,
            "instruction_sheet_link": sale_order.instruction_sheet_link or 'N/A',
            "team_id": sale_order.assign_team_id.id if sale_order.assign_team_id else 'N/A',
            "partner_name": sale_order.partner_id.name if sale_order.partner_id else 'N/A',
            "order_link": sale_order.order_link or 'N/A',
            "profile_name":sale_order.profile_id.name or 'N/A',
            "partner_id": sale_order.partner_id if sale_order.partner_id else False,
            "client_id": sale_order.partner_id if sale_order.partner_id else False,
        }
        print("ORder Values",values)
        return values
    
    @http.route('/sale/get_team_members', type='json', auth='user')
    def get_team_members(self, employee_id):
        emp = request.env['hr.employee'].sudo().search(
            [('id', '=', employee_id)], limit=1)

        if not emp:
            return {"success": False, "message": "Employee not found"}

        return {
            "success": True,
            "employee_barc": emp.barcode or '',
            "company_name": emp.company_id.name or '',
        }

    @http.route('/operation_dashboard', type='http', auth="user", website=True)
    def dashboard(self, assign_team_id=None, status=None,year=None, month=None, **kw):
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

     
        if not employee or not (user.operation_leader or user.operation_man or user.is_hto):
            return request.redirect('/my')
        
        # 1. Directly assigned operations
        domain_employee = [('employee_id', '=', employee.id)]

        # 2. Operations where user is team leader
        team_ids = request.env['assign.team'].sudo().search([('team_leader', '=', user.id)]).ids
        domain_team_leader = [('assigned_team_id', 'in', team_ids)]

        # 3. Operations where user is a service manager
        service_type_ids = request.env['service.type'].sudo().search([
            ('service_manager_ids', 'in', employee.id)
        ]).ids
        manager_team_ids = request.env['assign.team'].sudo().search([
            ('service_type_id', 'in', service_type_ids)
        ]).ids
        domain_service_manager = [('assigned_team_id', 'in', manager_team_ids)]

        manager_teams = request.env['assign.team'].sudo().search([
            ('service_type_id', 'in', service_type_ids)
        ])
       
       
        domain = ['|', '|'] + domain_employee + domain_team_leader + domain_service_manager
        search_value = kw.get('search_value', '')
      
        
        today = fields.Date.today()
        if year and month:
            start_date = f"{year}-{month}-01"
            # Calculate end date (last day of the month)
            end_date = datetime.strptime(
                start_date, "%Y-%m-%d") + timedelta(days=31)
            end_date = end_date.replace(day=1) - timedelta(days=1)
        else:
            start_date = today.replace(day=1)
            next_month = today.replace(day=28) + timedelta(days=4)
            end_date = next_month.replace(day=1) - timedelta(days=1)

        # Convert to string format if needed
        start_date_str = start_date if isinstance(
            start_date, str) else start_date.strftime("%Y-%m-%d")
        end_date_str = end_date if isinstance(
            end_date, str) else end_date.strftime("%Y-%m-%d")

        # Add date filter to domain
        if year and month:
            domain.append(('date', '>=', start_date_str))
            domain.append(('date', '<=', end_date_str))
        if assign_team_id:
            domain.append(('assigned_team_id', '=', int(assign_team_id)))
            
        if status:
            domain.append(('order_status', '=', status))
        
        
        operations = request.env['project.operation'].sudo().search(domain,order="id desc")
    
        if search_value:
            domain += ['|'] * 8 + [
                ('name', 'ilike', search_value),
                ('partner_id.name', 'ilike', search_value),
                ('partner_id.phone', 'ilike', search_value),
                ('partner_id.email', 'ilike', search_value),
                ('user_id.name', 'ilike', search_value),
                ('order_number', 'ilike', search_value),
                ('order_link', 'ilike', search_value),
                ('instruction_sheet_link', 'ilike', search_value),
                ('service_type_id.name', 'ilike', search_value),
            ]
        
        # Fetch project operations
        filter_operations = operations.sudo().search(domain)

        
        minimum_target = employee.minimum_target
        achieved_sales = 0.0
        balance_amount = 0.0
        bonus_amount = 0.0
        
        def format_currency(value, is_bonus=False):
            currency_symbol = request.env.company.currency_id.symbol if is_bonus else '$'
            return currency_symbol + ' ' + '{:,.2f}'.format(value)

        values = {
            'orders': filter_operations,
            'res_company': request.env.company,
            'manager_teams':manager_teams,
           
            'minimum_target': format_currency(minimum_target),
            'achieved_sales': format_currency(achieved_sales),
            'balance_amount': format_currency(balance_amount),
            'bonus_amount': format_currency(bonus_amount, is_bonus=True),
            'minimum_target_raw': minimum_target,
            'achieved_sales_raw': achieved_sales,
            'balance_amount_raw': balance_amount,
            'bonus_amount_raw': bonus_amount,
        }
        
        return request.render('sales_portal_bdcalling.operation_dash_template', values)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
    # def dashboard(self, assign_team_id=None, year=None, month=None, **kw):

    #     # Check if the logged-in user is a sales head
    #     user = request.env.user
    #     employee_id = request.env['hr.employee'].sudo().search([
    #         ('user_id', '=', user.id)
    #     ], limit=1)
        
    #     if user.operation_leader:
            
    #         print("Operateion Leader",user.operation_leader)
    #         print("Employee ID",user.employee_id)
            
    #     else:
    #         print(user)
    #     emp_assign_team_leader = employee_id.assign_team_id.team_leader
    #     is_sales_head = user.has_group('sales_team.group_sale_manager')
        # search_value = kw.get('search_value', '')
        # _logger.info('Search Value: %s', search_value)
        
        
        
        
        
    #     operation_order = request.env['project.operation'].sudo().search([])
        
        
    #     print("Assign Team ID",emp_assign_team_leader)
        
        

        # page = int(kw.get('page', 1)) or 1
        # per_page = 20
        # offset = (page - 1) * per_page
        # domain = []
        # if not is_sales_head:
        #     domain = [('user_id', '=', user.id)]

        # today = fields.Date.today()
        # if year and month:
        #     start_date = f"{year}-{month}-01"
        #     # Calculate end date (last day of the month)
        #     end_date = datetime.strptime(
        #         start_date, "%Y-%m-%d") + timedelta(days=31)
        #     end_date = end_date.replace(day=1) - timedelta(days=1)
        # else:
        #     start_date = today.replace(day=1)
        #     next_month = today.replace(day=28) + timedelta(days=4)
        #     end_date = next_month.replace(day=1) - timedelta(days=1)

        # # Convert to string format if needed
        # start_date_str = start_date if isinstance(
        #     start_date, str) else start_date.strftime("%Y-%m-%d")
        # end_date_str = end_date if isinstance(
        #     end_date, str) else end_date.strftime("%Y-%m-%d")

        # # Add date filter to domain
        # if year and month:
        #     domain.append(('date', '>=', start_date_str))
        #     domain.append(('date', '<=', end_date_str))
        # if assign_team_id:
        #     domain.append(('assigned_team_id', '=', int(assign_team_id)))
        #     _logger.info('Filtered Orders: %s', domain)

        # orders = request.env['project.operation'].sudo().search(
        #     domain, order='date desc')
        # total_sales = sum(orders.mapped('monetary_value'))
        # kpi_domain = [
        #     ('employee_id', '=', employee_id.id),
        #     ('period_start', '<=', start_date_str),
        #     ('period_end', '>=', end_date_str)
        # ]
        # _logger.info('KPI Domain: %s', kpi_domain)
        # kpi_record = request.env['employee.kpi'].sudo().search(
        #     kpi_domain, limit=1)
        # _logger.info('KPI Record: %s', kpi_record)
        # # Set default values
        # minimum_target = employee_id.minimum_target
        # achieved_sales = 0.0
        # balance_amount = 0.0
        # bonus_amount = 0.0

        # # If KPI record found, get values
        # if kpi_record:
        #     # minimum_target = kpi_record.minimum_target
        #     achieved_sales = kpi_record.total_sales
        #     balance_amount = minimum_target - achieved_sales
        #     bonus_amount = kpi_record.bonus_amount
        #     _logger.info('KPI Values: %s, %s, %s, %s', minimum_target,
        #                  achieved_sales, balance_amount, bonus_amount)
        # if search_value:
        #     _logger.info('Search Value: %s', search_value)
        #     domain.append('|')
        #     domain.append('|')
        #     domain.append('|')
        #     domain.append(('employee_id.barcode', '=', search_value))
        #     domain.append(('employee_id.name', '=', search_value))
        #     domain.append(('assigned_team_id.name', '=', search_value))
        #     domain.append(('order_id', '=', search_value))

        #     orders = request.env['project.operation'].sudo().search(domain)
        #     if not orders:
        #         domain = ['|', '|', '|',
        #                   ('employee_id.barcode', 'ilike', search_value),
        #                   ('employee_id.name', 'ilike', search_value),
        #                   ('assigned_team_id.name', 'ilike', search_value),
        #                   ('order_id', 'ilike', search_value),
        #                   ]
        # _logger.info('Domain: %s', domain)
        # filtered_orders = orders.sudo().search(domain, order='date desc')
        # total_count = len(filtered_orders)
        
        # # total_pages = math.ceil(total_count / per_page)
        # # pager = portal_pager(
        # #     url="/operation_dashboard",
        # #     url_args={'search': search_value},
        # #     total=total_count,
        # #     page=page,
        # #     step=per_page,
        # #     scope=5,
        # # )

        # def format_currency(value, is_bonus=False):
        #     currency_symbol = request.env.company.currency_id.symbol if is_bonus else '$'
        #     return currency_symbol + ' ' + '{:,.2f}'.format(value)

        # # _logger.info('books_________________: %s', pager)
        # values = {
        #     'orders': filtered_orders,
        #     'res_company': request.env.company,
        #     # 'current_status': status,
        #     'search_value': search_value,
        #     # 'page': page,
        #     # 'pager': pager,
        #     # 'total_pages': total_pages,
        #     'minimum_target': format_currency(minimum_target),
        #     'achieved_sales': format_currency(achieved_sales),
        #     'balance_amount': format_currency(balance_amount),
        #     'bonus_amount': format_currency(bonus_amount, is_bonus=True),
        #     'minimum_target_raw': minimum_target,
        #     'achieved_sales_raw': achieved_sales,
        #     'balance_amount_raw': balance_amount,
        #     'bonus_amount_raw': bonus_amount,
        # }
        

    @http.route('/operation/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_operation_order(self, **kwargs):
        order_id = kwargs.get('order_id')
        if not order_id:
            return {'success': False, 'message': 'Missing order_id'}

        _logger.info('Order ID: %s', order_id)

        order = request.env['project.operation'].sudo().search(
            [('order_id', '=', order_id)])
        _logger.info('Order: %s', order)

        if not order.exists():
            return {'success': False, 'message': 'Order not found'}

        employee_id = int(kwargs.get('employee_id')) if kwargs.get(
            'employee_id') and kwargs.get('employee_id').isdigit() else False
        partner_id = int(kwargs.get('partner_id')) if kwargs.get(
            'partner_id') and kwargs.get('partner_id').isdigit() else False
        assigned_team_id = int(kwargs.get('team_id')) if kwargs.get(
            'team_id') and kwargs.get('team_id').isdigit() else False
        date = kwargs.get('date')
        percentage = kwargs.get('percentage') if kwargs.get(
            'percentage') else False
        monetary_value = float(kwargs.get('monetary_value', 0)) if kwargs.get(
            'monetary_value') else 0
        delivery_amount = float(kwargs.get('delivery_amount', 0)) if kwargs.get(
            'delivery_amount') else 0
        special_remarks = kwargs.get('special_remarks')
        order_status = kwargs.get('order_status')
        order_link = kwargs.get('order_link')
        instruction_sheet_link = kwargs.get('instruction_sheet_link')
        revision_count = int(kwargs.get('revision_count', 0)
                             ) if kwargs.get('revision_count') else 0
        _logger.info('Received Data: %s', kwargs)

        updates = {}
        if employee_id and order.employee_id.id != employee_id:
            updates['employee_id'] = employee_id
        if partner_id and order.partner_id.id != partner_id:
            updates['partner_id'] = partner_id
        if assigned_team_id and order.assigned_team_id.id != assigned_team_id:
            updates['assigned_team_id'] = assigned_team_id
        if date and order.date != date:
            updates['date'] = date
        if instruction_sheet_link and order.instruction_sheet_link != instruction_sheet_link:
            updates['instruction_sheet_link'] = instruction_sheet_link
        if order_link and order.order_link != order_link:
            updates['order_link'] = order_link
        if percentage and order.percentage != percentage:
            updates['percentage'] = percentage
        if monetary_value and order.monetary_value != monetary_value:
            updates['monetary_value'] = monetary_value
        if delivery_amount and order.delivery_amount != delivery_amount:
            updates['delivery_amount'] = delivery_amount
        if special_remarks and order.special_remarks != special_remarks:
            updates['special_remarks'] = special_remarks
        if order_status and order.order_status != order_status:
            updates['order_status'] = order_status

        _logger.info('Updates to Apply: %s', updates)

        if updates:
            try:
                order.write(updates)
                order.message_post(
                    body="Operation order updated by %s" % request.env.user.name)
                revision_count += 1
                order.write({'revision_count': revision_count})
                updated_order = request.env['project.operation'].sudo().browse(
                    order.id)

                _logger.info(
                    'Updated Order Data------------------------------1: %s', updated_order.read())
                return {'success': True, 'message': "Operation order updated successfully!"}
            except Exception as e:
                _logger.error(
                    "Error updating operation order --------------------------------2: %s", str(e))
                return {'success': False, 'message': f"Error updating order: {str(e)}"}
        else:
            _logger.info('No changes detected-------------------------3')
            return {'success': False, 'message': "No changes detected."}
        
        
        
    @http.route('/delete/operation/order', type='json',methods=['POST'], auth='user',csrf=False)
    def delete_operation_order(self, order_id):
        try:
            operation = request.env['project.operation'].sudo().search([('order_id', '=', order_id)], limit=1)
            if not operation:
                return { 'success': False, 'message': f'No operation found with order_id {order_id}' }

            operation.unlink()
            return { 'success': True, 'message': 'Operation deleted successfully.' }

        except Exception as e:
            return { 'success': False, 'message': str(e) }

