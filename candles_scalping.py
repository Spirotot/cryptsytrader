'''
Created on Aug 18, 2013

@author: spirotot
'''
import sqlite3
from datetime import datetime, timedelta
import PyCryptsy
import time
import smtplib
import sys
from optparse import OptionParser
from multiprocessing import Process, Lock, cpu_count, Queue

class Mailer():
    def __init__(self, fromaddr='spirotot@gmail.com', toaddr='spirotot@gmail.com', username='spirotot', password='', table=""):
        self.fromaddr = fromaddr
        self.toaddr = toaddr
        self.username = username
        self.password = password
        self.table = table
        self.send("Starting table: " + self.table)

    def send(self, message=""):
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(self.username,self.password)
        headers = ["from: " + self.fromaddr,
                   "subject: " + "ALERT: " + self.table,
                   "to: " + self.toaddr,
                   "mime-version: 1.0",
                   "content-type: text/html"]
        headers = "\r\n".join(headers)
        
        server.sendmail(self.fromaddr, self.toaddr, headers + '\r\n\r\n' +  message)
        server.quit()
        
class BacktestPortfolio():
    def __init__(self, BTC=0.05, alt=0, buyFee=0.2, sellFee=0.3):
        self.BTC = BTC
        self.init_BTC = BTC
        self.alt = alt
        self.init_alt = alt
        self.buyFee = 1.0 - (buyFee / 100.0)
        self.sellFee = 1.0 - (sellFee / 100.0)
        self.num_trades = 0
        self.init_buy = True
        self.init_price = 0
        
    def buy(self, price=None, buy_and_hold=False):
        if buy_and_hold is True:
            print "INIT BTC: " + str(self.init_BTC)
            self.BTC = self.init_BTC
            
        if self.BTC > 0.0:
            self.alt = (self.BTC * self.buyFee) / price
            self.BTC = 0.0
            self.num_trades += 1
            if self.init_buy is True and buy_and_hold is not True:
                print "Price: " + str(price)
                self.init_price = price
                self.initial_buy = False
        
    def sell(self, price):
        if self.alt > 0.0:
            self.BTC = (self.alt * price) * self.buyFee
            self.alt = 0.0
            self.num_trades += 1
        
    def print_final(self, price):
        print "Final EMA portfolio..."
        if self.BTC > 0.0:
            print "BTC: " + str(self.BTC) + " ",
        else:
            print "You have " + str(self.alt) + " altcoins."
            self.sell(price)
            print "You could sell them for " + str(self.BTC) + " BTC",
        change = 0
        if self.BTC == self.init_BTC:
            print "(0.0% gains)."
        if self.BTC < self.init_BTC:
            print "(" + str(100 - ((self.BTC / self.init_BTC) * 100.0)) + "% loss.)"
            change = (100 - ((self.BTC / self.init_BTC) * 100.0))
        if self.BTC > self.init_BTC:
            print "(" + str(((self.BTC / self.init_BTC) * 100)-100) + "% gain.)"
            change = self.BTC / self.init_BTC
        print "Trades: " + str(self.num_trades)
        ema_btc = self.BTC
        ema_change = change
        #Buy and hold.
        if self.init_price != 0:
            self.buy(price=self.init_price, buy_and_hold=True)
            self.sell(price)
            print "Final Buy & Hold portfolio..."
            if self.BTC > 0.0:
                print "BTC: " + str(self.BTC) + " ",
            else:
                print "You have " + str(self.alt) + " altcoins."
                self.sell(price)
                print "You could sell them for " + str(self.BTC) + " BTC",
            change = 0
            if self.BTC == self.init_BTC:
                print "(0.0% gains)."
            if self.BTC < self.init_BTC:
                print "(" + str(100 - ((self.BTC / self.init_BTC) * 100.0)) + "% loss.)"
                change = (100 - ((self.BTC / self.init_BTC) * 100.0))
            if self.BTC > self.init_BTC:
                print "(" + str(((self.BTC / self.init_BTC) * 100)-100) + "% gain.)"
                change = self.BTC / self.init_BTC
            
            bh_btc = self.BTC
            bh_change = change
            return ema_btc, ema_change, bh_btc, bh_change
        else:
            print "No trades, so no final Buy & Hold portfolio."
    
