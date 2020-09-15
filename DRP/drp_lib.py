# -*- coding: utf-8 -*-
"""
Created on Mon Sep  7 18:13:24 2020

@author: James Ang
"""

import pandas as pd
import math

class Demand_Centre():
    
    # CLASS ATTRIBUTES
    
    # INSTANCE ATTRIBUTES
    def __init__(self, excelfile, sheet_name):
        
        self.excelfile = excelfile
        self.sheet_name = sheet_name
        self.table = pd.read_excel(self.excelfile, sheet_name=self.sheet_name, skiprows = 11, usecols = 'B:L')
        self.table.index = self.table['Category']
        self.table.drop('Category', axis=1, inplace=True)
        self.table = self.table.transpose().fillna(0)
        self.total_demand = self.table['Spot Forecast Demand(MT)'] +\
                    self.table['Spot Order (MT)'] +\
                    self.table['Term Forecast Demand (MT)'] +\
                    self.table['Term Order (MT)']
        self.product_selling_price = self.table['Product Selling Price (RM/MT)']
        self.spot_forecast_demand = self.table['Spot Forecast Demand(MT)']
        self.spot_order = self.table['Spot Order (MT)']
        self.proj_end_inv = pd.Series(data=[0]*len(self.table), index = self.table.index)
        self.planned_receipts = pd.Series(data=[0]*len(self.table), index = self.table.index)
        self.net_requirements = pd.Series(data=[0]*len(self.table), index = self.table.index)
        self.planned_orders = pd.Series(data=[0]*len(self.table), index = self.table.index)
        self.truck_count_10T = pd.Series(data=[0]*len(self.table), index = self.table.index)
        self.truck_count_20T = pd.Series(data=[0]*len(self.table), index = self.table.index)
        self.total_shipment_cost = pd.Series(data=[0]*len(self.table), index = self.table.index)
        self.product_unit_cost = self.table['Product Unit Cost (RM/MT)']
        self.product_cost = pd.Series(data=[0]*len(self.table), index = self.table.index)
        self.totalsupply_cost = pd.Series(data=[0]*len(self.table), index = self.table.index)
        self.revenue = pd.Series(data=[0]*len(self.table), index = self.table.index)
        self.profit = pd.Series(data=[0]*len(self.table), index = self.table.index)
        self.spot_demand = pd.Series(data=[0]*len(self.table), index = self.table.index)
        self.first_week = self.table.index[0]
        
    def calculate(self, dc_params): 
        
        # NEED TO INCLUDE SELECTION (SUPP1 or SUPP2) LATER
        supplier_leadtime = dc_params.leadtime_sup1
        ship10T_val = dc_params.ship_value10T_sup1
        ship20T_val = dc_params.ship_value20T_sup1
        ship10T_cost = dc_params.ship_cost10T_sup1
        ship20T_cost = dc_params.ship_cost20T_sup1
        
        self.proj_end_inv[0] = dc_params.init_end_inv +\
                            self.table['Scheduled Receipts (MT)'][0] +\
                            self.planned_receipts[0] -\
                            self.total_demand[0]
        
        for i in range(1, len(self.table)):
    
            # Net Requirements
            if self.proj_end_inv[i-1] - self.total_demand[i] <= dc_params.safety_stock:
                self.net_requirements[i] = self.total_demand[i] - self.proj_end_inv[i-1] + dc_params.safety_stock
            else:
                self.net_requirements[i] = 0 
            
            # Planned Receipts
            if i >= supplier_leadtime:
                self.planned_receipts[i] = math.ceil(self.net_requirements[i]/dc_params.lotsize)*dc_params.lotsize
            
            # Projected Ending Inventory
            self.proj_end_inv[i] = self.proj_end_inv[i-1] + self.table['Scheduled Receipts (MT)'][i] + self.planned_receipts[i] - self.total_demand[i]

        for i in range(0, len(self.table)-int(supplier_leadtime)):
            
            # Planned Orders
            self.planned_orders[i] = self.planned_receipts[i + int(supplier_leadtime)]        

            # Adding truck count
            self.truck_count_10T[i] = ((self.planned_orders[i] + ship10T_val - 1)%ship20T_val)//ship10T_val
            self.truck_count_20T[i] = (self.planned_orders[i] + ship10T_val - 1)//ship20T_val
            
            # Total Transportation Cost
            self.total_shipment_cost[i] = self.truck_count_10T[i]*ship10T_cost + self.truck_count_20T[i]*ship20T_cost
            
            # Product Cost
            self.product_cost[i] = self.product_unit_cost[i]*self.planned_orders[i]
            
            # Total Supply Cost
            self.totalsupply_cost[i] = self.total_shipment_cost[i] + self.product_cost[i]
            
            # Revenue
            self.revenue[i] = self.product_selling_price[i]*self.planned_orders[i]
            
            # Profit
            self.profit[i] = self.revenue[i] - self.totalsupply_cost[i]
            
            # Spot Demand
            self.spot_demand[i] = self.spot_forecast_demand[i + int(supplier_leadtime)] + self.spot_order[i + int(supplier_leadtime)]
        
        return self.proj_end_inv, self.planned_receipts, self.net_requirements


class Demand_Centre_Params():
    
    # INSTANCE ATTRIBUTES
    def __init__(self, excelfile, sheet_name): 
        self.excelfile = excelfile
        self.sheet_name = sheet_name
        self.table = pd.read_excel(self.excelfile, sheet_name = self.sheet_name, skiprows = 1, nrows = 9, usecols = 'B:D')
        self.table.index = self.table['Category']
        self.table.drop('Category', axis=1, inplace=True)
        self.table = self.table.transpose().fillna(0)
        self.init_end_inv = self.table.loc['Value','Initial Ending Inventory (MT)']
        self.safety_stock = self.table.loc['Value','Safety Stock (MT)']
        self.leadtime_sup1 = self.table.loc['Value','Lead Time (weeks) - sup 1']
        self.leadtime_sup2 = self.table.loc['Value','Lead Time (weeks) - sup 2']
        self.lotsize = self.table.loc['Value','Lot Size (MT)']
        self.ship_value10T_sup1 = self.table.loc['Value','Shipment cost (10 Ton) - sup 1']
        self.ship_value20T_sup1 = self.table.loc['Value','Shipment cost (20 Ton) - sup 1']
        self.ship_value10T_sup2 = self.table.loc['Value','Shipment cost (10 Ton) - sup 2']
        self.ship_value20T_sup2 = self.table.loc['Value','Shipment cost (20 Ton) - sup 2']        
        self.ship_cost10T_sup1 = self.table.loc['Price','Shipment cost (10 Ton) - sup 1']
        self.ship_cost20T_sup1 = self.table.loc['Price','Shipment cost (20 Ton) - sup 1']
        self.ship_cost10T_sup2 = self.table.loc['Price','Shipment cost (10 Ton) - sup 2']
        self.ship_cost20T_sup2 = self.table.loc['Price','Shipment cost (20 Ton) - sup 2']
    


