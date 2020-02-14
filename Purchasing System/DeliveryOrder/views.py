from django.shortcuts import render

from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from django import forms
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponseRedirect
from django.template import RequestContext
from django.db import models
from datetime import datetime
from app.models import Person,Item,Vendor
from PurchaseOrder.models import PurchaseOrder,PurchaseOrderItem
from DeliveryOrder.models import DeliveryOrder,DeliveryOrderItem
from django.views.generic import TemplateView
from django.core.exceptions import ObjectDoesNotExist
from django.forms import formset_factory
from django.http.request import QueryDict
from decimal import Decimal
import random
import datetime 


@login_required
def deliveryorderform(request):
    context = {
            'title':'Delivery Order Form',
            'year':'2019/2020'
        }
    context['user'] = request.user

    return render(request,'DeliveryOrder/deliveryorderform.html',context)


@login_required
def fillingdeliveryorder(request):

    context = {}
    pur_id = request.GET['pur_id']
    do_id = random.randint(10000000,99999999)
    user_id = request.user.id
    staff = Person.objects.get(user_id = user_id)

    try: 
        po = PurchaseOrder.objects.get(purchase_order_id = pur_id)
        item_list = PurchaseOrderItem.objects.filter(purchase_order_id = pur_id)

        listOfItem = list()

        for perItem in item_list:
            quantityCheckRequired = False
            itemComplete = False
            tempTotalQuantity = 0
            tempOriginalItempQuantity = 0

            for eachItem in DeliveryOrderItem.objects.filter(purchase_order_id = po.purchase_order_id).filter(item_id = perItem.item_id):
                tempTotalQuantity = tempTotalQuantity+eachItem.quantity
                tempOriginalItempQuantity = PurchaseOrderItem.objects.filter(purchase_order_id = po.purchase_order_id).get(item_id = perItem.item_id).quantity

                if tempTotalQuantity+perItem.quantity>tempOriginalItempQuantity or tempTotalQuantity+perItem.quantity<=0:
                    perItem.quantity = tempOriginalItempQuantity-tempTotalQuantity
                    quantityCheckRequired = True
                if tempTotalQuantity==tempOriginalItempQuantity:
                    itemComplete = True
            if itemComplete is False:
                total= perItem.quantity * perItem.unit_price
                item_table = {
                    'item_name': perItem.item_id.item_name,
                    'item_id': perItem.item_id,
                    'quantity' : perItem.quantity,
                    'unit_price': perItem.unit_price,
                    'total_price': total
                }
                listOfItem.append(item_table)
        if len(listOfItem) <= 0:
            context = {
                'error': 'Delivery Order Completed for '+pur_id,
                'title': 'Delivery Order Form',
                'delivery_order_id': 'DO' + str(do_id),
                'purchase_order_id': pur_id, 
                'staff_id' : staff.person_id,
                'vendor_id': po.vendor_id.vendor_id,
            }
            return render(request,'DeliveryOrder/deliveryorderform.html',context)
        else:
            context = {
                'title': 'Delivery Order Form',
                'delivery_order_id': 'DO' + str(do_id),
                'purchase_order_id': pur_id, 
                'staff_id' : staff.person_id,
                'vendor_id': po.vendor_id.vendor_id,
                'rows':listOfItem
            }
            return render(request,'DeliveryOrder/deliveryorderform.html',context)

    except PurchaseOrder.DoesNotExist:

        context = { 'error': 'The Purchase Order ID: '+pur_id+' is invalid !',
                    'title': 'Delivery Order Form'
            }
        return render(request,'DeliveryOrder/deliveryorderform.html',context)

