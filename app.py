import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_table

from python.model import Model
from python.plot import Plot


##############################
### Create an App Instance ###
##############################


theme = dbc.themes.LUX
css = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css'

app = dash.Dash(name='name', external_stylesheets=[theme, css])
server = app.server
app.title = 'HADCET Temperature Data'


###################################################################################
### Setup - get data, create initial objects that will get updated in callbacks ###
###################################################################################


# some month-related variables we'll need to convert between numeric months, month shorthands, month longhands
long_months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
               'October', 'November', 'December']
short_months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
month_dict = {short_months[i]: i + 1 for i in range(12)}
month_dict_rev = {v: k for k, v in month_dict.items()}
month_length_dict = {1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}

# instantiate our two classes
hadcet = Model(local_data=False)
plot = Plot(hadcet.df, hadcet.ave_df)

# initial values we'll use for the start of the dashboard
day0, month0, year0 = 1, 1, 2020
temp0 = 5

# easier to reference this unicode string than put it directly in a string
degree_sign = '\u00b0'

# initial graphs/values we'll use for the start of the dashboard
start_lineplot = plot.get_lineplot(year0, day0)
start_day_hist = plot.get_day_hist(month0, day0, temp0)
start_day_recent5 = hadcet.get_day_prev_5yr(month0, day0)
start_day_perc_geq = hadcet.get_perc_geq(month0, day0, temp0)
start_recs_min, start_recs_max = hadcet.get_day_records(month0, day0)
start_year_comp_table = hadcet.get_year_comp_table([2020])
start_year_comp_graph = plot.get_year_comparison_graph([2020], 1)


#####################
### Define Inputs ###
#####################


# Inputs for Part 1
year_input = dcc.Input(id='year-input', placeholder='year', type='number',
                       min=1772, max=2020, step=1, value=2020)
window_size_input = dcc.Input(id='window-size-input', min=1, max=35, step=2, value=1, type='number',
                              placeholder='rolling average window size')

# Inputs for Part 2
month_input = dcc.Dropdown(id='month-input', placeholder='month', value='jan',
                           options=[{'label': long_months[i], 'value': short_months[i]} for i in range(12)])
day_input = dcc.Input(id='day-input', placeholder='day', value=1, min=1, max=31, step=1, type='number')
temp_input = dcc.Input(id='temp-input', placeholder='temp', value=0, min=-20, max=40, step=1, type='number',
                       style={'display': 'inline-block'})

# Inputs for Part 3
multi_year_input = dcc.Dropdown(id='multi-year-input', value=['2020'], multi=True,
                                options=[{'label': str(yr), 'value': str(yr)} for yr in range(2020, 1771, -1)])

month_span_input = dcc.RangeSlider(id='month-span-input', min=1, max=12, step=None, value=[1, 12],
                                   marks={i+1: short_months[i] for i in range(12)})


#####################
### Build Layouts ###
#####################


# PART 1 - ALLTIME VS. SELECTED YEAR
layout_part1 = html.Div([
    dbc.Row([
        dbc.Col([
            html.Div('Compare Selected Year to All-time Daily Average',
                     style={'font-weight': 'bold', 'font-size': '32px'})])]),
    html.Br(), html.Br(),
    dbc.Row([
        dbc.Col(children=[
            html.Br(),
            html.Div('Select year', style={'font-weight': 'bold', 'font-size': '16px'}),
            year_input,
            html.Br(), html.Br(), html.Br(),
            html.Div('Select size of rolling average window', style={'font-weight': 'bold', 'font-size': '16px'}),
            window_size_input,
            html.Div('(set =1 for no smoothing)', style={'font-size': '10px'}),
            html.Br()],
            width={'offset': 0, 'size': 2},
            style={'border': '4px #073763 solid', 'border-radius': '4px', 'height': '280px', 'align': 'bottom'}),
        dbc.Col(children=[dcc.Graph(id='plot', figure=start_lineplot)],
                width={'size': 10})]),
    html.Br(), html.Br(),
    html.Hr()])