class CryptsyPortfolio():
    def __init__(self, key = "", secret = "", buyFee=0.2, sellFee=0.3, table=None):
        self.crypt = PyCryptsy.PyCryptsy(key,secret)
        self.buyFee = 1.0 - (buyFee / 100.0)
        self.sellFee = 1.0 - (sellFee / 100.0)
        self.last_buy_price = 0
        self.alt_name = str(table.split("_")[0]).upper()
        self.base_name = str(table.split("_")[1]).upper()
        self.get_balances()
        
    def get_info(self):
        print str(self.crypt.GetInfo())    
    
    def get_balances(self):
        self.alt = self.crypt.GetAvailableBalance(self.alt_name)
        self.base = self.crypt.GetAvailableBalance(self.base_name)
        
        print self.alt_name + " balance: " + str(self.alt)
        print self.base_name + " balance: " + str(self.base)
        
    def buy(self):
        self.get_balances()
        print self.alt
        print self.base
        price = self.crypt.GetSellPrice(self.alt_name, self.base_name)
        self.last_buy_price = price #Store the last buy price.
        qty = (self.base * 0.02) / price #Only risk 2% of capital at a time...
        self.crypt.CreateBuyOrder(self.alt_name, self.base_name, qty, price + (price * 0.05)) #Added multiplication -- to hopefully guarantee that we get more quantity.
        print "\n\nCryptsy: Buying " + str(qty) + " " + self.alt_name + " at " + str(price) + " " + self.base_name + " each, for a total of " + str(qty * price) + " " + self.base_name + " before fees."
        return str("\n\nCryptsy: Buying " + str(qty) + " " + self.alt_name + " at " + str(price) + " " + self.base_name + " each, for a total of " + str(qty * price) + " " + self.base_name + " before fees.")        

    def sell(self):
        self.get_balances()
        sell_price = self.crypt.GetSellPrice(self.alt_name, self.base_name)
        buy_price = self.crypt.GetBuyPrice(self.alt_name, self.base_name)
        price = buy_price - ((buy_price - sell_price) * 0.10)
        qty = self.alt
        self.crypt.CreateSellOrder(self.alt_name, self.base_name, qty, price)
        print "\n\nCryptsy: Selling " + str(qty) + " " + self.alt_name + " at " + str(price) + " " + self.base_name + " each, for a total of " + str(qty * price) + " " + self.base_name + " before fees. Our last buy price was: " + str(self.last_buy_price)
        return str("\n\nCryptsy: Selling " + str(qty) + " " + self.alt_name + " at " + str(price) + " " + self.base_name + " each, for a total of " + str(qty * price) + " " + self.base_name + " before fees. Our last buy price was: " + str(self.last_buy_price))
        
class Candle():
    def __init__(self, trades):
        if len(trades) != 0:
            self.open, self.close, self.high, self.low, self.volume = self.calculate(trades)
        
    def calculate(self, trades):
        open = trades[0][2]
        close = trades[-1][2]
        high = trades[0][2]
        low = trades[0][2]
        volume = 0
        
        for trade in trades:
            #print str(trade)
            volume = volume + trade[3]
            if trade[2] > high:
                high = trade[2]
            if trade[2] < low:
                low = trade[2]
                
        return open, close, high, low, volume

