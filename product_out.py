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
    order_line = fields.One2many('product.out.line', 'order_id', string='Matériels sortie')
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
 

class product_out_line(osv.osv):
    _name = "product.out.line"
    _description = 'Articles Sortie'
    
    name = fields.Text(string='Description')
    product_id = fields.Many2one('product.product', string="Article",required= True)
    marque = fields.Char('Marque', related ='product_id.product_brand_id.name', readonly=True)
    model = fields.Char('Modèle', related ='product_id.model', readonly=True)
    quantity = fields.Float(string="Quantité",required= True, default=1.0)
    qty_on_hand = fields.Float(string='Qté en stock', related='product_id.qty_available', readonly=True)
    product_uom_id = fields.Many2one('product.uom', string="Unité", store=True, related='product_id.uom_id')
    num_serie = fields.Char(string="Numéro de série", store=True, readonly=True, related='product_id.num_serie')
    location_id = fields.Many2one('stock.location', domain=[('usage','=','internal')], string='Source', required=True)
    destination_location_id = fields.Many2one('stock.location', string="Destination Location",required= True)
    order_id = fields.Many2one('product.out', string="N° Bon", ondelete='cascade', index=True)
    partner_id = fields.Many2one('res.partner' ,string='Client', related='order_id.partner_id', store=True)
    price_unit = fields.Float(string='Unit Price', required=True, digits=dp.get_precision('Product Price'))
    date_order = fields.Date(string='Remis le', required=True, readonly=True, index=True, states={'draft': [('readonly', False)]}, copy=False, default=fields.Datetime.now)

    @api.multi
    def button_approve(self):
        self.write({'state': 'draft'})
        self._create_picking()
        return {}


    @api.multi
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'waiting']:
                continue
            else:
                order.write({'state': 'confirmed'})
        return {}


    @api.multi
    def _create_picking(self):
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.order_line.mapped('product_id.type')]):
                res = order._prepare_picking()
                picking = self.env['stock.picking'].create(res)
                moves = order.order_line.filtered(lambda r: r.product_id.type in ['product', 'consu'])._create_stock_moves(picking)
                move_ids = moves.action_confirm()
                moves = self.env['stock.move'].browse(move_ids)
                seq = 0
                for move in sorted(moves, key=lambda move: move.date_expected):
                    seq += 5
                    move.sequence = seq
                moves.force_assign()
        return True

    @api.multi
    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:

            template = {
                'name': line.name or '',
                'product_id': line.product_id.id,
                'date': line.date_order,
                'destination_location_id': line.destination_location_id,
                'location_id': line.location_id,
                'partner_id': line.partner_id,
                'num_serie': line.num_serie,
                'model': line.model,
                'marque': line.marque,
                'quantity': line.quantity,
                'qty_on_hand': line.qty_on_hand,
                'product_uom_id': line.product_uom_id,
                'price_unit': line.price_unit,
                'partner_id': line.partner_id,
            }

        return done