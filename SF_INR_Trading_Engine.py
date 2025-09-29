import sf_order_router #kk
import sf_get_prices #piyush
import sf_monitoring #vvk


def main(symbol, spot_exchange, futures_exchange, quantity_usd, take_profit):
    #will be called frontend go button, webhooks next phase
   #kk 
   # create pending order table once sf_opentrade is called
   # insert order details in pending order table 
   # No hedge if spread is >0.2%
   # check balance on both exchanges
   #spread = float(futures_price) - float(spot_price) 

    spot_price = get_prices.get_spot_price(symbol, spot_exchange) #piyush
    position_size = float(quantity_usd) / float(spot_price)
    # next phase brake in to smaller chunks

    if sf_order_router.open_trade(symbol,spot_exchange, futures_exchange, position_size,) == "success":
        #kk make db table on success contains futures_exchange_order_id, and all the details
        sf_monitoring.monitor_trade() #vvk
        #vvk first read db table to get details of completed orders
        #then monitor the each trade for take profit , telegram alert
        #vvk if take profit hit call kk order_router.close_trade()
    else:
        #send alert to user

    # tojo add refersh button or auto refersh to show order deails from db
    # add cancel button to trigger kk close_trade()
    # add pending order tab, get order status from db sf_pending orders table kk