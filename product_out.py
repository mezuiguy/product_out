# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from openerp import SUPERUSER_ID
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import UserError
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.osv import osv

class BonSortie(osv.osv):
    _name = "product.out"
    _description = "Bon Sortie"
    _order = 'name desc, date desc, id desc'
    # _inherits = {'stock.picking': 'stock_picking_id'}
    _inherit ='stock.picking'
    
    
    # stock_picking_id = fields.Many2one('stock.picking', string="Picking/Stock", ondelete="cascade", required=True, auto_join=True)
    type_mvmt = fields.Selection([('interne','Interne'),('externe','Externe')], string="Type Mouvement", default='externe')
    type_livreur = fields.Selection([('interne','Interne'),('externe','Externe')], string="Type transporteur", default='interne')
    livreur_externe = fields.Many2one('res.partner', string='Transporteur Ext')
    livreur_interne = fields.Many2one('hr.employee', string='Transporteur Int')
    recepteur_interne = fields.Many2one('hr.employee', string='Reçu Par')
    user_id = fields.Many2one('res.users', string='Délivré par', track_visibility='onchange', default=lambda self: self.env.user)

    company_id = fields.Many2one('res.company', default=lambda self: self.env['res.company']._company_default_get('bon.sortie')) 
    remarks = fields.Text(string="Observation")
  
   
    
    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('product.out') or '/'
        return super(BonSortie, self).create(vals)
        
   
    @api.multi
    def unlink(self):
        for order in self:
            if order.state != 'draft':
                raise UserError(_('Vous ne pouvez pas supprimer le bon de sortie!'))
        return super(BonSortie, self).unlink()  
 
 