# PART 2 ROW 1 - HISTORICAL DATA FOR A SINGLE DATE - INPUTS, HISTOGRAM, PROBABILITY STATEMENT
layout_part2_row1 = html.Div([
    dbc.Row([
        dbc.Col([
            html.Div('Examine Single Dates in History',
                     style={'font-weight': 'bold', 'font-size': '32px'})])]),
    html.Br(),
    dbc.Row([
        dbc.Col(children=[
            html.Br(),
            html.Div('Select month', style={'font-weight': 'bold', 'font-size': '16px'}),
            month_input,
            html.Br(),
            html.Div('Select day', style={'font-weight': 'bold', 'font-size': '16px'}),
            day_input,
            html.Br(), html.Br(),
            html.Div('Select temperature', style={'font-weight': 'bold', 'font-size': '16px'}),
            temp_input,
            html.Div(f'{degree_sign}C'.rjust(5), style={'font-size': '16px', 'display': 'inline-block'}),
            html.Br(), html.Br()],
            width={'offset': 0, 'size': 2}, align='center',
            style={'border': '4px #073763 solid', 'border-radius': '4px', 'height': '290px'}),
        dbc.Col(dcc.Graph(id='day-hist', figure=start_day_hist), align='bottom'),
        dbc.Col(children=[
            html.Div(id='day-perc-geq',
                     children=[html.P(f'← \n'),  # , style={'font-size': '24px', 'align': 'center'}),
                               html.P(f'{start_day_perc_geq}% of days on record with the date of'
                                      f'{long_months[0]} {1} had a mean temperature of at least'
                                      f'{0}C.')],
                     style={'font-size': '18px', 'border': '4px #073763 solid', 'border-radius': '4px',
                            'height': '290px', 'width': '190px', 'padding': '10px'})],
                width={'offset': 0, 'size': 2},
                align='center')])])


# colors for the three tables in layout_part2_row2
recent_table_color = '#d4e4da'  # greenish
record_min_table_color = '#cacde4'  # bluish
record_max_table_color = '#e4d4d4'  # reddish


# PART 2 ROW 2 - HISTORICAL DATA FOR A SINGLE DATE - RECENT 5, RECORD LOWS, RECORD HIGHS TABLES
layout_part2_row2 = html.Div([
    dbc.Row([
        dbc.Col(children=[
            html.Div(id='day-recent-title', children=['Recent temps on January 1:'],
                     style={'font-size': '15px', 'font-weight': 'bold'}),
            dash_table.DataTable(id='day-last-5yr',
                                 columns=[{'name': c, 'id': c, 'format': {'specifier': '.2f'}} for
                                          c in start_day_recent5.columns],
                                 data=start_day_recent5.to_dict('records'),
                                 style_cell={'textAlign': 'center', 'backgroundColor': recent_table_color,
                                             'border': '1px solid white'})],
            width={'offset': 0, 'size': 3}),
        dbc.Col(children=[
            html.Div(id='day-record-title-min', children=['Record lows on January 1:'],
                     style={'font-size': '15px', 'font-weight': 'bold'}),
            dash_table.DataTable(id='day-records-min',
                                 columns=[{'name': c, 'id': c} for c in start_recs_min.columns],
                                 data=start_recs_min.to_dict('records'),
                                 style_cell={'textAlign': 'center', 'backgroundColor': record_min_table_color,
                                             'border': '1px solid white'})],
            width={'offset': 1, 'size': 3}),
        dbc.Col(children=[
            html.Div(id='day-record-title-max', children=['Record highs on January 1:'],
                     style={'font-size': '15px', 'font-weight': 'bold'}),
            dash_table.DataTable(id='day-records-max',
                                 columns=[{'name': c, 'id': c} for c in start_recs_max.columns],
                                 data=start_recs_max.to_dict('records'),
                                 style_cell={'textAlign': 'center', 'backgroundColor': record_max_table_color,
                                             'border': '1px solid white'})],
            width={'offset': 1, 'size': 3})],
            justify='center'),
    html.Br(), html.Br(), html.Br(),
    html.Hr()])


# PART 3 - COMPARING YEARS
layout_part3 = html.Div([
    dbc.Row([
        dbc.Col([
            html.Div('Compare Multiple Years to All-Time Daily Average',
                     style={'font-weight': 'bold', 'font-size': '32px'})])]),
    html.Br(), html.Br(),
    dbc.Row(children=[
        dbc.Col(children=[
            html.Div('Select up to 5 years for comparison'),
            html.Br(),
            multi_year_input,
            html.Br()],
            width={'offset': 0, 'size': 2}, align='center',
            style={'border': '4px #073763 solid', 'border-radius': '4px', 'height': '290px'}),
        dbc.Col(
            dcc.Graph(id='year-comparison-graph', figure=start_year_comp_graph),
            width={'offset': 0, 'size': 7}, align='center'),
        dbc.Col(
            dash_table.DataTable(id='year-comparison-table',
                                 columns=[{'name': c, 'id': c} for c in start_year_comp_table],
                                 data=start_year_comp_table.to_dict('records'),
                                 style_cell={'textAlign': 'center', 'backgroundColor': 'white',
                                             'border': '1px solid white'},
                                 # structured as [cond1, cond2] + [list comp of conditionals]
                                 style_data_conditional=[
                                     # turn off click-highlighting
                                     {'if': {'state': 'selected'},
                                      'backgroundColor': 'inherit !important',
                                      'border': 'inherit !important'},
                                     # set All Time row to yellow
                                     {'if': {'row_index': 0},
                                      'backgroundColor': '#DAD4D3'},
                                     # set all other rows to a lighter grey than the header
                                     ] + [{'if': {'row_index': i+1},
                                           'background-color': plot.light_colors[i]} for i in range(5)]),
            width={'offset': 1, 'size': 2})],
            justify='left'),
    html.Br(), html.Br(), html.Br(), html.Hr()])



