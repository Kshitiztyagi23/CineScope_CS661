import dash
from dash import dcc, html, Input, Output, callback, State
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pycountry

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Movie Data Dashboard"

# Dark theme styles
dark_theme = {
    'backgroundColor': '#1e1e1e',
    'color': '#ffffff',
    'fontFamily': 'Arial, sans-serif'
}

plot_dark_theme = {
    'paper_bgcolor': '#2d2d2d',
    'plot_bgcolor': '#2d2d2d',
    'font_color': '#ffffff'
}

# Light theme styles
light_theme = {
    'backgroundColor': '#ffffff',
    'color': '#000000',
    'fontFamily': 'Arial, sans-serif'
}

plot_light_theme = {
    'paper_bgcolor': '#ffffff',
    'plot_bgcolor': '#ffffff',
    'font_color': '#000000'
}

# Global theme state
current_theme = 'dark'

# Individual plot theme states
plot_themes = {
    'correlation_heatmap': 'dark',
    'budget_revenue_bar': 'dark',
    'genre_treemap': 'dark',
    'budget_revenue_scatter': 'dark',
    'genre_sunburst': 'dark',
    'country_genre_pie': 'dark',
    'choropleth_map': 'dark',
    'top10_movies': 'dark'
}

def get_current_theme():
    return dark_theme if current_theme == 'dark' else light_theme

def get_current_plot_theme():
    return plot_dark_theme if current_theme == 'dark' else plot_light_theme

def get_plot_theme(plot_name):
    """Get theme for a specific plot"""
    return plot_dark_theme if plot_themes.get(plot_name, 'dark') == 'dark' else plot_light_theme