def deliveryorderconfirmation(request):

    context = {}
    do_id = request.POST['delivery_order_id']
    po_id = request.POST['purchase_order_id']
    vendor_id = request.POST['vendor_id']
    shipping_inst = request.POST['shipping_inst']
    description = request.POST['description']
    

    user_id = request.user.id
    staff = Person.objects.get(user_id=user_id)
    try:
        vendor_info = Vendor.objects.get(vendor_id = vendor_id)
    except Vendor.DoesNotExist:
        context = {
            'error': 'Vendor ID: '+vendor_id+' is invalid',
            'title': 'Delivery Order Form',
            'delivery_order_id': do_id,
            'purchase_order_id': po_id, 
            'staff_id' : staff.person_id,
            'vendor_id': vendor_id,
        }
        return render(request,'DeliveryOrder/deliveryorderform.html',context)

    doCount = DeliveryOrder.objects.filter(delivery_order_id = do_id)
    if doCount.count() == 0:

        try:
            po = PurchaseOrder.objects.get(purchase_order_id = po_id)
            
            responses = request.read()
            #print(responses)
            q= QueryDict(responses)
            items_id = q.getlist('item_id')
            #print(items_id)
            items_name = q.getlist('item_name')
            #print(items_name)
            items_quantity = q.getlist('quantity')
            #print(items_quantity)
            items_unit_price = q.getlist('unit_price')
            #print(items_unit_price)
            items_total_price = q.getlist('total_price')
            #print(items_total_price)
 
            items = list()
            itemCheckList = list()
            i = 0
            items_length = len(items_id)
            grand_total = Decimal(0)

            while i < items_length:
                itemComplete = False
                quantityCheckRequired = False

                tempTotalQuantity = 0
                tempOriginalItempQuantity = 0

                try:
                    tempOriginalItempQuantity = PurchaseOrderItem.objects.filter(purchase_order_id = po.purchase_order_id).get(item_id = items_id[i]).quantity
                except PurchaseOrderItem.DoesNotExist:
                    context = {
                        'error': 'Error in finding Item: '+items_id[i]+' for PO: '+po.purchase_order_id+'. Try Again',
                        'title': 'Delivery Order Form',
                        'delivery_order_id': do_id,
                        'purchase_order_id': po_id, 
                        'staff_id' : staff.person_id,
                        'vendor_id': vendor_id,
                    }
                    return render(request,'DeliveryOrder/deliveryorderform.html',context)

                for eachItem in DeliveryOrderItem.objects.filter(purchase_order_id = po.purchase_order_id).filter(item_id = items_id[i]):

                    tempTotalQuantity = tempTotalQuantity+eachItem.quantity
                    
                    if tempTotalQuantity+Decimal(items_quantity[i])>tempOriginalItempQuantity or tempTotalQuantity+Decimal(items_quantity[i])<=0:
                        items_quantity[i] = tempOriginalItempQuantity-tempTotalQuantity
                        quantityCheckRequired = True
                    if tempTotalQuantity==tempOriginalItempQuantity:
                        itemComplete = True


                if quantityCheckRequired is True or Decimal(items_quantity[i])<=0 or Decimal(items_quantity[i])>PurchaseOrderItem.objects.filter(purchase_order_id = po.purchase_order_id).get(item_id = items_id[i]).quantity:
                    itemCheckList.append(items_id[i])

                if itemComplete is False:
                    total= Decimal(items_quantity[i]) * Decimal(items_unit_price[i])
                    item_table = {
                        'item_name': items_name[i],
                        'item_id': items_id[i],
                        'quantity' : items_quantity[i],
                        'unit_price': items_unit_price[i],
                        'total_price': total
                    }
                    items.append(item_table)
                    grand_total = grand_total + total

                i = i + 1
            #print(items)

            if items_length <=0:

                item_list = PurchaseOrderItem.objects.filter(purchase_order_id = po_id)

                listOfItem = list()

                for perItem in item_list:
                    quantityCheckRequired = False
                    itemComplete = False
                    tempTotalQuantity = 0
                    tempOriginalItempQuantity = 0

                    for eachItem in DeliveryOrderItem.objects.filter(purchase_order_id = po.purchase_order_id).filter(item_id = perItem.item_id):
                        tempTotalQuantity = tempTotalQuantity+eachItem.quantity
                        tempOriginalItempQuantity = PurchaseOrderItem.objects.filter(purchase_order_id = po.purchase_order_id).get(item_id = perItem.item_id).quantity

                        if tempTotalQuantity+perItem.quantity>tempOriginalItempQuantity or tempTotalQuantity+perItem.quantity<=0:
                            perItem.quantity = tempOriginalItempQuantity-tempTotalQuantity
                            quantityCheckRequired = True
                        if tempTotalQuantity==tempOriginalItempQuantity:
                            itemComplete = True
                    if itemComplete is False:
                        total= perItem.quantity * perItem.unit_price
                        item_table = {
                            'item_name': perItem.item_id.item_name,
                            'item_id': perItem.item_id,
                            'quantity' : perItem.quantity,
                            'unit_price': perItem.unit_price,
                            'total_price': total
                        }
                        listOfItem.append(item_table)

                if len(listOfItem) <= 0:
                    context = {
                        'error': 'Delivery Order Completed for '+po_id,
                        'title': 'Delivery Order Form',
                        'delivery_order_id': do_id,
                        'purchase_order_id': po_id, 
                        'staff_id' : staff.person_id,
                        'vendor_id': vendor_id,
                    }
                    return render(request,'DeliveryOrder/deliveryorderform.html',context)
                else:
                    context = {
                        'title': 'Delivery Order Form',
                        'delivery_order_id': do_id,
                        'purchase_order_id': po_id, 
                        'staff_id' : staff.person_id,
                        'vendor_id': vendor_id,
                        'rows':listOfItem,
                    }
                    return render(request,'DeliveryOrder/deliveryorderform.html',context)
                
            else:
                if len(items)<items_length:

                    if len(items)<=0:
                            context = {
                                'error': 'All Items are already delivered for Purchase Order: '+po_id,
                                'title': 'Delivery Order Form',
                                'delivery_order_id': do_id,
                                'purchase_order_id': po_id, 
                                'staff_id' : staff.person_id,
                                'vendor_id': vendor_id,
                                'rows':items
                            }
                            return render(request,'DeliveryOrder/deliveryorderform.html',context)
                    else:
                        if len(itemCheckList)>0:
                            context = {
                                'error': 'Quantity for '+",".join(itemCheckList)+' cannot be higher then the purchase order\'s item quantity or less then 0 ',
                                'title': 'Delivery Order Form',
                                'delivery_order_id': do_id,
                                'purchase_order_id': po_id, 
                                'staff_id' : staff.person_id,
                                'vendor_id': vendor_id,
                                'rows':items
                            }

                            return render(request,'DeliveryOrder/deliveryorderform.html',context)
                        
                else:
                    print(itemCheckList)

                    if len(itemCheckList)>0:
                        context = {
                            'error': 'Quantity for '+",".join(itemCheckList)+' cannot be higher then the purchase order\'s item quantity  or less then 0',
                            'title': 'Delivery Order Form',
                            'delivery_order_id': do_id,
                            'purchase_order_id': po_id, 
                            'staff_id' : staff.person_id,
                            'vendor_id': vendor_id,
                            'rows':items
                        }

                        return render(request,'DeliveryOrder/deliveryorderform.html',context)
                    else:
                        context = {
                                'title': 'Delivery Order Confirmation',
                                'purchase_order_id' : po_id,
                                'delivery_order_id' : do_id,
                                'staff_id' : staff.person_id,
                                'vendor_id' : vendor_id,
                                'shipping_inst' : shipping_inst,
                                'grand_total': grand_total,
                                'rows' : items,
                                'staff_info' : staff,
                                'vendor_info' : vendor_info,
                                'description' : description,
                                'year':'2019/2020'
                            }

                        return render(request,'DeliveryOrder/deliveryorderconfirmation.html',context)

        except PurchaseOrder.DoesNotExist:
            context = { 
                'error': 'The Purchase Order ID '+po_id+' is invalid !',
                        'title': 'Delivery Order Form',
                        'delivery_order_id': do_id,
                        'purchase_order_id': po_id, 
                        'staff_id' : staff.person_id,
                        'vendor_id': vendor_id,
                }
            return render(request,'DeliveryOrder/deliveryorderform.html',context)
        
    else:
        context = {
                'error': 'The Delivery Order ID '+do_id+' already exist!',
                'title': 'Delivery Order Form',
                'delivery_order_id': do_id,
                'purchase_order_id': po_id, 
                'staff_id' : staff.person_id,
                'vendor_id': vendor_id,
            }

        return render(request,'DeliveryOrder/deliveryorderform.html',context)
        

 
