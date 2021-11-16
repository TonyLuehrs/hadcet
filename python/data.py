import pandas as pd
import numpy as np
import datetime
import requests

months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

# use this function if the data is being accessed via 'requests'
def download_hadcet_data(url):

    print('accessing data from the hadcet website')
    # download the .txt data file
    response = requests.get(url)

    # split over newlines, split over whitespace, convert from string to int
    data = [[int(x) for x in row.split()] for row in response.text.split('\n')]
    df = pd.DataFrame(data)

    # all text files have blank last row, comes into pandas as row of nans
    df = df[:-1]

    # convert all cols to int (just need days and years as int for datetime)
    for i in df.columns:
        df[[i]] = df[[i]].astype(float).astype(int)
        
    # rename columns: year, day, {12 months}
    cols = ['year', 'day'] + months
    df.columns = cols
        
    return df


# use this function if the data is being accessed locally
def read_local_hadcet_data(filename):

    with open('C:/Users/alueh/Desktop/NEXT/Hadcet Dashboard/data/' + filename) as f:
        data = [[int(x) for x in row.replace('\n', '').split()] for row in f.readlines()]

    df = pd.DataFrame(data)

    # convert all cols to int (just need days and years as int for datetime)
    for i in df.columns:
        df[[i]] = df[[i]].astype(float).astype(int)

    # rename columns: year, day, {12 months}
    cols = ['year', 'day'] + months
    df.columns = cols

    return df


# data is 1D, but in 2D structure, need to flatten it
def flatten_time(df):
    
    # create empty Series to hold ALL temperatures
    temperatures = pd.Series(dtype='float64')
    
    # identify initial and final years of the dataset
    firstyear = df['year'].min()
    finalyear = df['year'].max()

    # initialize other variables
    finalmonth = -1
    finalday = -1
    
    # for each year, flatten the data and append to the temperatures Series
    for yr in range(firstyear, finalyear+1):
        
        # slice out just one years' data from the overall df
        yrdf = df[df['year'] == yr]
        
        # if its the final year of dataset, find the final month and day of data
        if yr == finalyear:
            
            # find first col of all -999; month previous is our finalmonth
            finalmonth = -1
            for i, mo in enumerate(months):
                if all(yrdf[mo] == -999):
                    finalmonth = i
                    break
            # if no cols were filled with -999, december must be last month
            if finalmonth == -1:
                finalmonth = 12
            
            # final day is 31 minus number of -999s in the final col
            finalday = 31 - sum(yrdf.iloc[:, finalmonth+1] == -999)
            
        # now (un?)ravel all of the temps into one list, drop nans==-999
        yrtemps = yrdf[months].to_numpy().T.ravel()*.1
        yrtemps = np.delete(yrtemps, np.where(yrtemps == -99.9))

        # create datetime index using finalyr/month/day info we got
        sdate = datetime.date(yr, 1, 1)
        #print(finalyear, finalmonth, finalday)
        edate = datetime.date(yr, 12, 31) if yr < finalyear else datetime.date(finalyear, finalmonth, finalday)
        delta = edate - sdate
        idx = pd.date_range(sdate, edate).tolist()

        # create Series with index=datetime, values=temperatures, append to overall Series
        yr_ser = pd.Series(yrtemps, index=idx)
        temperatures = temperatures.append(yr_ser)
    
    return temperatures


# we'll want to add some rolling average columns
def get_rolling_ave(array, size, fillna=False):
    # compute rolling average (the smart way)
    cs = np.cumsum(array)
    cs[size:] = cs[size:] - cs[:-size]
    result = cs[size - 1:] / size
    # put filler np.nan values in front to keep length
    if fillna:
        front = np.empty(size - 1)
        front[:] = np.nan
        result = np.concatenate((front, result))

    return result


##################################################################################
### All of the below of this code is functions that became methods in model.py ###
### The above four functions are still imported intho model.py and plot.py     ###
##################################################################################


