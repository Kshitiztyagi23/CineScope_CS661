import dash
from dash import dcc, html, Input, Output, callback, State
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pycountry

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Movie Data Dashboard"

# Load data
try:
    df = pd.read_csv('TMDB_movie_dataset_v11.csv')
except FileNotFoundError:
    df = pd.DataFrame()

# Plot functions from notebook
def create_correlation_heatmap(df):
    """Cell 9: Correlation heatmap"""
    try:
        df_clean = df[
            (df['vote_average'].notna()) &
            (df['vote_count'].notna()) &
            (df['revenue'].notna()) &
            (df['budget'].notna()) &
            (df['popularity'].notna()) &
            (df['vote_count'] > 0) &
            (df['budget'] > 0) &
            (df['revenue'] > 0)
        ]
        
        numeric_cols = ['vote_average', 'vote_count', 'budget', 'revenue', 'popularity']
        df_numeric = df_clean[numeric_cols].dropna()
        corr = df_numeric.corr().round(2)
        
        fig = px.imshow(
            corr,
            text_auto=True,
            color_continuous_scale='YlGnBu',
            zmin=-1,
            zmax=1,
            title='Interactive Correlation Heatmap'
        )
        fig.update_layout(margin=dict(l=40, r=40, t=50, b=40))
        return fig
    except:
        return {}

def create_budget_revenue_bar(df):
    """Cell 13: Budget vs Revenue bar chart"""
    try:
        df_filtered = df[(df['budget'] > 1e5) & (df['revenue'] > 1e5)].copy()
        
        bins = [0, 1e6, 1e7, 5e7, 1e8, 2e8, 5e8, 1e9]
        labels = ['<1M', '1M–10M', '10M–50M', '50M–100M', '100M–200M', '200M–500M', '>500M']
        df_filtered['budget_range'] = pd.cut(df_filtered['budget'], bins=bins, labels=labels)
        
        grouped = df_filtered.groupby('budget_range').agg(
            average_revenue=('revenue', 'mean'),
            movie_count=('budget', 'count')
        ).reset_index()
        
        fig = px.bar(
            grouped,
            x='budget_range',
            y='average_revenue',
            hover_data={'movie_count': True, 'average_revenue': ':.2f'},
            labels={'average_revenue': 'Avg Revenue (USD)', 'budget_range': 'Budget Range'},
            title='Average Revenue by Budget Range',
            color='average_revenue',
            color_continuous_scale='viridis'
        )
        return fig
    except:
        return {}

def create_genre_treemap(df):
    """Cell 14: Genre revenue treemap"""
    try:
        df_clean = df[df['genres'].notna() & (df['genres'] != '')].copy()
        df_clean['genre_list'] = df_clean['genres'].apply(lambda x: [g.strip() for g in x.split(',')])
        
        df_exploded = df_clean.explode('genre_list')
        df_exploded = df_exploded[df_exploded['revenue'] > 0]
        
        genre_revenue = (
            df_exploded.groupby('genre_list')['revenue']
            .sum()
            .reset_index()
            .rename(columns={'genre_list': 'genre'})
            .sort_values(by='revenue', ascending=False)
        )
        
        fig = px.treemap(
            genre_revenue,
            path=['genre'],
            values='revenue',
            title='Total Revenue Share by Genre',
            color='revenue',
            color_continuous_scale='viridis'
        )
        return fig
    except:
        return {}

def create_budget_revenue_scatter(df):
    """Cell 15: Budget vs Revenue scatter plot"""
    try:
        df_filtered = df[(df['budget'] > 0) & (df['revenue'] > 0)]
        
        fig = px.scatter(
            df_filtered, 
            x='budget', 
            y='revenue',
            title='Budget vs Revenue',
            labels={'budget': 'Budget (log scale)', 'revenue': 'Revenue (log scale)'},
            opacity=0.5
        )
        fig.update_xaxes(type="log")
        fig.update_yaxes(type="log")
        return fig
    except:
        return {}