# PART 4 - "ABOUT" SECTION
layout_part4 = html.Div([
    html.Div('Links', style={'font-weight': 'bold', 'font-size': '24px', 'margin-left': '10px'}),
    html.Div("The HadCET data is hosted by the United Kingdom's Meteorological Office "
             "and can be found here:", style={'margin-left': '20px'}),
    html.A("https://www.metoffice.gov.uk/hadobs/hadcet/", href='https://www.metoffice.gov.uk/hadobs/hadcet/',
           target="_blank", style={'margin-left': '30px', "text-decoration": "underline"}),
    html.Br(), html.Br(),
    html.Div('This dashboard was created by Tony Luehrs. You can find all of the code '
             'used to generate this dashboard at my github:', style={'margin-left': '20px'}),
    html.A("https://www.github.com/TonyLuehrs/hadcet", href='https://www.github.com/TonyLuehrs/hadcet',
           target="_blank", style={'margin-left': '30px', "text-decoration": "underline"}),
    html.Br(), html.Br(),

    html.Div('Dataset History and Citation', style={'font-weight': 'bold', 'font-size': '24px', 'margin-left': '10px'}),
    html.Div('Monthly average temperature began being record in 1659.', style={'margin-left': '20px'}),
    html.Div('Daily average temperatures began being recorded on Jan. 1, 1772.', style={'margin-left': '20px'}),
    html.Div('Daily minimum and maximum temperatures began being recorded in 1878.', style={'margin-left': '20px'}),
    html.Br(),
    html.Div('It is important to note that the data assembled in this dataset came from a variety of sources,'
             ' a variety of locations within central England, and in a variety of indoor and outdoor environments.'
             ' For full details on methodologies, see the following paper by Parker, Legg, and Foland:',
             style={'margin-left': '20px'}),
    html.Br(),
    html.A("https://www.metoffice.gov.uk/hadobs/hadcet/Parker_etalIJOC1992_dailyCET.pdf",
           href='https://www.metoffice.gov.uk/hadobs/hadcet/Parker_etalIJOC1992_dailyCET.pdf',
           target="_blank", style={'margin-left': '30px', "text-decoration": "underline"}),
    html.Div('Parker, D.E., T.P. Legg, and C.K. Folland. 1992. A new daily Central England',
             style={'margin-left': '35px'}),
    html.Div('Temperature Series, 1772-1991. Int. J. Clim., Vol 12, pp 317-342',
             style={'margin-left': '35px'}),
    html.Br(), html.Br(), html.Hr()

])



#################
### Callbacks ###
#################



# PART 1 CALLBACK - UPDATE SMOOTHED LINEPLOT OF ONE YEAR'S TEMPERATURES
@app.callback(
    output=Output(component_id='plot', component_property='figure'),
    inputs=[
        Input(component_id='year-input', component_property='value'),
        Input(component_id='window-size-input', component_property='value')])
def update_part1(year, window_size):
    return plot.get_lineplot(year, window_size)



# PART 2 CALLBACK 1 - UPDATE WHICH DAYS CAN BE SELECTED BASED ON THE MONTH SELECTED
@app.callback(
    output=[Output(component_id='day-input', component_property='max'),
            Output(component_id='day-input', component_property='value')],
    inputs=[Input(component_id='month-input', component_property='value'),
            Input(component_id='day-input', component_property='value')])
def update_available_days(month, day):
    # month comes in as, ex, 'feb', but we'll want to use int(2)
    month_num = month_dict[month]
    if day > month_length_dict[month_num]:
        day_value = month_length_dict[month_num]
        day_max = day_value
    else:
        day_value = day
        day_max = month_length_dict[month_num]
    return day_max, day_value

