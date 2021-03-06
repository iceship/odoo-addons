# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv
from osv import fields
from tools.translate import _

class sale_order_line(osv.osv):
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'
    
    def check_discount_constrains(self, cr, uid, line_id, vals, context=None):
        order_obj = self.pool.get('sale.order')
        line_obj = self.pool.get('sale.order.line')
        pricelist_obj = self.pool.get('product.pricelist')
        
        line = False
        if line_id:
            line = line_obj.browse(cr, uid, line_id, context=context)
            if isinstance(line, list):
                line = line[0]
        
        discount = vals.get('discount', False)
        pricelist = self.get_order_pricelist(cr, uid, line_id, vals, context=context)
        
        order_id = vals.get('order_id', False)
        order = False
        if order_id:
            order = order_obj.browse(cr, uid, order_id, context=context)
            if isinstance(order, list):
                order = order[0]
        else:
            order = line.order_id
        
        if discount:
            if pricelist.visible_discount:
                product_uom = vals.get('product_uom', False)
                if not product_uom:
                    product_uom = line.product_uom.id
                
                product_uom_qty = vals.get('product_uom_qty', False)
                if not product_uom_qty:
                    product_uom_qty = line.product_uom_qty
                
                product_id = vals.get('product_id', False)
                if not product_id:
                    if not line.product_id:
                        return
                    product_id = line.product_id.id
                
                list_price = pricelist_obj.price_get(cr, uid, [pricelist.id], product_id, product_uom_qty or 1.0,
                                                     order.id, {'uom': product_uom, 'date': order.date_order })
                
                real_price = self.get_real_price(cr, uid, list_price, product_id, product_uom_qty, product_uom,
                                                     pricelist, context=context)
                
                
                item_pair_id = list_price['item_id']
                item_id = item_pair_id.keys()[0]
                computed_price = list_price[item_id]
                
                # Modified by Juan because it seams not to work this way
                # if real_price != 0 and not real_price:
                if real_price != 0:
                    factor = ((real_price - computed_price) / real_price)
                else:
                    factor = 0
                list_discount = factor * 100
                discount -= list_discount
            
            restriction_obj = self.pool.get('price_security.discount_restriction')
            restriction_obj.check_discount_with_restriction(cr, uid, discount, pricelist.id, context=context)
            
    
    
    def get_real_price(self, cr, uid, res_dict, product_id, qty, uom, pricelist, context=None):
        item_obj = self.pool.get('product.pricelist.item')
        price_type_obj = self.pool.get('product.price.type')
        product_obj = self.pool.get('product.product')
        template_obj = self.pool.get('product.template')
        field_name = 'list_price'

        if res_dict.get('item_id',False) and res_dict['item_id'].get(pricelist,False):
            item = res_dict['item_id'].get(pricelist,False)
            item_base = item_obj.read(cr, uid, [item], ['base'])[0]['base']
            if item_base > 0:
                field_name = price_type_obj.browse(cr, uid, item_base).field

        product = product_obj.browse(cr, uid, product_id, context)
        product_tmpl_id = product.product_tmpl_id.id

        product_read = template_obj.read(cr, uid, product_tmpl_id, [field_name], context)

        factor = 1.0
        if uom and uom != product.uom_id.id:
            product_uom_obj = self.pool.get('product.uom')
            uom_data = product_uom_obj.browse(cr, uid,  product.uom_id.id)
            factor = uom_data.factor
        return product_read[field_name] * factor
    
sale_order_line()