# # default is to access local data; set to False to use requests with the urls
# def get_hadcet_df(local_data=True):
#
#     # get local or online data
#     if local_data:
#         meantemps = read_local_hadcet_data('hadcet_mean.txt')
#         mintemps = read_local_hadcet_data('hadcet_min.txt')
#         maxtemps = read_local_hadcet_data('hadcet_max.txt')
#     else:
#         mean_temp_url = 'https://www.metoffice.gov.uk/hadobs/hadcet/cetdl1772on.dat'
#         min_temp_url = 'https://www.metoffice.gov.uk/hadobs/hadcet/cetmindly1878on_urbadj4.dat'
#         max_temp_url = 'https://www.metoffice.gov.uk/hadobs/hadcet/cetmaxdly1878on_urbadj4.dat'
#         meantemps = download_hadcet_data(mean_temp_url)
#         mintemps = download_hadcet_data(min_temp_url)
#         maxtemps = download_hadcet_data(max_temp_url)
#
#     # get all three temperature Series with date as the joining index
#     mean_series = flatten_time(meantemps)
#     min_series = flatten_time(mintemps)
#     max_series = flatten_time(maxtemps)
#
#     # combine them into one DataFrame, organize columns
#     temps = pd.concat([mean_series, min_series, max_series], axis=1)
#     temps = temps.reset_index()
#     temps.columns = ['date', 'meantemp', 'mintemp', 'maxtemp']
#
#     # get some simpler time columns for indexing later (we wanted the datetime col for the pd.concat())
#     temps['year'] = temps['date'].apply(lambda d: int(str(d).split()[0].split('-')[0]))
#     temps['month'] = temps['date'].apply(lambda d: int(str(d).split()[0].split('-')[1]))
#     temps['day'] = temps['date'].apply(lambda d: int(str(d).split()[0].split('-')[2]))
#     temps = temps[['date', 'year', 'month', 'day', 'meantemp', 'mintemp', 'maxtemp']]
#
#     return temps
#
#
# # takes in the df from get_final_df(), generates a df for aves for each day of the year
# def get_daily_ave_df(df):
#
#     lows = []
#     highs = []
#     aves = []
#     fifths = []
#     ninetyfifths = []
#     month_list = []
#     day_list = []
#
#     for month in range(1, 13):
#         for day in range(1, 32):
#             daytemps = df[(df['month'] == month) & (df['day'] == day)][['meantemp', 'mintemp', 'maxtemp']]
#             if len(daytemps > 0):
#                 lows.append(daytemps['mintemp'].min())
#                 highs.append(daytemps['maxtemp'].max())
#                 aves.append(daytemps['meantemp'].mean())
#                 fifths.append(np.percentile(daytemps['meantemp'].values, 5))
#                 ninetyfifths.append(np.percentile(daytemps['meantemp'].values, 95))
#                 month_list.append(month)
#                 day_list.append(day)
#
#     ave_df = pd.DataFrame({'month': month_list, 'day': day_list, 'lows': lows, 'highs': highs, 'aves': aves,
#                            'fifths': fifths, 'ninetyfifths': ninetyfifths,})
#
#     return ave_df
#

# def get_day_prev_5yr(df, month, day):
#
#
#     # find the most recent year that a temp has been recorded for this day and month
#     last_whole_year = df[(df['day'] == day) & (df['month'] == month)]['year'].max()
#
#     # select year, min, and max associated with this day and month and within the most recent 5 years
#     # finally, reverse the list so that the most recent temp is on top
#     normal_range = range(last_whole_year-4, last_whole_year+1)
#     feb29_range = range(last_whole_year-16, last_whole_year+1)
#     our_range = normal_range if not ((month == 2) and (day == 29)) else feb29_range
#     print(month, day, list(our_range))
#     table_df = df[(df['year'].isin(list(our_range))) &
#                   (df['day'] == day) & (df['month'] == month)][['year', 'mintemp', 'maxtemp']].iloc[::-1, :]
#
#     # force them into strings because dash keeps giving me the ol' 3.4000000000000001
#     table_df['mintemp'] = table_df['mintemp'].round(1).astype(str)
#     table_df['maxtemp'] = table_df['maxtemp'].round(1).astype(str)
#
#     # rename columns to how we'll want them to be in the dashboard
#     table_df.columns = ['Year', 'Daily Low', 'Daily High']
#
#     return table_df
#
#
# def get_day_records(df, month, day):
#     maxdf = df[(df['month']==month) & (df['day']==day)].sort_values('maxtemp', ascending=False)[['year', 'maxtemp']][:5]
#     mindf = df[(df['month']==month) & (df['day']==day)].sort_values('mintemp')[['year', 'mintemp']][:5]
#
#     mindf['mintemp'] = mindf['mintemp'].round(1).astype(str)
#     maxdf['maxtemp'] = maxdf['maxtemp'].round(1).astype(str)
#
#     maxdf.columns = ['Year', 'Temp (C)']
#     mindf.columns = ['Year', 'Temp (C)']
#
#     return mindf, maxdf
#
#
#
# # find percent of days with the given month and day that had a mean temp at least as big as the given temp
# def get_perc_geq(df, month, day, temp):
#     temps = df[(df['month'] == month) & (df['day'] == day)]['meantemp'].values
#     count_geq = sum([t >= temp for t in temps])
#     return str(round(count_geq*100/len(temps), 3))


#df = get_hadcet_df()
