from dash import Dash, html, dcc, callback, Output, Input, State
import plotly.express as px
import pandas as pd
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from dash import ctx

df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminder_unfiltered.csv')

app = Dash(__name__)

# Получаем числовые колонки для выбора осей
numeric_columns = df.select_dtypes(include='number').columns.tolist()

app.layout = html.Div([
    html.H1(children='Dash', style={'textAlign':'center'}),
    
    # Фильтры и управляющие элементы
    html.Div([
        html.Div([
            html.Label('Select Countries:'),
            dcc.Dropdown(
                id='country-dropdown',
                options=[{'label': country, 'value': country} for country in df['country'].unique()],
                value=['Canada', 'United States'],
                multi=True
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            html.Label('Select Y-axis for Line Chart:'),
            dcc.Dropdown(
                id='y-axis-dropdown',
                options=[{'label': col, 'value': col} for col in numeric_columns],
                value='pop'
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            html.Label('Select Year:'),
            dcc.RangeSlider(
                id='year-slider',
                min=df['year'].min(),
                max=df['year'].max(),
                value=[df['year'].min(), df['year'].max()],
                marks={str(year): str(year) for year in range(df['year'].min(), df['year'].max()+1, 10)},
                step=1
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            html.Label('Select Continent:'),
            dcc.Dropdown(
                id='continent-dropdown',
                options=[{'label': continent, 'value': continent} for continent in df['continent'].unique()],
                value=None,
                multi=True
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
    ], style={'border': '1px solid #ddd', 'borderRadius': '5px', 'padding': '10px', 'marginBottom': '20px'}),
    
    # Графики в первой строке
    html.Div([
        html.Div([
            dcc.Graph(id='line-chart')
        ], style={'width': '48%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='bubble-chart')
        ], style={'width': '48%', 'display': 'inline-block', 'float': 'right'}),
    ]),
    
    # Управление для пузырьковой диаграммы
    html.Div([
        html.Div([
            html.Label('X-axis for Bubble Chart:'),
            dcc.Dropdown(
                id='bubble-x-dropdown',
                options=[{'label': col, 'value': col} for col in numeric_columns],
                value='gdpPercap'
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            html.Label('Y-axis for Bubble Chart:'),
            dcc.Dropdown(
                id='bubble-y-dropdown',
                options=[{'label': col, 'value': col} for col in numeric_columns],
                value='lifeExp'
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            html.Label('Size for Bubble Chart:'),
            dcc.Dropdown(
                id='bubble-size-dropdown',
                options=[{'label': col, 'value': col} for col in numeric_columns],
                value='pop'
            )
        ], style={'width': '30%', 'display': 'inline-block', 'padding': '10px'}),
    ], style={'border': '1px solid #ddd', 'borderRadius': '5px', 'padding': '10px', 'marginBottom': '20px'}),
    
    # Графики во второй строке
    html.Div([
        html.Div([
            dcc.Graph(id='top-countries-chart')
        ], style={'width': '48%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='pie-chart')
        ], style={'width': '48%', 'display': 'inline-block', 'float': 'right'}),
    ]),
    
    # Скрытые div для хранения состояния
    html.Div(id='selected-data', style={'display': 'none'}),
    dcc.Store(id='filter-store')
])

# Обновление линейного графика
@app.callback(
    Output('line-chart', 'figure'),
    [Input('country-dropdown', 'value'),
     Input('y-axis-dropdown', 'value'),
     Input('year-slider', 'value'),
     Input('continent-dropdown', 'value'),
     Input('bubble-chart', 'selectedData'),
     Input('top-countries-chart', 'selectedData')]
)
def update_line_chart(selected_countries, y_axis, years, selected_continents, bubble_selected, bar_selected):
    dff = df.copy()
    
    # Применяем фильтры по годам
    if years:
        dff = dff[(dff['year'] >= years[0]) & (dff['year'] <= years[1])]
    
    # Применяем фильтры по континентам
    if selected_continents:
        dff = dff[dff['continent'].isin(selected_continents)]
    
    # Определяем выбранные страны из разных источников
    countries_to_show = set()
    
    if selected_countries:
        countries_to_show.update(selected_countries)
    
    # Обработка выбранных точек с пузырьковой диаграммы
    if bubble_selected and ctx.triggered_id == 'bubble-chart':
        bubble_countries = [point['customdata'][0] for point in bubble_selected['points']]
        countries_to_show = set(bubble_countries)
    
    # Обработка выбранных столбцов с барчарта
    if bar_selected and ctx.triggered_id == 'top-countries-chart':
        bar_countries = [point['x'] for point in bar_selected['points']]
        countries_to_show = set(bar_countries)
    
    if countries_to_show:
        dff = dff[dff['country'].isin(countries_to_show)]
    
    fig = px.line(dff, x='year', y=y_axis, color='country',
                  title=f'Comparison of {y_axis} over time',
                  custom_data=['country'])
    
    fig.update_layout(
        transition_duration=500,
        clickmode='event+select'
    )
    return fig

# Обновление пузырьковой диаграммы
@app.callback(
    Output('bubble-chart', 'figure'),
    [Input('year-slider', 'value'),
     Input('bubble-x-dropdown', 'value'),
     Input('bubble-y-dropdown', 'value'),
     Input('bubble-size-dropdown', 'value'),
     Input('continent-dropdown', 'value'),
     Input('line-chart', 'selectedData'),
     Input('top-countries-chart', 'selectedData'),
     Input('country-dropdown', 'value')]
)
def update_bubble_chart(years, x_axis, y_axis, size, selected_continents, 
                       line_selected, bar_selected, dropdown_countries):
    dff = df.copy()
    
    # Применяем фильтр по году (берем последний год из диапазона)
    if years:
        dff = dff[dff['year'] == years[1]]
    
    # Применяем фильтры по континентам
    if selected_continents:
        dff = dff[dff['continent'].isin(selected_continents)]
    
    # Создаем базовую фигуру
    fig = px.scatter(dff, x=x_axis, y=y_axis, size=size, color='continent',
                    hover_name='country', log_x=True, size_max=60,
                    custom_data=['country'],
                    title=f'Bubble Chart for {years[1]}')
    
    # Определяем выбранные страны
    selected_points = []
    
    if dropdown_countries and ctx.triggered_id == 'country-dropdown':
        selected_points = [i for i, country in enumerate(dff['country']) 
                         if country in dropdown_countries]
    elif line_selected and ctx.triggered_id == 'line-chart':
        selected_countries = [point['customdata'][0] for point in line_selected['points']]
        selected_points = [i for i, country in enumerate(dff['country']) 
                         if country in selected_countries]
    elif bar_selected and ctx.triggered_id == 'top-countries-chart':
        selected_countries = [point['x'] for point in bar_selected['points']]
        selected_points = [i for i, country in enumerate(dff['country']) 
                         if country in selected_countries]
    
    if selected_points:
        for trace in fig.data:
            trace.selectedpoints = selected_points
    
    fig.update_layout(
        clickmode='event+select',
        transition_duration=500
    )
    return fig

# Обновление графика топ-15 стран
@app.callback(
    Output('top-countries-chart', 'figure'),
    [Input('year-slider', 'value'),
     Input('continent-dropdown', 'value'),
     Input('line-chart', 'selectedData'),
     Input('bubble-chart', 'selectedData'),
     Input('country-dropdown', 'value')]
)
def update_top_countries_chart(years, selected_continents, line_selected, 
                             bubble_selected, dropdown_countries):
    dff = df.copy()
    
    # Применяем фильтр по году (берем последний год из диапазона)
    if years:
        dff = dff[dff['year'] == years[1]]
    
    # Применяем фильтры по континентам
    if selected_continents:
        dff = dff[dff['continent'].isin(selected_continents)]
    
    dff = dff.nlargest(15, 'pop')
    
    fig = px.bar(dff, x='country', y='pop', color='continent',
                 title=f'Top 15 Countries by Population in {years[1]}',
                 custom_data=['country'])
    
    # Определяем выбранные страны
    selected_points = []
    
    if dropdown_countries and ctx.triggered_id == 'country-dropdown':
        selected_points = [i for i, country in enumerate(dff['country']) 
                         if country in dropdown_countries]
    elif line_selected and ctx.triggered_id == 'line-chart':
        selected_countries = [point['customdata'][0] for point in line_selected['points']]
        selected_points = [i for i, country in enumerate(dff['country']) 
                         if country in selected_countries]
    elif bubble_selected and ctx.triggered_id == 'bubble-chart':
        selected_countries = [point['customdata'][0] for point in bubble_selected['points']]
        selected_points = [i for i, country in enumerate(dff['country']) 
                         if country in selected_countries]
    
    if selected_points:
        for trace in fig.data:
            trace.selectedpoints = selected_points
    
    fig.update_layout(
        xaxis={'categoryorder': 'total descending'},
        clickmode='event+select',
        transition_duration=500
    )
    return fig

# Обновление круговой диаграммы
@app.callback(
    Output('pie-chart', 'figure'),
    [Input('year-slider', 'value'),
     Input('continent-dropdown', 'value')]
)
def update_pie_chart(years, selected_continents):
    dff = df.copy()
    
    # Применяем фильтр по году (берем последний год из диапазона)
    if years:
        dff = dff[dff['year'] == years[1]]
    
    # Применяем фильтры по континентам
    if selected_continents:
        dff = dff[dff['continent'].isin(selected_continents)]
    
    continent_pop = dff.groupby('continent')['pop'].sum().reset_index()
    
    fig = px.pie(continent_pop, values='pop', names='continent',
                 title=f'Population by Continent in {years[1]}')
    
    fig.update_layout(transition_duration=500)
    return fig

if __name__ == '__main__':
    app.run(debug=True)