class Trader():
    def __init__(self, table, interval=60, numCandles=100, backtest=True, verbose=True, alertsonly=False, emails=False):
        self.table = table
        self.interval=interval
        self.backtest=backtest
        if numCandles is not None:
            self.numCandles=int(numCandles)
        else:
            self.numCandles=numCandles
            
        if self.backtest is True:
            self.portfolio = BacktestPortfolio()
            self.final_btc = 0
            self.change = 0
            self.bh_btc = 0
            self.bh_change = 0
            print "Backtesting..."
        elif self.backtest is False:
            print "Live trading!"
            self.portfolio = CryptsyPortfolio(table=self.table)
        self.verbose=verbose
        self.alertsonly=alertsonly
        self.emails=emails
        if self.emails is True:
            self.mailer = Mailer(table=self.table)
        self.live_trade = False
        self.pre_candles = {}
        self.candles = {}
        self.newest_date = None
        self.older_date = None
        self.newer_date = None
        self.trade_time = None
        self.first_trade = True
        
        self.convert_trades_to_candles()
        
    def convert_trades_to_candles(self):
        if self.older_date is not None and self.newer_date > datetime.now(): #Don't store unclosed (recent) candle...
            return False
        
        if len(self.pre_candles) == 0:
            self.pre_candles[0] = []
            
        if len(self.candles) == 0:
            counter = 0
        else:
            counter = len(self.candles) - 1
            
        conn = sqlite3.connect("cryptsy_trades.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM " + self.table + " ORDER BY datetime DESC LIMIT 1;")
        for trade in cursor:
            self.newest_date = datetime.strptime(str(trade[1]), '%Y-%m-%d %H:%M:%S')
        
        cursor.execute("SELECT * FROM " + self.table + " ORDER BY datetime ASC;")
        #Organize trades by time window.
        for trade in cursor:
            self.trade_time = datetime.strptime(str(trade[1]), '%Y-%m-%d %H:%M:%S')
            
            if self.numCandles is not None:
                if self.trade_time < (self.newest_date - timedelta(0, (self.interval*60) * self.numCandles)):
                    continue         
            
            if self.older_date is None: #First time running/generating candles
                print "Oldest trade: " + str(trade)
                self.older_date = datetime.strptime(str(trade[1]), '%Y-%m-%d %H:%M:%S')
                self.newer_date = self.older_date + timedelta(0, self.interval*60)
            
            
            if self.trade_time < self.older_date:
                continue

            if self.trade_time >= self.older_date and self.trade_time < self.newer_date:
                self.pre_candles[counter].append(trade)
                continue
            else:
                if (self.newer_date + timedelta(0, self.interval*60)) > datetime.now(): #No need to start calculating the candle for the next (live) interval.
                    break
                self.older_date = self.newer_date
                self.newer_date = self.older_date + timedelta(0, self.interval*60)
                counter += 1
                self.pre_candles[counter] = []
                continue
        
        while (self.newer_date < datetime.now()):
            self.older_date = self.newer_date
            self.newer_date = self.older_date + timedelta(0, self.interval*60)
            counter += 1
            self.pre_candles[counter] = []
                
        conn.close()
        #END Organize trades by time window.
        
        print "Last trade time: " + str(self.trade_time)
        
        #Calculate candles for each window.
        lenCandles = len(self.candles)
        for key in self.pre_candles.keys():
            if len(self.pre_candles[key]) != 0:
                #print str(pre_candles[key])
                self.candles[key] = Candle(self.pre_candles[key])
                '''
                if self.candles[key] is not None:
                    print "Candle: " + str(key)
                    print "\tOpen: \t" + str(self.candles[key].open)
                    print "\tClose: \t" + str(self.candles[key].close)q
                    print "\tHigh: \t" + str(self.candles[key].high)
                    print "\tLow: \t" + str(self.candles[key].low)
                    print "\tVol: \t" + str(self.candles[key].volume)'''
            else:
                self.candles[key] = self.candles[key-1]
                self.candles[key].volume = 0
        #END Calculate candles for each window.
        if lenCandles < len(self.candles):
            return True
        else:
            print "Why the crap are we here..? :("
            return False
        
