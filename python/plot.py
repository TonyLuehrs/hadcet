import numpy as np
import pandas as pd
import plotly.graph_objects as go
from python.data import get_rolling_ave

class Plot:

    def __init__(self, df, ave_df):

        self.df = df
        self.ave_df = ave_df
        self.long_months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
                            'October', 'November', 'December']
        # self.colors is not used, but the order matches the order of the hex colors in light and dark colors
        self.colors = ['green', 'orange', 'blue', 'pink', 'brown']
        self.light_colors = ['#AADDA9', '#FAC586', '#C2C1FF', '#F9BAF1', '#D9B089']
        self.dark_colors = ['#23A320', '#DD7903', '#2923EC', '#E80DCE', '#6F3600']

    # (Part 1) This gets the five traces that stay the same in the top plot
    def get_alltime_traces(self):
        xspan = pd.date_range(start='1/1/1772', end='12/31/1772')

        high = go.Scatter(x=xspan, y=self.ave_df['highs'], name='record highs', mode='lines',
                          line=dict(color='red', width=1),
                          hovertemplate=
                          "Day:" + "%{x|%m/%d}".rjust(25) +
                          "<br>Record High:" + "%{y} C".rjust(9) +
                          "<br><extra></extra>"
                          )
        nfth = go.Scatter(x=xspan, y=self.ave_df['ninetyfifths'], name='ninety-fifth percentile', mode='lines',
                          line=dict(color='firebrick', width=1), hoverinfo='skip')
        ave = go.Scatter(x=xspan, y=self.ave_df['aves'], name='all-time daily average',
                         line=dict(color='black', width=2),
                         hovertemplate=
                         "Day:" + "%{x|%m/%d}".rjust(40) +
                         "<br>Alltime Day Average:" + "%{y} C".rjust(10) +
                         "<br><extra></extra>"
                         )
        fth = go.Scatter(x=xspan, y=self.ave_df['fifths'], name='fifth percentile', mode='lines',
                         line=dict(color='royalblue', width=1), hoverinfo='skip')
        low = go.Scatter(x=xspan, y=self.ave_df['lows'], name='record lows', mode='lines',
                         line=dict(color='blue', width=1),
                         hovertemplate=
                         "Day:" + "%{x|%m/%d}".rjust(25) +
                         "<br>Record Low:" + "%{y} C".rjust(10) +
                         "<br><extra></extra>"
                         )
        return [high, nfth, ave, fth, low]

    # (Parts 1 & 3) This gets the trace for a single year (with smoothing)
    def get_year_trace(self, year, window_size, color_num):
        yvals = get_rolling_ave(self.df[self.df['year'] == year]['meantemp'].values, window_size, fillna=True)
        yvals = np.concatenate((yvals[(window_size - 1) // 2:], yvals[:(window_size - 1) // 2]))
        year_trace = go.Scatter(x=pd.date_range(start='1/1/1772', end='12/31/1772'), y=yvals,
                                name=f'{year} temps',
                                line=dict(color=self.dark_colors[color_num], width=2),
                                hovertemplate=
                                "Date:" + ("%{x|%m/%d}/" + f"{year}").rjust(21) +
                                "<br>Mean Temp:" + "%{y} C".rjust(9) +
                                "<br><extra></extra>"
                                )
        return year_trace

    # (Part 1) This creates the plot of the current year with the 5 traces generated in the above method
    def get_lineplot(self, year, window_size):
        lineplot = go.Figure()

        # the five lines always on the graph
        alltime_traces = self.get_alltime_traces()
        for t in alltime_traces:
            lineplot.add_trace(t)

        # the selected year's line (0 -> color is always green)
        lineplot.add_trace(self.get_year_trace(year, window_size, 0))

        lineplot.update_xaxes(dtick='M1', tickformat='%b',
                              showline=True, linewidth=2, linecolor='black', gridcolor='grey')
        lineplot.update_yaxes(showgrid=False, zeroline=False,
                              showline=True, linewidth=2, linecolor='black', gridcolor='black')
        lineplot.update_layout(autosize=False, margin=dict(t=0, b=10), width=1000, height=320,
                               yaxis_title='Degrees Celsius',
                               plot_bgcolor='rgb(230, 230, 255)')

        return lineplot

    # (not used) Generates histogram comparing selected year's temps to alltime temps
    def get_histogram(self, which, year):

        # 'which' can take on values of 'mintemp', 'meantemp', or 'maxtemp'

        histogram = go.Figure()
        histogram.add_trace(go.Histogram(x=self.df[self.df['year'] == year][which], histnorm='probability density',
                                         nbinsx=18, name=f'{year} temps'))
        histogram.add_trace(go.Histogram(x=self.df[which], histnorm='probability density',
                                         nbinsx=18, name=f'Alltime daily {which}'))
        histogram.update_xaxes(range=[-5, 30], showgrid=False)
        histogram.update_yaxes(range=[0, .12], showgrid=False, showticklabels=False)
        histogram.update_traces(opacity=0.6)
        histogram.update_layout(barmode='overlay',
                                autosize=False, margin=dict(t=10, b=10), width=450, height=280,
                                legend=dict(yanchor="top", y=1, xanchor="left", x=0))

        return histogram

    # (Part 2) Creates the histogram of all temps on a given date (with a vert line at a selected temp)
    def get_day_hist(self, month, day, temp):
        temps = self.df[(self.df['month'] == month) & (self.df['day'] == day)]['meantemp']
        day_hist = go.Figure()
        day_hist.add_trace(go.Histogram(x=temps, histnorm='probability density', name=f'{month}/{day} temps',
                                        hovertemplate='Temp Range: ' + '%{x}<br>'.rjust(9) +
                                                      'Proportion: ' + '%{y}'.rjust(14)))
        day_hist.add_vline(x=temp)
        day_hist.update_layout(xaxis=dict(range=[-12, 28], tickmode='linear', dtick=1, title='Degrees Celsius',
                                          title_standoff=0),
                               yaxis=dict(range=[0, .25], showticklabels=False, showgrid=False),
                               title_text=f'Histogram of n={len(temps)} observations '
                                          f'from {self.long_months[month - 1]} {day}',
                               title_x=.5,
                               title_yanchor='top',
                               margin_t=35,
                               margin_r=15,
                               width=700,
                               height=350, )

        return day_hist

    # (Part 3) Creates graph comparing temps of selected years, with smoothing
    def get_year_comparison_graph(self, years, window_size, start_month=1, end_month=10):
        xspan = pd.date_range(start='1/1/1772', end='12/31/1772')

        lineplot = go.Figure()

        ave = go.Scatter(x=xspan, y=self.ave_df['aves'], name='all-time average',
                         line=dict(color='black', width=2),
                         hovertemplate=
                         "Day:" + "%{x|%m/%d}".rjust(40) +
                         "<br>Alltime Day Average:" + "%{y} C".rjust(10) +
                         "<br><extra></extra>"
                         )
        lineplot.add_trace(ave)

        for color_num, year in enumerate(years):
            lineplot.add_trace(self.get_year_trace(year, window_size, color_num))

        lineplot.update_xaxes(#dtick='M1',# tickformat='%b',
                              showline=True, linewidth=2, linecolor='black', gridcolor='grey',
                              rangeslider_visible=True,
                              # add range selector on bottom
                              rangeselector=dict(buttons=[dict(step='all', visible=False)]),
                              # change tick format depending on zoom level
                              tickformatstops=[
                                  dict(dtickrange=[None, 3600000000], value="%b%e"),
                                  dict(dtickrange=[3600000000, None], value="%b")])
        lineplot.update_yaxes(showgrid=False, zeroline=False,
                              showline=True, linewidth=2, linecolor='black', gridcolor='black')
        lineplot.update_layout(autosize=False, margin=dict(t=25, b=0, r=60, l=117), width=765, height=300,
                               yaxis_title='Degrees Celsius',
                               plot_bgcolor='rgb(230, 230, 255)',
                               #legend=dict(x=0, y=1),
                               showlegend=False,
                               title_text=f'Year Comparison with smoothing window of n={window_size} days',
                               title_x=.5,
                               yaxis=dict(range=[0, 21]),
                               xaxis=dict(range=[self.long_months[start_month-1][:3],
                                                 self.long_months[end_month-1][:3]])
                               )

        return lineplot