import pandas as pd
import numpy as np
import datetime as dt
import plotly.express as px
import plotly.graph_objects as go
import pandas_datareader as web
import yfinance as yf
from flask import Flask, request

app = Flask(__name__)
app.config["DEBUG"] = True

@app.route('/api/v1/capture', methods=['POST'])
def create_upside_downside():
  start = request.json["start"]
  end = request.json["end"]
  num_tckrs = request.json["num_tckrs"]
  ref_tckr = request.json["ref_tckr"]
  per = request.json["per"]
  data = get_data(start, end, num_tckrs, ref_tckr, per)
  up, down = buckets(data)
  capture_calcs = capture(up, down)
  beta_calcs = beta(up, down)
  # only doing capture right now for testing
  return capture_calcs.to_json()
  


def get_data(start, end, num_tckrs, ref_tckr, per):
    print(request.json)
    # Gets the start date, end date, number of stocks to comapare, and the reference stock/index from the user
    #start = dt.datetime.strptime(input("Enter the starting date(YYYY-MM-DD): "), '%Y-%m-%d').date()
    #end = dt.datetime.strptime(input("Enter the ending date(YYYY-MM-DD): "), '%Y-%m-%d').date()
    #num_tckrs = input("How many stocks would you like to compare? ")
    #ref_tckr = input("What would you like to compare the stocks too? ") #^GSPC is the S&P 500 ticker on yf for some reason
    #per = input("Would you like Annual(Y), Monthly(M), or Weekly(W) Data? ")

    #Loop to get individual securities
    
    tckr_list = [ref_tckr]
    for i in range(int(num_tckrs)):
      tckr_list.append(input("Security " + str(i + 1) + " : ").upper())
    
    #Loop to grab the price data from yahoo finance and combine them into one pandas dataframe
    stock_data = pd.DataFrame()
    for tckr in tckr_list:
        data = yf.download(tckr, start, end) #function to actually grab the data
        if per == 'Y':
          data = data.iloc[((len(data.index)-1)%252)::252].pct_change().dropna() # converts price data into yearly returns data
        elif per == 'M':
          data = data.iloc[((len(data.index)-1)%21)::21].pct_change().dropna() # converts price data into Monthly returns data
        elif per == 'W':
          data = data.iloc[((len(data.index)-1)%5)::5].pct_change().dropna() # converts price data into weekly returns data
        stock_data[tckr] = data['Close'] #appends to overall/output dataframe
    return stock_data


def buckets(data):
    avg = data.iloc[:, 0].mean() #grabs the average from the 1st column, which will always be the reference inputted by the user
    data['Direction'] = np.where(data.iloc[:, 0] >= avg, 1, 0) #look up np.where() for info on this function, np is numpy which is a common python library
    up_data = data.loc[data['Direction'] == 1].drop(['Direction'], axis = 1) #grabs up data
    down_data = data.loc[data['Direction'] == 0].drop(['Direction'], axis = 1) #grabs down data
    return up_data, down_data

def capture(up, down):
  cap = pd.DataFrame()

  for i in [up, down]:
    ref = i.iloc[:, 0] + 1
    lis = {}
    for j in i:
      stock = i[j] + 1
      lis[j] = (np.prod(stock)-1)/(np.prod(ref)-1) *100
    cap = cap.append(lis, ignore_index = True)
  cap.index = ['Up Capture', 'Down Capture']
  return cap

def beta(up, down):
  betas = pd.DataFrame()

  for i in [up, down]:
    ref = i.iloc[:, 0] + 1
    lis = {}
    for j in i:
      stock = i[j]
      corr = pd.DataFrame(ref).corrwith(stock)[0]
      lis[j] = (np.std(stock)/np.std(ref))*corr
    betas = betas.append(lis, ignore_index = True)
  betas.index = ['Up Beta', 'Down Beta']

  return betas


def graphing(capture_calc, beta_calc):
  line = [(0, capture_calc.max().max()), (0, capture_calc.max().max())]
  fig = go.Figure()
  fig.add_trace(go.Scatter(x = capture_calc.iloc[1], y = capture_calc.iloc[0], mode='markers', name = 'Down, Up'))
  fig.add_trace(go.Line(x = line[0], y = line[1], mode = 'lines', name = 'Reference Line'))
  fig.update_layout(title = {'text': 'Up vs. Down Capture'}, xaxis_title = 'Down Capture', yaxis_title = 'Up Capture')
  fig.show()

  line = [(0,beta_calc.max().max()), (0,beta_calc.max().max())]
  gif = go.Figure()
  gif.add_trace(go.Scatter(x = beta_calc.iloc[1], y = beta_calc.iloc[0], mode='markers', name = 'Down, Up'))
  gif.add_trace(go.Line(x = line[0], y = line[1], mode = 'lines', name = 'Reference Line'))
  gif.update_layout(title = {'text': 'Up vs. Down Beta'}, xaxis_title = 'Down Beta', yaxis_title = 'Up Beta')
  gif.show()


if __name__ == '__main__':
    app.run()
