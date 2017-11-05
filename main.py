'''
Created on Aug 14, 2013

@author: spirotot
'''

import PyCryptsy
import sqlite3
from multiprocessing import Process, Queue, Lock
import time, sys

#conn = sqlite3.connect("cryptsy_trades.db")

key = ""
secret = ""
watching_markets = ["cgb_btc", "ftc_btc", "lky_btc", "mec_btc", "mnc_btc", "pxc_btc", "wdc_btc"]
def worker(q, l):
    crypt = PyCryptsy.PyCryptsy(key,secret)
    conn = sqlite3.connect("cryptsy_trades.db")
    
    while True:
        market_tuple = q.get()

        count = 0
        if market_tuple is None:
            conn.commit()
            conn.close()
            break
        
        cursor = conn.cursor()
        table_name = market_tuple[0]
        #Create the table if it doesn't exist...
        cursor.execute('''CREATE TABLE IF NOT EXISTS"''' + table_name + '''" (
                        "tradeid" INTEGER PRIMARY KEY NOT NULL,
                        "datetime" TEXT,
                        "tradeprice" REAL,
                        "quantity" REAL,
                        "total" REAL,
                        "initiate_ordertype" TEXT)'''
                       )
        
        mktid = market_tuple[1]
        if (table_name in watching_markets) or (1==1):
            #l.acquire()
            #print str(time.asctime()) + ": Adding trades for " + table_name + "..."
            #l.release()
            for trade in crypt.GetMarketTrades(mktid):
                trade = (trade['tradeid'], trade['datetime'], trade['tradeprice'], trade['quantity'], trade['total'], trade['initiate_ordertype']) 
                #cursor.execute("INSERT OR IGNORE INTO " + table_name + " VALUES(?,?,?,?,?,?)", trade)
                try:
                    cursor.execute("INSERT INTO " + table_name + " VALUES(?,?,?,?,?,?)", trade)
                    count = count + 1
                except:
                    if "IntegrityError" not in str(sys.exc_info()):
                        l.acquire()
                        print str(sys.exc_info())
                        l.release()
            
            if count > 0:       
                l.acquire()
                print str(time.asctime()) + ": Added " + str(count) + " trades for " + table_name + "!"
                l.release()
        
        conn.commit()    
        cursor.close()

def main():
    q = Queue()
    l = Lock()
    crypt = PyCryptsy.PyCryptsy(key, secret)
    #Start 4 workers to take care of downloading and storing the trades...
    processes = []
    i = 0
    while i < 4:
        print "Starting process: " + str(i)
        p = Process(target=worker, args=(q,l))
        p.daemon = True
        #q.put(None) #Put a None for this process, so it'll exit.
        p.start()
        processes.append(p)
        print "Started process: " + str(i)
        i = i + 1
        
    while True:
        #Get all the markets, and add them to a queue.
        #l.acquire()
        #print str(time.asctime()) + ": Refreshing markets..."
        #l.release()
        for item in crypt.GetMarkets():
            market_tuple = [str(str(item["primary_currency_code"]).lower() + "_" + str(item["secondary_currency_code"]).lower()), item["marketid"]]
            #print "Got market tuple" + str(market_tuple)
            q.put(market_tuple)
            
        time.sleep(10 * 60)
            

if __name__ == '__main__':
    main()