def deliveryorderdetails(request):
    context = {}
    do_id = request.POST['delivery_order_id']
    po_id = request.POST['purchase_order_id']
    shipping_inst = request.POST['shipping_inst']
    staff_id = request.POST['staff_id']
    vendor_id = request.POST['vendor_id']
    description = request.POST['description']
    po = PurchaseOrder.objects.get(purchase_order_id = po_id)
    staff_info = Person.objects.get(person_id = staff_id)
    vendor_info = Vendor.objects.get(vendor_id = vendor_id)

    responses = request.read()
    print(responses)
   
    q= QueryDict(responses)
    
    items_id = q.getlist('item_id')
    print(items_id)
    items_name = q.getlist('item_name')
    print(items_name)
    items_quantity = q.getlist('quantity')
    print(items_quantity)
    items_unit_price = q.getlist('unit_price')
    print(items_unit_price)
    items_total_price = q.getlist('total_price')
    print(items_total_price)


    items = list()

    i = 0
    items_length = len(items_id)
    grand_total = Decimal(0)

    while i < items_length:
        total= Decimal(items_quantity[i]) * Decimal(items_unit_price[i])
        item_table = {
            'item_name': items_name[i],
            'item_id': items_id[i],
            'quantity' : items_quantity[i],
            'unit_price': items_unit_price[i],
            'total_price': total
        }
        items.append(item_table)
        i = i + 1
        grand_total = grand_total + total
    print(items)

 
    try:
        # push the data to the database 
        current_time = datetime.datetime.now() 
        print(current_time)
        do_info = DeliveryOrder(delivery_order_id = do_id,
                                shipping_instructions = shipping_inst, 
                                time_created = current_time,
                                total_price = grand_total, 
                                person_id = staff_info,
                                description = description,
                                vendor_id = vendor_info, 
                                purchase_order_id = po)
        do_info.save()

        delivery_order = DeliveryOrder.objects.get(delivery_order_id = do_id)
        for item in items:
            item_info = Item.objects.get(item_id = item['item_id'])
            do_item_info = DeliveryOrderItem(delivery_order_id = delivery_order, 
                                             purchase_order_id = po,
                                             item_id = item_info, 
                                             quantity = item['quantity'], 
                                             unit_price = item['unit_price'],
                                             total_price = item['total_price'])
            do_item_info.save()

        # info pass to html
        context = {
                'title': 'Delivery Order Details',
                'purchase_order_id' : po_id,
                'delivery_order_id' : do_id,
                'staff_id' : staff_id,
                'vendor_id' : vendor_id,
                'shipping_inst' : shipping_inst,
                'rows' : items,
                'staff_info' : staff_info,
                'vendor_info' : vendor_info,
                'grand_total': grand_total,
                'time_created': current_time,
                'description' : description
            }

        return render(request,'DeliveryOrder/deliveryorderdetails.html',context)
    except IntegrityError:
        return render(request,'DeliveryOrder/deliveryorderdetails.html',context)