class MovingAverages(Trader):
    def __init__(self, table="ltc_btc", short=10, long=21, interval=60, numCandles=100, sellThreshold=0.0, buyThreshold=0.25, sellFee=0.3, buyFee=0.2, backtest=True, verbose=True, alertsonly=False, emails=False):
        Trader.__init__(self, table=table, interval=interval, numCandles=numCandles, backtest=backtest, verbose=verbose, alertsonly=alertsonly, emails=emails)
        self.short = short
        self.long = long
        self.shortEMAs = {}
        self.longEMAs = {}
        self.sellThreshold = sellThreshold
        self.buyThreshold = buyThreshold
        self.sellFee = sellFee
        self.buyFee = sellFee

        self.currentTrend = None
        self.eval_ema() #Calculate EMAs
        
        if self.backtest is False:
            self.live()
            
    def live(self):
        self.live_trade = True
        while True:
            if self.newer_date <= datetime.now():
                print "Checking for new trades..."
                if self.convert_trades_to_candles() is True:
                    print "Got new candle/s."
                
                    shortEMA = self.calculateEMA(self.candles[len(self.candles) - 1].close, self.short, self.shortEMAs[len(self.shortEMAs) - 1])
                    longEMA = self.calculateEMA(self.candles[len(self.candles) - 1].close, self.long, self.longEMAs[len(self.longEMAs) - 1])
                    
                    self.shortEMAs[len(self.shortEMAs)] = shortEMA
                    self.longEMAs[len(self.longEMAs)] = shortEMA
                    
                    self.diffs[len(self.diffs)] = self.get_diff(shortEMA, longEMA)
                    
                    self.advice(self.diffs[len(self.diffs) - 1], len(self.diffs) - 1)
                    
                else:
                    print "No new candles -- I don't think we should be here, anyway."
                    
            else:
                print "Sleeping for: " + str((self.newer_date - datetime.now()))
                sec = (self.newer_date - datetime.now()).seconds
                time.sleep(sec + 1)
                
    def get_diff(self, shortEMA, longEMA):
        return 100.0 * (shortEMA - longEMA) / ((shortEMA + longEMA) / 2)
    
    def advice(self, diff, counter=None):
        advicestr = ""
        if diff > self.buyThreshold:
            if self.verbose is True or self.live_trade is True:
                advicestr = advicestr + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "|" + self.table + ": We are currently in uptrend (" + str(diff) + ") "
            if self.currentTrend != "up": 
                self.currentTrend = "up"
                if self.verbose is True or self.live_trade is True:
                    advicestr = advicestr + "|" + self.table + ": Advice: BUY @ " + str(self.candles[counter].close) + " BTC"
                if self.backtest is True:
                    self.portfolio.buy(price=self.candles[counter].close)
                elif self.live_trade is True and self.alertsonly is False: #THIS IS THE READ DEAL!!
                    advicestr = advicestr + self.portfolio.buy()
            else:
                if self.verbose is True or self.live_trade is True:
                    advicestr = advicestr + "|" + self.table + ": Advice: HOLD @ " + str(self.candles[counter].close) + " BTC"
        elif diff < self.sellThreshold:
            if self.verbose is True or self.live_trade is True:
                advicestr = advicestr + str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")) + "|" + self.table + ": We are currently in downtrend (" + str(diff) + ")"
            if self.currentTrend != "down":
                self.currentTrend = "down"
                if self.verbose is True or self.live_trade is True:
                    advicestr = advicestr + "|" + self.table + ": Advice: SELL @ " + str(self.candles[counter].close) + " BTC"
                if self.backtest is True:
                    self.portfolio.sell(self.candles[counter].close)
                elif self.live_trade is True and self.alertsonly is False: #THIS IS THE REAL DEAL!!
                    advicestr = advicestr + self.portfolio.sell()
            else:
                if self.verbose is True or self.live_trade is True:
                    advicestr = advicestr + "|" + self.table + ": Advice: HOLD @ " +str(self.candles[counter].close) + " BTC"
        
        if len(advicestr) > 5:
            if (self.alertsonly is True or self.live_trade is True) and self.emails is True:
                self.mailer.send(advicestr)
            if self.verbose is True:
                print (advicestr)
    
    def eval_ema(self):
        self.shortEMAs = {}
        self.longEMAs = {}
        self.diffs = {}
        longEMA = self.candles[0].close
        shortEMA = self.candles[0].close
        
        counter = 0
        
        while (counter < len(self.candles) - 1):
            self.shortEMAs[counter] = shortEMA
            self.longEMAs[counter] = longEMA
            self.diffs[counter] = self.get_diff(shortEMA, longEMA)
            self.advice(self.diffs[counter], counter)
            shortEMA = self.calculateEMA(self.candles[counter].close, self.short, shortEMA)
            longEMA = self.calculateEMA(self.candles[counter].close, self.long, longEMA)
            counter += 1
            
        if self.backtest is True:
            try:
                self.final_btc, self.change, self.bh_btc, self.bh_change = self.portfolio.print_final(self.candles[len(self.candles) - 1].close)
            except:
                pass
        
    def calculateEMA(self, price, period, EMA_yesterday):
        k = 2.0 / (period + 1.0)
        return price * k + EMA_yesterday * (1.0-k)
    