# this simpler version below of the above callback has problems. if the date selected is jan 31, then the month
#  is changed to feb, but there is no feb 31, so pandas lookup fails. so, sometimes changing the month causes us
#  to have to also change the day's *value*, not just its max

# @app.callback(
#     output=Output(component_id='day-input', component_property='max'),
#     inputs=[Input(component_id='month-input', component_property='value')])
# def update_available_days(month):
#     return hadcet.ave_df[hadcet.ave_df['month'] == month_dict[month]]['day'].max()



# PART 2 CALLBACK 2 - UPDATE SINGLE DATE IN HISTORY, TEMP
@app.callback(
    output=[
        Output(component_id='day-hist', component_property='figure'),
        Output(component_id='day-recent-title', component_property='children'),
        Output(component_id='day-last-5yr', component_property='data'),
        Output(component_id='day-perc-geq', component_property='children'),
        Output(component_id='day-record-title-min', component_property='children'),
        Output(component_id='day-record-title-max', component_property='children'),
        Output(component_id='day-records-min', component_property='data'),
        Output(component_id='day-records-max', component_property='data')],
    inputs=[
        Input(component_id='month-input', component_property='value'),
        Input(component_id='day-input', component_property='value'),
        Input(component_id='temp-input', component_property='value')])
def update_part2(month, day, temp):
    day_hist = plot.get_day_hist(month_dict[month], day, temp)
    day_recent_title = f'Recent temps on {long_months[short_months.index(month)]} {day}:'
    day_recent_5yr = hadcet.get_day_prev_5yr(short_months.index(month) + 1, day)
    day_perc_geq = [html.P(f'← \n'),
                    html.P(f'{hadcet.get_perc_geq(short_months.index(month) + 1, day, temp)}% of days on '
                           f'record with the date of {long_months[short_months.index(month)]} {day}'
                           f' had a mean temperature of at least {temp}{degree_sign}C.')]
    day_records_title_min = f'Record lows on {long_months[short_months.index(month)]} {day}:'
    day_records_title_max = f'Record highs on {long_months[short_months.index(month)]} {day}:'
    day_records_min, day_records_max = hadcet.get_day_records(short_months.index(month) + 1, day)
    return day_hist, day_recent_title, day_recent_5yr.to_dict('records'), day_perc_geq, \
           day_records_title_min, day_records_title_max, \
           day_records_min.to_dict('records'), day_records_max.to_dict('records')



# PART 3 CALLBACK 1 - MAX OF 5 YEARS SELECTED IN MULTI-YEAR INPUT
@app.callback(
    output=Output(component_id='multi-year-input', component_property='options'),
    inputs=[
        Input(component_id='multi-year-input', component_property='value')])
def update_part3_options(multi_year):
    if len(multi_year) == 5:
        return [{'label': str(yr), 'value': str(yr)} for yr in multi_year]
    else:
        return [{'label': str(yr), 'value': str(yr)} for yr in range(2020, 1771, -1) if yr not in multi_year]



# PART 3 CALLBACK 2 - UPDATE MULTI-SELECT YEAR TABLE, GRAPH
@app.callback(
    output=[Output(component_id='year-comparison-table', component_property='data'),
            Output(component_id='year-comparison-graph', component_property='figure')],
    inputs=[
        Input(component_id='multi-year-input', component_property='value')])
def update_part3(multi_year):
    years = [int(year) for year in multi_year]
    if years == 0:
        return start_year_comp_table.to_dict('records')
    year_comparison_table = hadcet.get_year_comp_table(years)
    year_comparison_graph = plot.get_year_comparison_graph(years, 29)
    return year_comparison_table.to_dict('records'), year_comparison_graph


###########################################
### Build overall layout and deploy app ###
###########################################


# introduction paragraph
description = html.Div('The HadCET (Hadley Center Central England Temperature) is the longest running daily '
                       'temperature record in the world. Monthly temperature data began being collected in 1659, '
                       'and daily temperatures began being recorded on Jan. 1, 1772.',
                       style={'font-size': '16px'})

# total intro (including above description paragraph)
intro = html.Div([html.Br(),
                  html.H1('HADCET Temperature Data'), html.Br(),
                  description, html.Br(), html.Br(),
                  html.Hr()])

# overall app layout
app.layout = dbc.Container(children=[
    intro, html.Br(), html.Br(),
    layout_part1, html.Br(), html.Br(),
    layout_part2_row1, html.Br(),
    layout_part2_row2, html.Br(), html.Br(),
    layout_part3, html.Br(), html.Br(),
    layout_part4, html.Br(), html.Br()
])

if __name__ == '__main__':
    app.run_server(debug=True)