def deliveryorderhistorydetails(request):

    print(request.body)
    pk = request.GET['do_id']
    delivery_order = DeliveryOrder.objects.get(delivery_order_id = pk)
    items = DeliveryOrderItem.objects.filter(delivery_order_id = pk)

    print(delivery_order.person_id)
    context = {

            'title': 'Delivery Order Details',
            'purchase_order_id' : delivery_order.purchase_order_id.purchase_order_id,
            'delivery_order_id' : pk,
            'staff_id' : delivery_order.person_id.person_id,
            'vendor_id' : delivery_order.vendor_id.vendor_id,
            'shipping_inst' : delivery_order.shipping_instructions,
            'rows' : items,
            'staff_info' : delivery_order.person_id,
            'vendor_info' : delivery_order.vendor_id,
            'grand_total': delivery_order.total_price,
            'time_created': delivery_order.time_created,
            'description' : delivery_order.description,
            'year':'2019/2020'
        }
  
    return render(request,'DeliveryOrder/deliveryorderhistorydetails.html',context)

def deliveryorderhistory(request):

    delivery_orders = DeliveryOrder.objects.all()

    context = {
            'title':'delivery Order History',
            'rows':delivery_orders,
            'year':'2019/2020'
        }
    return render(request,'DeliveryOrder/deliveryorderhistory.html',context)