def create_genre_sunburst(df):
    """Cell 16: Year-wise genre sunburst"""
    try:
        df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
        df['year'] = df['release_date'].dt.year
        df = df[df['year'] >= 2020]
        df = df[df['year'] <= 2023]
        
        df_cleaned = df.dropna(subset=['year', 'genres']).copy()
        df_cleaned['year'] = df_cleaned['year'].astype(int)
        df_cleaned['genre_list'] = df_cleaned['genres'].apply(lambda x: [g.strip() for g in x.split(',')])
        
        df_exploded = df_cleaned.explode('genre_list')
        top_genres = ['Comedy', 'Horror', 'Animation', 'Thriller', 'Romance', 'Action']
        df_exploded = df_exploded[df_exploded['genre_list'].isin(top_genres)]
        
        genre_counts = df_exploded.groupby(['year', 'genre_list']).size().reset_index(name='count')
        
        fig = px.sunburst(
            genre_counts,
            path=['year', 'genre_list'],
            values='count',
            title='Year-wise Genre Evolution (2020-2023)',
            color='count',
            color_continuous_scale='viridis'
        )
        return fig
    except:
        return {}

def create_country_genre_pie(df, genre=None):
    """Cell 7: Country contribution to genres"""
    try:
        selected_countries = [
            'United States of America', 'United Kingdom', 'France', 
            'India', 'Germany', 'Canada', 'China'
        ]
        
        df_clean = df[df['genres'].notna() & df['production_countries'].notna()]
        df_clean['genres_list'] = df_clean['genres'].apply(lambda x: [g.strip() for g in x.split(',')])
        df_clean['country_list'] = df_clean['production_countries'].apply(lambda x: [c.strip() for c in x.split(',')])
        
        df_exploded = df_clean.explode('genres_list').explode('country_list')
        df_exploded = df_exploded[df_exploded['country_list'].isin(selected_countries)]
        
        genre_country_counts = df_exploded.groupby(['genres_list', 'country_list']).size().reset_index(name='count')
        
        if genre and genre != 'all':
            genre_data = genre_country_counts[genre_country_counts['genres_list'] == genre]
        else:
            # Show first available genre
            genre = genre_country_counts['genres_list'].iloc[0] if not genre_country_counts.empty else 'Action'
            genre_data = genre_country_counts[genre_country_counts['genres_list'] == genre]
        
        if genre_data.empty:
            return {}
            
        total = genre_data['count'].sum()
        genre_data['percent'] = 100 * genre_data['count'] / total
        
        fig = px.pie(
            genre_data,
            names='country_list',
            values='percent',
            title=f"Top 7 Country Contribution to '{genre}' Genre",
            hover_data=['count'],
            color_discrete_sequence=px.colors.sequential.Viridis
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        return fig
    except:
        return {}

def create_choropleth_map(df):
    """Interactive global movie production choropleth"""
    try:
        # Preprocess data
        df1 = df.copy()
        df1 = df1[df1['production_countries'].notna()]
        df1 = df1[df1['production_countries'].str.strip() != '']
        
        df1['production_countries'] = df1['production_countries'].str.split(',\s*')
        df1['genres'] = df1['genres'].str.split(',\s*')
        df1 = df1.explode('production_countries').explode('genres')
        df1['production_countries'] = df1['production_countries'].str.strip()
        df1['genres'] = df1['genres'].str.strip()
        
        def get_iso_alpha3_enhanced(country_name):
            manual_mapping = {
                'United States': 'USA', 'United States of America': 'USA',
                'United Kingdom': 'GBR', 'UK': 'GBR',
                'Russia': 'RUS', 'Russian Federation': 'RUS',
                'South Korea': 'KOR', 'Korea, Republic of': 'KOR',
                'North Korea': 'PRK', 'Korea, Democratic People\'s Republic of': 'PRK',
                'Czech Republic': 'CZE', 'Czechia': 'CZE',
                'Iran': 'IRN', 'Iran, Islamic Republic of': 'IRN',
                'Venezuela': 'VEN', 'Venezuela, Bolivarian Republic of': 'VEN',
                'Bolivia': 'BOL', 'Bolivia, Plurinational State of': 'BOL',
                'Taiwan': 'TWN', 'Taiwan, Province of China': 'TWN',
                'Moldova': 'MDA', 'Moldova, Republic of': 'MDA',
                'Vietnam': 'VNM', 'Viet Nam': 'VNM',
                'Macedonia': 'MKD', 'North Macedonia': 'MKD',
                'The Former Yugoslav Republic of Macedonia': 'MKD'
            }
            if country_name in manual_mapping:
                return manual_mapping[country_name]
            try:
                return pycountry.countries.lookup(country_name).alpha_3
            except:
                return None
        
        # Summary tables
        summary = df1.groupby('production_countries').agg(movie_count=('title', 'count')).reset_index()
        summary['iso_alpha'] = summary['production_countries'].apply(get_iso_alpha3_enhanced)
        summary = summary.dropna(subset=['iso_alpha'])
        summary['log_movie_count'] = np.log10(summary['movie_count'] + 1)
        
        fig = px.choropleth(
            summary,
            locations="iso_alpha",
            color="log_movie_count",
            hover_name="production_countries",
            color_continuous_scale="plasma",
            labels={'log_movie_count': 'Log₁₀(Movies + 1)'},
            title="Global Movie Production"
        )
        fig.update_traces(
            hovertemplate="<b>%{hovertext}</b><br><br>" +
                          "🎬 Movies Produced: <b>%{customdata[0]:,}</b><br>" +
                          "📈 Log Scale: %{z:.2f}<extra></extra>",
            customdata=summary[['movie_count']].values
        )
        fig.update_layout(
            geo=dict(
                showframe=False,
                showcoastlines=True,
                projection_type='natural earth',
                landcolor="rgb(243,243,243)"
            ),
            margin=dict(t=60, b=20, l=10, r=10),
            coloraxis_colorbar=dict(
                title="Legend",
                tickvals=[0, 1, 2, 3, 4],
                ticktext=["1", "10", "100", "1K", "10K"]
            ),
            height=500
        )
        return fig
    except:
        return {}

# App layout
app.layout = html.Div([
    html.H1("🎬 Movie Data Dashboard", style={'textAlign': 'center', 'marginBottom': '30px'}),
    
    html.Div([
        html.H3(f"Total Movies: {len(df)}", style={'textAlign': 'center'})
    ], style={'marginBottom': '30px'}),
    
    html.Div([
        html.Label("Select Tab:"),
        dcc.Dropdown(
            id='tab-selector',
            options=[
                {'label': '📊 Overview', 'value': 'overview'},
                {'label': '🎭 Genre Analysis', 'value': 'genre'},
                {'label': '🌍 Country Analysis', 'value': 'country'},
                {'label': '🏢 Company Analysis', 'value': 'company'}
            ],
            value='overview',
            style={'width': '300px'}
        )
    ], style={'marginBottom': '20px'}),
    
    html.Div(id='analysis-controls'),
    html.Div(id='main-content')
])

# Callbacks
@callback(
    Output('analysis-controls', 'children'),
    Input('tab-selector', 'value')
)
def update_controls(selected_tab):
    if selected_tab == 'genre':
        return html.Div([
            html.Label("Select Genre:"),
            html.P("Genre selection will be added here")
        ])
    elif selected_tab == 'country':
        return html.Div([
            html.Label("Select Country:"),
            html.P("Country selection will be added here")
        ])
    elif selected_tab == 'company':
        return html.Div([
            html.Label("Select Company:"),
            html.P("Company selection will be added here")
        ])
    return html.Div()

@callback(
    Output('main-content', 'children'),
    [Input('tab-selector', 'value')],
    prevent_initial_call=False
)
def update_content(selected_tab):
    if selected_tab == 'overview':
        return html.Div([
            html.H2("📊 Overview"),
            html.Div([
                html.Div([
                    dcc.Graph(figure=create_correlation_heatmap(df))
                ], style={'width': '50%', 'display': 'inline-block'}),
                html.Div([
                    dcc.Graph(figure=create_budget_revenue_scatter(df))
                ], style={'width': '50%', 'display': 'inline-block'})
            ]),
            html.Div([
                dcc.Graph(figure=create_genre_sunburst(df))
            ])
        ])
    elif selected_tab == 'genre':
        return html.Div([
            html.H2("🎭 Genre Analysis"),
            html.Div([
                dcc.Graph(figure=create_budget_revenue_bar(df))
            ]),
            html.P("Additional genre-specific analysis will be added here")
        ])
    elif selected_tab == 'country':
        return html.Div([
            html.H2("🌍 Country Analysis"),
            html.Div([
                dcc.Graph(figure=create_choropleth_map(df))
            ], style={'marginBottom': '20px'}),
            html.Div([
                html.Div([
                    dcc.Graph(figure=create_country_genre_pie(df))
                ], style={'width': '50%', 'display': 'inline-block'}),
                html.Div([
                    dcc.Graph(figure=create_genre_treemap(df))
                ], style={'width': '50%', 'display': 'inline-block'})
            ])
        ])
    elif selected_tab == 'company':
        return html.Div([
            html.H2("🏢 Company Analysis"),
            html.P("Company analysis plots will be added here")
        ])
    return html.Div("Select a tab")

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)