class EMAScalping(Trader):
    def __init__(self, table="ezc_ltc", interval=30, numCandles=None, sellFee=0.3, buyFee=0.2, backtest=True, verbose=True, alertsonly=False, emails=False):
        Trader.__init__(self, table=table, interval=interval, numCandles=numCandles, backtest=backtest, verbose=verbose, alertsonly=alertsonly, emails=emails)
        self.trend = ""
        self.backtester()
        if self.backtest is False:
            self.live()
    
    def calculateEMA(self, price, period, EMA_yesterday):
        k = 2.0 / (period + 1.0)
        return price * k + EMA_yesterday * (1.0-k)
           
    def backtester(self):
        self.highEMAs = {}
        self.lowEMAs = {}
        self.diffs = {}
        highEMA = self.candles[0].high
        lowEMA = self.candles[0].low
        
        counter = 0
        
        while (counter < len(self.candles) - 1):
            highEMA = self.calculateEMA(self.candles[counter].high, 5, highEMA)
            lowEMA = self.calculateEMA(self.candles[counter].low, 5, lowEMA)
            self.highEMAs[0] = highEMA
            self.lowEMAs[0] = lowEMA
            self.advice(highEMA, lowEMA, self.candles[counter].open, self.candles[counter].close)
            counter += 1
            
        if self.backtest is True:
            try:
                self.final_btc, self.change, self.bh_btc, self.bh_change = self.portfolio.print_final(self.candles[len(self.candles) - 1].close)
            except:
                pass
            
        if self.backtest is True:
            self.final_btc, self.change, self.bh_btc, self.bh_change = self.portfolio.print_final(self.candles[len(self.candles) - 1].close)
            
    def live(self):
        self.live_trade = True

        while True:
            if self.newer_date <= datetime.now():
                print "Checking for new trades..."
                if self.convert_trades_to_candles() is True:
                    print "Got new candle/s."
                
                    highEMA = self.calculateEMA(self.candles[len(self.candles) - 1].high, 5, self.highEMAs[0])
                    lowEMA = self.calculateEMA(self.candles[len(self.candles) - 1].low, 5, self.lowEMAs[0])
                    
                    self.highEMAs[0] = highEMA
                    self.lowEMAs[0] = lowEMA
                    print "High: " + str(highEMA)
                    print "Low: " + str(lowEMA)
                    print "Open: " + str(self.candles[len(self.candles) - 1].close)
                    print "Current trend: " + self.trend 
                    self.advice(highEMA, lowEMA, self.candles[len(self.candles) - 1].open, self.candles[len(self.candles) - 1].close)
                
                else:
                    print "No new candles -- I don't think we should be here, anyway."
                    
            else:
                print "Sleeping for: " + str((self.newer_date - datetime.now()))
                sec = (self.newer_date - datetime.now()).seconds
                time.sleep(sec + 1)
        return
        
    def advice(self, highEMA, lowEMA, open, close):
        if open > highEMA:
            if self.trend != "down":
                if self.backtest is True:
                    print "SELL @ " + str(close)
                    self.portfolio.sell(price=close)
                elif self.backtest is False and self.live_trade is True:
                    self.mailer.send(self.portfolio.sell())
            self.trend = "down"
        
        if open < lowEMA:
            if self.trend != "up":
                if self.backtest is True:
                    print "BUY @ " + str(close)
                    self.portfolio.buy(price=close)
                elif self.backtest is False and self.live_trade is True:
                    self.mailer.send(self.portfolio.buy())
            self.trend = "up"
        
         