def create_plot_toggle_button(plot_id):
    """Create a theme toggle button for a specific plot"""
    current_plot_theme = plot_themes.get(plot_id, 'dark')
    icon = "☀️" if current_plot_theme == 'dark' else "🌙"
    
    return html.Button(
        icon,
        id=f'{plot_id}-theme-toggle',
        n_clicks=0,
        style={
            'position': 'absolute',
            'top': '10px',
            'right': '10px',
            'fontSize': '16px',
            'border': '1px solid #ccc',
            'borderRadius': '50%',
            'width': '30px',
            'height': '30px',
            'backgroundColor': '#2d2d2d' if current_plot_theme == 'dark' else '#f0f0f0',
            'color': '#ffffff' if current_plot_theme == 'dark' else '#000000',
            'cursor': 'pointer',
            'zIndex': 5
        },
        title="Toggle plot theme"
    )

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
        fig.update_layout(
            margin=dict(l=40, r=40, t=50, b=40),
            paper_bgcolor=get_plot_theme('correlation_heatmap')['paper_bgcolor'],
            plot_bgcolor=get_plot_theme('correlation_heatmap')['plot_bgcolor'],
            font_color=get_plot_theme('correlation_heatmap')['font_color']
        )
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
        fig.update_layout(
            paper_bgcolor=get_plot_theme('budget_revenue_bar')['paper_bgcolor'],
            plot_bgcolor=get_plot_theme('budget_revenue_bar')['plot_bgcolor'],
            font_color=get_plot_theme('budget_revenue_bar')['font_color']
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
        fig.update_layout(
            paper_bgcolor=get_plot_theme('genre_treemap')['paper_bgcolor'],
            plot_bgcolor=get_plot_theme('genre_treemap')['plot_bgcolor'],
            font_color=get_plot_theme('genre_treemap')['font_color']
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
        fig.update_layout(
            paper_bgcolor=get_plot_theme('budget_revenue_scatter')['paper_bgcolor'],
            plot_bgcolor=get_plot_theme('budget_revenue_scatter')['plot_bgcolor'],
            font_color=get_plot_theme('budget_revenue_scatter')['font_color']
        )
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
            color_continuous_scale='inferno'
        )
        fig.update_layout(
            paper_bgcolor=get_plot_theme('genre_sunburst')['paper_bgcolor'],
            plot_bgcolor=get_plot_theme('genre_sunburst')['plot_bgcolor'],
            font_color=get_plot_theme('genre_sunburst')['font_color']
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
        fig.update_layout(
            paper_bgcolor=get_plot_theme('country_genre_pie')['paper_bgcolor'],
            plot_bgcolor=get_plot_theme('country_genre_pie')['plot_bgcolor'],
            font_color=get_plot_theme('country_genre_pie')['font_color']
        )
        return fig
    except:
        return {}

# Global variables for choropleth data
choropleth_data = {}

def create_choropleth_map(df):
    """Interactive global movie production choropleth"""
    global choropleth_data
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
        country_genre = df1.groupby(['production_countries', 'genres']).size().reset_index(name='count')
        summary = df1.groupby('production_countries').agg(movie_count=('title', 'count')).reset_index()
        summary['iso_alpha'] = summary['production_countries'].apply(get_iso_alpha3_enhanced)
        summary = summary.dropna(subset=['iso_alpha'])
        summary['log_movie_count'] = np.log10(summary['movie_count'] + 1)
        
        # Store data globally for callback access
        choropleth_data = {
            'summary': summary,
            'country_genre': country_genre
        }
        
        fig = px.choropleth(
            summary,
            locations="iso_alpha",
            color="log_movie_count",
            hover_name="production_countries",
            color_continuous_scale="plasma",
            labels={'log_movie_count': 'Log₁₀(Movies + 1)'},
            title="Global Movie Production (Click on countries for genre breakdown)"
        )
        fig.update_traces(
            hovertemplate="<b>%{hovertext}</b><br><br>" +
                          "🎬 Movies Produced: <b>%{customdata[0]:,}</b><br>",
            customdata=summary[['movie_count']].values
        )
        fig.update_layout(
            geo=dict(
                showframe=False,
                showcoastlines=True,
                projection_type='natural earth',
                landcolor="rgb(50,50,50)" if plot_themes.get('choropleth_map', 'dark') == 'dark' else "rgb(243,243,243)",
                bgcolor=get_plot_theme('choropleth_map')['paper_bgcolor']
            ),
            margin=dict(t=60, b=20, l=10, r=10),
            coloraxis_colorbar=dict(
                title="Legend",
                tickvals=[0, 1, 2, 3, 4],
                ticktext=["1", "10", "100", "1K", "10K"]
            ),
            height=600,
            paper_bgcolor=get_plot_theme('choropleth_map')['paper_bgcolor'],
            font_color=get_plot_theme('choropleth_map')['font_color']
        )
        return fig
    except:
        return {}

def create_top10_movies_plot(df, country='United States of America', feature='revenue'):
    """Interactive top 10 movies plot"""
    try:
        # Preprocess data similar to the original
        df_processed = df.copy()
        df_processed = df_processed[df_processed['title'] != 'IPL 2025']
        df_processed = df_processed[df_processed['title'] != 'TikTok Rizz Party']
        df_processed = df_processed.dropna(subset=["title", "production_countries"])
        
        # Expand production countries
        df_processed['production_countries'] = df_processed['production_countries'].str.split(',\s*')
        df_processed = df_processed.explode('production_countries')
        df_processed['production_countries'] = df_processed['production_countries'].str.strip()
        
        # Compute ROI
        df_processed['roi'] = df_processed['revenue'] / df_processed['budget']
        df_processed.replace([np.inf, -np.inf], np.nan, inplace=True)
        df_processed = df_processed.dropna(subset=['roi'])
        
        # Features mapping
        features = {
            'revenue': '💰 Revenue',
            'budget': '📦 Budget',
            'roi': '📈 ROI',
            'popularity': '🔥 Popularity'
        }
        
        label = features.get(feature, feature)
        
        # Filter data for the selected country
        data = df_processed[df_processed['production_countries'] == country].dropna(subset=[feature])
        top10 = data.sort_values(by=feature, ascending=False).head(10)
        
        if top10.empty:
            return px.bar(title=f"No data available for {country} - {label}")
        
        # Create the plot
        color_range = (5, 9) if feature == 'vote_average' else None
        color_scale = 'plasma' if feature == 'vote_average' else 'viridis'
        
        fig = px.bar(
            top10,
            y='title',
            x=feature,
            color=feature,
            orientation='h',
            color_continuous_scale=color_scale,
            range_color=color_range,
            title=f"{label} - Top 10 Movies in {country}",
            labels={feature: label, 'title': 'Movie'}
        )
        
        fig.update_layout(
            yaxis=dict(autorange='reversed'),
            xaxis_title=label,
            yaxis_title=None,
            title_font=dict(size=18, family='Arial'),
            coloraxis_colorbar=dict(title=label),
            paper_bgcolor=get_plot_theme('top10_movies')['paper_bgcolor'],
            plot_bgcolor=get_plot_theme('top10_movies')['plot_bgcolor'],
            font_color=get_plot_theme('top10_movies')['font_color'],
            height=500
        )
        
        return fig
    except Exception as e:
        return px.bar(title="Error creating plot")

# App layout
app.layout = html.Div([
    html.Div([
        html.H1("🎬 CineScope", 
                style={
                    'textAlign': 'center', 
                    'marginBottom': '30px',
                    'color': get_current_theme()['color'],
                    'display': 'inline-block',
                    'width': '85%'
                }),
        html.Button(
            "🌙", 
            id='theme-toggle',
            n_clicks=0,
            style={
                'position': 'absolute',
                'top': '20px',
                'right': '20px',
                'fontSize': '24px',
                'border': '2px solid #555',
                'borderRadius': '50%',
                'width': '50px',
                'height': '50px',
                'backgroundColor': '#2d2d2d' if current_theme == 'dark' else '#f0f0f0',
                'color': '#ffffff' if current_theme == 'dark' else '#000000',
                'cursor': 'pointer',
                'transition': 'all 0.3s ease'
            },
            title="Toggle theme"
        )
    ], style={'position': 'relative'}),
    
    html.Div([
        html.H3(f"Total Movies: {len(df)}", 
               style={
                   'textAlign': 'center',
                   'color': get_current_theme()['color']
               })
    ], style={'marginBottom': '30px'}),
    
    html.Div([
        html.Label("Select Tab:", 
                  style={
                      'color': get_current_theme()['color'],
                      'fontSize': '16px',
                      'marginBottom': '10px',
                      'display': 'block'
                  }),
        html.Div([
            dcc.Slider(
                id='tab-slider',
                min=0,
                max=3,
                step=1,
                value=0,
                marks={
                    0: {'label': '📊 Overview', 'style': {'color': get_current_theme()['color']}},
                    1: {'label': '🎭 Genre Analysis', 'style': {'color': get_current_theme()['color']}},
                    2: {'label': '🌍 Country Analysis', 'style': {'color': get_current_theme()['color']}},
                    3: {'label': '🏢 Company Analysis', 'style': {'color': get_current_theme()['color']}}
                },
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={'marginBottom': '40px', 'paddingLeft': '20px', 'paddingRight': '20px'})
    ], style={'marginBottom': '20px'}),
    
    html.Div(id='analysis-controls'),
    html.Div(id='main-content')
], style={
    'backgroundColor': get_current_theme()['backgroundColor'],
    'minHeight': '100vh',
    'padding': '20px',
    'fontFamily': get_current_theme()['fontFamily']
}, id='main-layout')

# Callbacks
# Individual plot theme toggle callbacks
@callback(
    Output('correlation-heatmap', 'figure'),
    Output('correlation_heatmap-theme-toggle', 'children'),
    Output('correlation_heatmap-theme-toggle', 'style'),
    Input('correlation_heatmap-theme-toggle', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_correlation_heatmap_theme(n_clicks):
    global plot_themes
    if n_clicks > 0:
        plot_themes['correlation_heatmap'] = 'light' if plot_themes['correlation_heatmap'] == 'dark' else 'dark'
    
    icon = "☀️" if plot_themes['correlation_heatmap'] == 'dark' else "🌙"
    button_style = {
        'position': 'absolute',
        'top': '10px',
        'right': '10px',
        'fontSize': '16px',
        'border': '1px solid #ccc',
        'borderRadius': '50%',
        'width': '30px',
        'height': '30px',
        'backgroundColor': '#2d2d2d' if plot_themes['correlation_heatmap'] == 'dark' else '#f0f0f0',
        'color': '#ffffff' if plot_themes['correlation_heatmap'] == 'dark' else '#000000',
        'cursor': 'pointer',
        'zIndex': 5
    }
    return create_correlation_heatmap(df), icon, button_style

@callback(
    Output('budget-revenue-scatter', 'figure'),
    Output('budget_revenue_scatter-theme-toggle', 'children'),
    Output('budget_revenue_scatter-theme-toggle', 'style'),
    Input('budget_revenue_scatter-theme-toggle', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_budget_revenue_scatter_theme(n_clicks):
    global plot_themes
    if n_clicks > 0:
        plot_themes['budget_revenue_scatter'] = 'light' if plot_themes['budget_revenue_scatter'] == 'dark' else 'dark'
    
    icon = "☀️" if plot_themes['budget_revenue_scatter'] == 'dark' else "🌙"
    button_style = {
        'position': 'absolute',
        'top': '10px',
        'right': '10px',
        'fontSize': '16px',
        'border': '1px solid #ccc',
        'borderRadius': '50%',
        'width': '30px',
        'height': '30px',
        'backgroundColor': '#2d2d2d' if plot_themes['budget_revenue_scatter'] == 'dark' else '#f0f0f0',
        'color': '#ffffff' if plot_themes['budget_revenue_scatter'] == 'dark' else '#000000',
        'cursor': 'pointer',
        'zIndex': 5
    }
    return create_budget_revenue_scatter(df), icon, button_style

@callback(
    Output('genre-sunburst', 'figure'),
    Output('genre_sunburst-theme-toggle', 'children'),
    Output('genre_sunburst-theme-toggle', 'style'),
    Input('genre_sunburst-theme-toggle', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_genre_sunburst_theme(n_clicks):
    global plot_themes
    if n_clicks > 0:
        plot_themes['genre_sunburst'] = 'light' if plot_themes['genre_sunburst'] == 'dark' else 'dark'
    
    icon = "☀️" if plot_themes['genre_sunburst'] == 'dark' else "🌙"
    button_style = {
        'position': 'absolute',
        'top': '10px',
        'right': '10px',
        'fontSize': '16px',
        'border': '1px solid #ccc',
        'borderRadius': '50%',
        'width': '30px',
        'height': '30px',
        'backgroundColor': '#2d2d2d' if plot_themes['genre_sunburst'] == 'dark' else '#f0f0f0',
        'color': '#ffffff' if plot_themes['genre_sunburst'] == 'dark' else '#000000',
        'cursor': 'pointer',
        'zIndex': 5
    }
    return create_genre_sunburst(df), icon, button_style

@callback(
    Output('budget-revenue-bar', 'figure'),
    Output('budget_revenue_bar-theme-toggle', 'children'),
    Output('budget_revenue_bar-theme-toggle', 'style'),
    Input('budget_revenue_bar-theme-toggle', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_budget_revenue_bar_theme(n_clicks):
    global plot_themes
    if n_clicks > 0:
        plot_themes['budget_revenue_bar'] = 'light' if plot_themes['budget_revenue_bar'] == 'dark' else 'dark'
    
    icon = "☀️" if plot_themes['budget_revenue_bar'] == 'dark' else "🌙"
    button_style = {
        'position': 'absolute',
        'top': '10px',
        'right': '10px',
        'fontSize': '16px',
        'border': '1px solid #ccc',
        'borderRadius': '50%',
        'width': '30px',
        'height': '30px',
        'backgroundColor': '#2d2d2d' if plot_themes['budget_revenue_bar'] == 'dark' else '#f0f0f0',
        'color': '#ffffff' if plot_themes['budget_revenue_bar'] == 'dark' else '#000000',
        'cursor': 'pointer',
        'zIndex': 5
    }
    return create_budget_revenue_bar(df), icon, button_style

@callback(
    Output('choropleth', 'figure'),
    Output('choropleth_map-theme-toggle', 'children'),
    Output('choropleth_map-theme-toggle', 'style'),
    Input('choropleth_map-theme-toggle', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_choropleth_map_theme(n_clicks):
    global plot_themes
    if n_clicks > 0:
        plot_themes['choropleth_map'] = 'light' if plot_themes['choropleth_map'] == 'dark' else 'dark'
    
    icon = "☀️" if plot_themes['choropleth_map'] == 'dark' else "🌙"
    button_style = {
        'position': 'absolute',
        'top': '10px',
        'right': '10px',
        'fontSize': '16px',
        'border': '1px solid #ccc',
        'borderRadius': '50%',
        'width': '30px',
        'height': '30px',
        'backgroundColor': '#2d2d2d' if plot_themes['choropleth_map'] == 'dark' else '#f0f0f0',
        'color': '#ffffff' if plot_themes['choropleth_map'] == 'dark' else '#000000',
        'cursor': 'pointer',
        'zIndex': 5
    }
    return create_choropleth_map(df), icon, button_style

@callback(
    Output('country-genre-pie', 'figure'),
    Output('country_genre_pie-theme-toggle', 'children'),
    Output('country_genre_pie-theme-toggle', 'style'),
    Input('country_genre_pie-theme-toggle', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_country_genre_pie_theme(n_clicks):
    global plot_themes
    if n_clicks > 0:
        plot_themes['country_genre_pie'] = 'light' if plot_themes['country_genre_pie'] == 'dark' else 'dark'
    
    icon = "☀️" if plot_themes['country_genre_pie'] == 'dark' else "🌙"
    button_style = {
        'position': 'absolute',
        'top': '10px',
        'right': '10px',
        'fontSize': '16px',
        'border': '1px solid #ccc',
        'borderRadius': '50%',
        'width': '30px',
        'height': '30px',
        'backgroundColor': '#2d2d2d' if plot_themes['country_genre_pie'] == 'dark' else '#f0f0f0',
        'color': '#ffffff' if plot_themes['country_genre_pie'] == 'dark' else '#000000',
        'cursor': 'pointer',
        'zIndex': 5
    }
    return create_country_genre_pie(df), icon, button_style

@callback(
    Output('top10-movies-graph', 'figure'),
    Input('top10-country-dropdown', 'value'),
    Input('btn-revenue', 'n_clicks'),
    Input('btn-budget', 'n_clicks'),
    Input('btn-roi', 'n_clicks'),
    Input('btn-popularity', 'n_clicks'),
    Input('top10_movies-theme-toggle', 'n_clicks'),
    prevent_initial_call=False
)
def update_top10_movies_graph(country, n_revenue, n_budget, n_roi, n_popularity, theme_clicks):
    ctx = dash.callback_context
    
    # Handle theme toggle
    if ctx.triggered and ctx.triggered[0]['prop_id'].startswith('top10_movies-theme-toggle'):
        global plot_themes
        plot_themes['top10_movies'] = 'light' if plot_themes['top10_movies'] == 'dark' else 'dark'
    
    # Handle feature selection
    feature = 'revenue'  # default
    if ctx.triggered:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger_id == 'btn-revenue':
            feature = 'revenue'
        elif trigger_id == 'btn-budget':
            feature = 'budget'
        elif trigger_id == 'btn-roi':
            feature = 'roi'
        elif trigger_id == 'btn-popularity':
            feature = 'popularity'
    
    return create_top10_movies_plot(df, country, feature)

@callback(
    Output('top10_movies-theme-toggle', 'children'),
    Output('top10_movies-theme-toggle', 'style'),
    Input('top10_movies-theme-toggle', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_top10_movies_theme_button(n_clicks):
    global plot_themes
    if n_clicks > 0:
        plot_themes['top10_movies'] = 'light' if plot_themes['top10_movies'] == 'dark' else 'dark'
    
    icon = "☀️" if plot_themes['top10_movies'] == 'dark' else "🌙"
    button_style = {
        'position': 'absolute',
        'top': '10px',
        'right': '10px',
        'fontSize': '16px',
        'border': '1px solid #ccc',
        'borderRadius': '50%',
        'width': '30px',
        'height': '30px',
        'backgroundColor': '#2d2d2d' if plot_themes['top10_movies'] == 'dark' else '#f0f0f0',
        'color': '#ffffff' if plot_themes['top10_movies'] == 'dark' else '#000000',
        'cursor': 'pointer',
        'zIndex': 5
    }
    return icon, button_style

# Main theme toggle callback
@callback(
    Output('main-layout', 'style'),
    Output('theme-toggle', 'children'),
    Output('theme-toggle', 'style'),
    Input('theme-toggle', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_theme(n_clicks):
    global current_theme
    
    if n_clicks > 0:
        current_theme = 'light' if current_theme == 'dark' else 'dark'
    
    theme = get_current_theme()
    button_icon = "☀️" if current_theme == 'dark' else "🌙"
    
    button_style = {
        'position': 'absolute',
        'top': '20px',
        'right': '20px',
        'fontSize': '24px',
        'border': '2px solid #555',
        'borderRadius': '50%',
        'width': '50px',
        'height': '50px',
        'backgroundColor': '#2d2d2d' if current_theme == 'dark' else '#f0f0f0',
        'color': '#ffffff' if current_theme == 'dark' else '#000000',
        'cursor': 'pointer',
        'transition': 'all 0.3s ease'
    }
    
    layout_style = {
        'backgroundColor': theme['backgroundColor'],
        'minHeight': '100vh',
        'padding': '20px',
        'fontFamily': theme['fontFamily']
    }
    
    return layout_style, button_icon, button_style

@callback(
    Output('analysis-controls', 'children'),
    Input('tab-slider', 'value'),
    Input('theme-toggle', 'n_clicks')
)
def update_controls(selected_tab, theme_clicks):
    tab_names = ['overview', 'genre', 'country', 'company']
    selected_tab_name = tab_names[selected_tab] if selected_tab < len(tab_names) else 'overview'
    
    if selected_tab_name == 'genre':
        return html.Div([])
    elif selected_tab_name == 'country':
        return html.Div([])
    elif selected_tab_name == 'company':
        return html.Div([])
    return html.Div()

@callback(
    Output('main-content', 'children'),
    [Input('tab-slider', 'value')],
    [Input('theme-toggle', 'n_clicks')],
    prevent_initial_call=False
)
def update_content(selected_tab, theme_clicks):
    tab_names = ['overview', 'genre', 'country', 'company']
    selected_tab_name = tab_names[selected_tab] if selected_tab < len(tab_names) else 'overview'
    
    theme = get_current_theme()
    
    if selected_tab_name == 'overview':
        return html.Div([
            html.H2("📊 Overview", style={'color': theme['color']}),
            html.Div([
                html.Div([
                    create_plot_toggle_button('correlation_heatmap'),
                    dcc.Graph(id='correlation-heatmap', figure=create_correlation_heatmap(df))
                ], style={'position': 'relative', 'marginBottom': '20px'})
            ]),
            html.Div([
                html.Div([
                    create_plot_toggle_button('budget_revenue_scatter'),
                    dcc.Graph(id='budget-revenue-scatter', figure=create_budget_revenue_scatter(df))
                ], style={'position': 'relative', 'marginBottom': '20px'})
            ]),
            html.Div([
                html.Div([
                    create_plot_toggle_button('budget_revenue_bar'),
                    dcc.Graph(id='budget-revenue-bar', figure=create_budget_revenue_bar(df))
                ], style={'position': 'relative', 'marginBottom': '20px'})
            ]),
            html.Div([
                html.Div([
                    create_plot_toggle_button('genre_sunburst'),
                    dcc.Graph(id='genre-sunburst', figure=create_genre_sunburst(df))
                ], style={'position': 'relative', 'marginBottom': '20px'})
            ])
        ])
    elif selected_tab_name == 'genre':
        return html.Div([
            html.H2("🎭 Genre Analysis", style={'color': theme['color']}),
            html.P("Additional genre-specific analysis will be added here", 
                  style={'color': theme['color']})
        ])
    elif selected_tab_name == 'country':
        popup_bg = '#2d2d2d' if current_theme == 'dark' else '#f8f9fa'
        popup_border = '#555' if current_theme == 'dark' else '#dee2e6'
        
        return html.Div([
            html.H2("🌍 Country Analysis", style={'color': theme['color']}),
            html.Div([
                html.Div([
                    create_plot_toggle_button('choropleth_map'),
                    dcc.Graph(id='choropleth', figure=create_choropleth_map(df))
                ], style={'position': 'relative', 'marginBottom': '20px'})
            ]),
            
            # Popup container for genre breakdown
            html.Div([
                html.Button("✕", id='close-button', n_clicks=0, style={
                    'position': 'absolute',
                    'top': '6px',
                    'left': '8px',
                    'fontSize': '16px',
                    'border': 'none',
                    'background': 'transparent',
                    'cursor': 'pointer',
                    'zIndex': 20,
                    'color': theme['color']
                }),
                dcc.Graph(id='genre-popup', config={'displayModeBar': False}),
            ],
            id='popup-container',
            style={
                'position': 'absolute',
                'top': '120px',
                'right': '40px',
                'width': '350px',
                'backgroundColor': popup_bg,
                'boxShadow': '0 4px 8px rgba(0,0,0,0.3)' if current_theme == 'dark' else '0 4px 8px rgba(0,0,0,0.1)',
                'padding': '10px',
                'borderRadius': '10px',
                'display': 'none',
                'zIndex': 10,
                'border': f'1px solid {popup_border}'
            }),
            
            html.Div([
                html.Div([
                    create_plot_toggle_button('country_genre_pie'),
                    dcc.Graph(id='country-genre-pie', figure=create_country_genre_pie(df))
                ], style={'position': 'relative', 'marginBottom': '20px'})
            ]),
            
            html.Div([
                html.Div([
                    create_plot_toggle_button('top10_movies'),
                    html.Div([
                        # Country selector for top 10 movies
                        html.Div([
                            html.Label("🌍 Select Country:", 
                                      style={'color': theme['color'], 'fontWeight': 'bold', 'marginBottom': '5px'}),
                            dcc.Dropdown(
                                id='top10-country-dropdown',
                                options=[
                                    {'label': 'United States of America', 'value': 'United States of America'},
                                    {'label': 'United Kingdom', 'value': 'United Kingdom'},
                                    {'label': 'France', 'value': 'France'},
                                    {'label': 'India', 'value': 'India'},
                                    {'label': 'Germany', 'value': 'Germany'},
                                    {'label': 'Canada', 'value': 'Canada'},
                                    {'label': 'China', 'value': 'China'},
                                    {'label': 'Spain', 'value': 'Spain'},
                                    {'label': 'Italy', 'value': 'Italy'},
                                    {'label': 'Japan', 'value': 'Japan'}
                                ],
                                value='United States of America',
                                style={
                                    'marginBottom': '10px',
                                    'backgroundColor': '#2d2d2d' if current_theme == 'dark' else '#ffffff',
                                    'color': '#ffffff' if current_theme == 'dark' else '#000000'
                                }
                            )
                        ], style={'marginBottom': '15px'}),
                        
                        # Feature buttons
                        html.Div([
                            html.Label("📊 Select Feature:", 
                                      style={'color': theme['color'], 'fontWeight': 'bold', 'marginBottom': '10px', 'display': 'block'}),
                            html.Div([
                                html.Button('💰 Revenue', id='btn-revenue', n_clicks=0, 
                                          style={
                                              'margin': '5px',
                                              'padding': '8px 15px',
                                              'border': 'none',
                                              'borderRadius': '8px',
                                              'background': 'linear-gradient(135deg, #6bffb8, #4caf50)',
                                              'color': 'white',
                                              'fontWeight': 'bold',
                                              'cursor': 'pointer'
                                          }),
                                html.Button('📦 Budget', id='btn-budget', n_clicks=0,
                                          style={
                                              'margin': '5px',
                                              'padding': '8px 15px',
                                              'border': 'none',
                                              'borderRadius': '8px',
                                              'background': 'linear-gradient(135deg, #ff6b6b, #e74c3c)',
                                              'color': 'white',
                                              'fontWeight': 'bold',
                                              'cursor': 'pointer'
                                          }),
                                html.Button('📈 ROI', id='btn-roi', n_clicks=0,
                                          style={
                                              'margin': '5px',
                                              'padding': '8px 15px',
                                              'border': 'none',
                                              'borderRadius': '8px',
                                              'background': 'linear-gradient(135deg, #74b9ff, #0984e3)',
                                              'color': 'white',
                                              'fontWeight': 'bold',
                                              'cursor': 'pointer'
                                          }),
                                html.Button('🔥 Popularity', id='btn-popularity', n_clicks=0,
                                          style={
                                              'margin': '5px',
                                              'padding': '8px 15px',
                                              'border': 'none',
                                              'borderRadius': '8px',
                                              'background': 'linear-gradient(135deg, #fd79a8, #e84393)',
                                              'color': 'white',
                                              'fontWeight': 'bold',
                                              'cursor': 'pointer'
                                          })
                            ], style={'textAlign': 'center'})
                        ], style={'marginBottom': '15px'}),
                        
                        # Graph
                        dcc.Graph(id='top10-movies-graph', figure=create_top10_movies_plot(df))
                    ], style={'padding': '15px'})
                ], style={'position': 'relative', 'marginBottom': '20px'})
            ])
        ])
    elif selected_tab_name == 'company':
        return html.Div([
            html.H2("🏢 Company Analysis", style={'color': theme['color']}),
            html.P("Company analysis plots will be added here", 
                  style={'color': theme['color']})
        ])
    return html.Div("Select a tab")

# Interactive choropleth callbacks
@callback(
    Output('genre-popup', 'figure'),
    Output('popup-container', 'style'),
    Input('choropleth', 'clickData'),
    Input('close-button', 'n_clicks'),
    State('popup-container', 'style'),
    prevent_initial_call=True
)
def update_genre_popup(clickData, close_clicks, current_style):
    ctx = dash.callback_context
    global choropleth_data

    popup_bg = '#2d2d2d' if current_theme == 'dark' else '#f8f9fa'
    popup_border = '#555' if current_theme == 'dark' else '#dee2e6'
    
    # Initialize default style if None
    if current_style is None:
        current_style = {
            'position': 'absolute',
            'top': '120px',
            'right': '40px',
            'width': '350px',
            'backgroundColor': popup_bg,
            'boxShadow': '0 4px 8px rgba(0,0,0,0.3)' if current_theme == 'dark' else '0 4px 8px rgba(0,0,0,0.1)',
            'padding': '10px',
            'borderRadius': '10px',
            'display': 'none',
            'zIndex': 10,
            'border': f'1px solid {popup_border}'
        }

    if ctx.triggered and ctx.triggered[0]['prop_id'].startswith('close-button'):
        current_style['display'] = 'none'
        return px.bar(title=""), current_style

    if not clickData or not choropleth_data:
        current_style['display'] = 'none'
        return px.bar(title=""), current_style

    try:
        iso = clickData['points'][0]['location']
        summary = choropleth_data['summary']
        country_genre = choropleth_data['country_genre']
        
        country = summary.loc[summary['iso_alpha'] == iso, 'production_countries'].values[0]

        genre_data = (
            country_genre[country_genre['production_countries'] == country]
            .groupby('genres')['count']
            .sum()
            .reset_index()
            .sort_values(by='count', ascending=False)
            .head(10)
        )

        if genre_data.empty:
            current_style['display'] = 'none'
            return px.bar(title="No data available"), current_style

        fig = px.bar(
            genre_data,
            x='genres',
            y='count',
            title=f"Top Genres in {country}",
            color='count',
            color_continuous_scale='Inferno'
        )

        fig.update_layout(
            xaxis_title=None,
            yaxis_title='Movies',
            margin=dict(t=50, l=30, r=10, b=70),
            paper_bgcolor=get_plot_theme('choropleth_map')['paper_bgcolor'],
            plot_bgcolor=get_plot_theme('choropleth_map')['plot_bgcolor'],
            font_color=get_plot_theme('choropleth_map')['font_color'],
            height=300
        )
        fig.update_xaxes(tickangle=45)

        # Make the popup visible with dynamic positioning
        updated_style = current_style.copy()
        updated_style['display'] = 'block'
        
        # Get click coordinates and adjust popup position
        if 'points' in clickData and len(clickData['points']) > 0:
            point = clickData['points'][0]
            if 'bbox' in point:
                # Use bbox coordinates if available
                bbox = point['bbox']
                x_pos = bbox['x0'] + (bbox['x1'] - bbox['x0']) / 2
                y_pos = bbox['y0'] + (bbox['y1'] - bbox['y0']) / 2
            else:
                # Fallback to center coordinates
                x_pos = 400  # Default center position
                y_pos = 300
            
            # Adjust position to prevent popup from going off-screen
            max_x = 800  # Approximate chart width
            max_y = 600  # Approximate chart height
            
            # Position popup to the right of click point, or left if too close to right edge
            if x_pos > max_x * 0.6:
                updated_style['left'] = f'{max(10, x_pos - 370)}px'
            else:
                updated_style['left'] = f'{min(max_x - 370, x_pos + 20)}px'
            
            # Position popup below click point, or above if too close to bottom
            if y_pos > max_y * 0.6:
                updated_style['top'] = f'{max(10, y_pos - 320)}px'
            else:
                updated_style['top'] = f'{min(max_y - 320, y_pos + 20)}px'
            
            # Remove right positioning when using left
            if 'right' in updated_style:
                del updated_style['right']

        return fig, updated_style
    except Exception as e:
        current_style['display'] = 'none'
        return px.bar(title=""), current_style

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)