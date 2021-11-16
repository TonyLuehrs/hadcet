import numpy as np
import pandas as pd
from python.data import read_local_hadcet_data, download_hadcet_data, flatten_time

months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']


class Model:

    def __init__(self, local_data=True):
        self.local_data = local_data
        self.df = self.get_hadcet_df()
        self.ave_df = self.get_daily_ave_df()


    # this method uses all three static functions above to create the DataFrame we need
    def get_hadcet_df(self):

        # get 2D temp DataFrames
        if self.local_data:
            meantemps = read_local_hadcet_data('hadcet_mean.txt')
            mintemps = read_local_hadcet_data('hadcet_min.txt')
            maxtemps = read_local_hadcet_data('hadcet_max.txt')
        else:
            mean_temp_url = 'https://www.metoffice.gov.uk/hadobs/hadcet/cetdl1772on.dat'
            min_temp_url = 'https://www.metoffice.gov.uk/hadobs/hadcet/cetmindly1878on_urbadj4.dat'
            max_temp_url = 'https://www.metoffice.gov.uk/hadobs/hadcet/cetmaxdly1878on_urbadj4.dat'
            meantemps = download_hadcet_data(mean_temp_url)
            mintemps = download_hadcet_data(min_temp_url)
            maxtemps = download_hadcet_data(max_temp_url)

        # flatten the 2D DataFrames into 1D Series
        mean_series = flatten_time(meantemps)
        min_series = flatten_time(mintemps)
        max_series = flatten_time(maxtemps)

        # combine them into one DataFrame, organize columns
        temps_df = pd.concat([mean_series, min_series, max_series], axis=1)
        temps_df = temps_df.reset_index()
        temps_df.columns = ['date', 'meantemp', 'mintemp', 'maxtemp']

        # get some simpler time columns for indexing later (we wanted the datetime col for the pd.concat())
        temps_df['year'] = temps_df['date'].apply(lambda d: int(str(d).split()[0].split('-')[0]))
        temps_df['month'] = temps_df['date'].apply(lambda d: int(str(d).split()[0].split('-')[1]))
        temps_df['day'] = temps_df['date'].apply(lambda d: int(str(d).split()[0].split('-')[2]))
        temps_df = temps_df[['date', 'year', 'month', 'day', 'meantemp', 'mintemp', 'maxtemp']]

        return temps_df

    # (Part 1) this generates the DataFrame used to create the first plot in the dashboard
    def get_daily_ave_df(self):

        lows = []
        highs = []
        aves = []
        fifths = []
        ninetyfifths = []
        month_list = []
        day_list = []
        cols = ['meantemp', 'mintemp', 'maxtemp']

        for month in range(1, 13):
            for day in range(1, 32):
                daytemps = self.df[(self.df['month'] == month) & (self.df['day'] == day)][cols]
                if len(daytemps > 0):
                    lows.append(daytemps['mintemp'].min())
                    highs.append(daytemps['maxtemp'].max())
                    aves.append(daytemps['meantemp'].mean())
                    fifths.append(np.percentile(daytemps['meantemp'].values, 5))
                    ninetyfifths.append(np.percentile(daytemps['meantemp'].values, 95))
                    month_list.append(month)
                    day_list.append(day)

        ave_df = pd.DataFrame({'month': month_list, 'day': day_list, 'lows': lows, 'highs': highs, 'aves': aves,
                               'fifths': fifths, 'ninetyfifths': ninetyfifths, })

        return ave_df

    # (Part 2) this generates the DataFrame for a table in the dashboard
    def get_day_prev_5yr(self, month, day):

        # TODO -need to make a custom fix for Feb. 29, only shows 2016 and 2020

        # find the most recent year that a temp has been recorded for this day and month
        last_whole_year = self.df[(self.df['day'] == day) & (self.df['month'] == month)]['year'].max()

        # select year, min, and max associated with this day and month and within the most recent 5 years
        # finally, reverse the list so that the most recent temp is on top
        normal_range = range(last_whole_year - 4, last_whole_year + 1)
        feb29_range = range(last_whole_year - 16, last_whole_year + 1)
        our_range = normal_range if not ((month == 2) and (day == 29)) else feb29_range
        #print(month, day, list(our_range))
        cols = ['year', 'mintemp', 'maxtemp']
        table_df = self.df[(self.df['year'].isin(list(our_range))) &
                           (self.df['day'] == day) & (self.df['month'] == month)][cols].iloc[::-1, :]

        # force them into strings because dash keeps giving me the ol' 3.4000000000000001
        table_df['mintemp'] = table_df['mintemp'].round(1).astype(str)
        table_df['maxtemp'] = table_df['maxtemp'].round(1).astype(str)

        # rename columns to how we'll want them to be in the dashboard
        table_df.columns = ['Year', 'Daily Low', 'Daily High']

        return table_df

    # (Part 2) this generates two DataFrames for two tables in the dashboard
    def get_day_records(self, month, day):
        maxdf = self.df[(self.df['month'] == month) & (self.df['day'] == day)] \
                    .sort_values('maxtemp', ascending=False)[['year', 'maxtemp']][:5]
        mindf = self.df[(self.df['month'] == month) & (self.df['day'] == day)] \
                    .sort_values('mintemp')[['year', 'mintemp']][:5]

        # dashboard tables are bad about miniscule floating point error, so we pass in a rounded string instead
        mindf['mintemp'] = mindf['mintemp'].round(1).astype(str)
        maxdf['maxtemp'] = maxdf['maxtemp'].round(1).astype(str)

        maxdf.columns = ['Year', 'Temp (C)']
        mindf.columns = ['Year', 'Temp (C)']

        return mindf, maxdf

    # (Part 2) this generates the historical probability of seeing at least a given temp on a given day
    def get_perc_geq(self, month, day, temp):
        temps = self.df[(self.df['month'] == month) & (self.df['day'] == day)]['meantemp'].values
        count_geq = sum([t >= temp for t in temps])
        return str(round(count_geq * 100 / len(temps), 1))

    def get_year_comp_table(self, years):

        # don't want the table to be too long, only accept 5 selected years (dash has no way to limit the number of
        #  selections in a multi-dropdown)
        years = years[:5]
        year_comp_table = pd.DataFrame(columns=['Year', 'Average', 'Low', 'High'])
        year_comp_table.loc[0] = ['All Time',
                                  str(round(self.ave_df['aves'].mean(), 2)),
                                  str(round(self.df['mintemp'].min(), 1)),
                                  str(round(self.df['maxtemp'].max(), 1))]
        if len(years) == 0:
            return year_comp_table
        for i, year in enumerate(years):
            year_comp_table.loc[i+1] = [str(year),
                                        str(round(self.df[self.df['year'] == year]['meantemp'].mean(), 2)),
                                        str(round(self.df[self.df['year'] == year]['mintemp'].min(), 1)),
                                        str(round(self.df[self.df['year'] == year]['maxtemp'].max(), 1))]

        return year_comp_table

# hadcet = Model()
# print(hadcet.df['year'])
# print(hadcet.get_year_comp_table([2020, 2019, 2018]))