class BreakoutTrading(Trader):
    def __init__(self, table="ezc_ltc", interval=30, numCandles=48, num_enter=18, num_exit=17, sellFee=0.3, buyFee=0.2, backtest=True, verbose=True, alertsonly=False, emails=False):
        Trader.__init__(self, table=table, interval=interval, numCandles=numCandles, backtest=backtest, verbose=verbose, alertsonly=alertsonly, emails=emails)
        self.num_enter=num_enter
        self.num_exit=num_exit
        self.closing_prices = []
        self.max = 0
        self.min = 0
        self.current_price = 0
        
        self.backtester()
        
        if self.backtest is False:
            self.live()
        
    def live(self):
        self.live_trade = True
        while True:
            if self.newer_date <= datetime.now():
                print "Checking for new trades..."
                if self.convert_trades_to_candles() is True:
                    print "Got new candle/s."
                
                    self.current_price = self.candles[len(self.candles) - 1].close
                    self.advice()
                    self.push_price(self.current_price)

                else:
                    print "No new candles -- I don't think we should be here, anyway."
                    
            else:
                print "Sleeping for: " + str((self.newer_date - datetime.now()))
                sec = (self.newer_date - datetime.now()).seconds
                time.sleep(sec + 1)
    
    def backtester(self):
        counter = 0
        print str(len(self.candles))
        while (counter < len(self.candles) - 1):
            self.current_price = self.candles[counter].close
            self.advice()
            self.push_price(self.current_price)
            counter += 1
            
        if self.backtest is True:
            self.final_btc, self.change, self.bh_btc, self.bh_change = self.portfolio.print_final(self.candles[len(self.candles) - 1].close)
    
    def push_price(self, price):
        self.closing_prices.insert(0, price)
        while len(self.closing_prices) > self.num_enter:
            self.closing_prices.pop()
    
    def advice(self):
        if self.current_price > self.get_max():
            self.portfolio.buy(price=self.current_price)
            print "BUY @ " + str(self.current_price)
        elif self.current_price < self.get_min():
            self.portfolio.sell(self.current_price)
            print "SELL @ " + str(self.current_price)
        else:
            print "HOLD @" + str(self.current_price)
        
        
    def get_max(self):
        if len(self.closing_prices) < self.num_enter:
            max = self.closing_prices[:-1]
        else:
            max = self.closing_prices[self.num_enter - 1]
        i = 0
        while i < self.num_enter and i < len(self.closing_prices):
            price = self.closing_prices[i]
            if price > max:
                max = price
            i += 1
        return max
    
    def get_min(self):
        if len(self.closing_prices) < self.num_exit:
            min = self.closing_prices[:-1]
        else:
            min = self.closing_prices[self.num_exit - 1]
        i = 0
        while i < self.num_exit and i < len(self.closing_prices):
            price = self.closing_prices[i]
            if price < min:
                min = price
            i += 1
        return min
    
class results():
    def __init__(self):
        self.best_btc = 0
        self.final_change = 0

class Starter():
    def __init__(self, table,short,long,interval,candle,buy_threshold,sell_threshold):
        self.table = table
        self.short = short
        self.long = long
        self.interval = interval
        self.candle = candle
        self.buy_threshold=buy_threshold
        self.sell_threshold=sell_threshold

def multithread(q, lock):
    while True:
        starter = q.get()
        
        if starter is None:
            break
        
        tableResults = {}
        ma = MovingAverages(table=starter.table, short=starter.short, long=starter.long, interval=starter.interval, backtest=True, verbose=False, emails=False,numCandles=starter.candle,buyThreshold=starter.buy_threshold, sellThreshold=starter.sell_threshold) 
        key = str(starter.table) + ";" + str(starter.short) + "/" + str(starter.long) + ";" + str(starter.interval) + ";" + str(starter.candle) + ";" + str(starter.buy_threshold) + ";" + str(starter.sell_threshold)
        tableResults[key] = results()
        tableResults[key].best_btc = ma.final_btc
        tableResults[key].final_change = ma.change  
        if ma.change > 0.0 and ma.portfolio.num_trades > 0:  
            lock.acquire()  
            with open("results", "a") as f:
                f.write(key + ";" + str(ma.final_btc) + ";" + str(ma.change) + ";" + str(ma.portfolio.num_trades) + ";" + str(ma.bh_btc) + ";" + str(ma.bh_change) + ";" + str(ma.final_btc - ma.bh_btc) + "\n")
                f.close()
            lock.release() 



def main(type=None, market=None, short=None, long=None, interval=None, backtest=True, quiet=False, numCandles=None, emails=True, buy_threshold=0.25, sell_threshold=(-0.25)):
    
    if quiet is False:
        verbose = True
    else:
        verbose=False

    if options.type == "ClassicEMA":
        print "Starting ClassicEMA..."
        MovingAverages(table=market, short=short, long=long, interval=interval, backtest=backtest, verbose=verbose, alertsonly=False, numCandles=numCandles, emails=emails, buyThreshold=buy_threshold, sellThreshold=sell_threshold)
    
    if options.type == "EMAScalping":
        print "Starting EMAScalping..."
        EMAScalping(table=market, interval=interval, backtest=backtest, verbose=verbose, alertsonly=False, emails=emails)
          

          
def profits():
    lock = Lock()
    processes = []
    i = 0
    q = Queue()
    while i < cpu_count():
        p = Process(target=multithread, args=(q, lock))
        processes.append(p)
        p.daemon = True
        p.start()
        i += 1
        
    emaPeriod = [[5,8],[10,21],[20,50],[50,200]]
    timePeriod = [15, 30, 60, 60*2, 60*4, 60*6, 60*12, 60*24]
    crypt = PyCryptsy.PyCryptsy("","")
    num_candles = [None]
    sell_thresholds = [0.0, -0.1, -0.25]
    buy_thresholds = [0.0, 0.1, 0.25]
    
    for item in crypt.GetMarkets():
        table = str(str(item["primary_currency_code"]).lower() + "_" + str(item["secondary_currency_code"]).lower())
        print "Testing " + str(table) + " ",
        for interval in timePeriod:
            for candle in num_candles:
                for ema in emaPeriod:
                    for sell_threshold in sell_thresholds:
                        for buy_threshold in buy_thresholds:
                            short = ema[0]
                            long = ema[1]
                            start = Starter(table, short,long,interval,candle,buy_threshold,sell_threshold)
                            q.put(start)
                    
    for item in processes:
        q.put(None)

    #Add in capability to check varying thresholds, as well.

        
    for p in processes:
        p.join()
    
    
if __name__ == '__main__':
    usage = "Usage: %prog [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-t", "--type", dest="type", help="Choose the type of trading: [EMAScalping, ClassicEMA]", default="ClassicEMA")
    parser.add_option("-m", "--market", dest="market", help="Market in the format of 'alt_base'", default=None)
    parser.add_option("-s", "--short", dest="short", help="Short EMA period.", default=0)
    parser.add_option("-l", "--long", dest="long", help="Long EMA period.", default=0)
    parser.add_option("-i", "--interval", dest="interval", help="Candle interval, in minutes.", default=None)
    parser.add_option("-b", "--backtest", dest="backtest", action="store_true", help="Don't live trade -- just backtest.", default=False)
    parser.add_option("-q", "--quiet", dest="quiet", action="store_true", help="Be less verbose.", default=False)
    parser.add_option("-e", "--emails", dest="emails", action="store_true", help="Send email alerts.", default=False)
    parser.add_option("-n", "--num_candles", dest="candles", help="Number of candles to start the backtest with.", default=None)
    parser.add_option("--bT", dest="buy_threshold", help="Set a buy threshold", default=0.25)
    parser.add_option("--sT", dest="sell_threshold", help="Set a sell threshold", default=(-0.25))
    parser.add_option("--profitable", dest="profitable", action="store_true", help="Find the most profitable coin/combo.", default=False)
    #ADD OPTIONS FOR BUY/SELL THRESHOLDS.
    (options, args) = parser.parse_args()
    
    #BreakoutTrading()
    #exit()
    
    if options.profitable is True:
        profits()
        exit()
    
    if options.market is None or options.interval is None or options.type is None:
        parser.print_help()
        exit(-1)
    else:
        main(type=options.type, market=options.market, short=int(options.short), long=int(options.long), interval=int(options.interval), backtest=options.backtest, quiet=options.quiet, emails=options.emails, numCandles=options.candles, buy_threshold=float(options.buy_threshold), sell_threshold=float(options.sell_threshold))

