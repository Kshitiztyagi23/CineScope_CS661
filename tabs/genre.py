import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output
import numpy as np

import warnings
warnings.filterwarnings("ignore")

# Load and process dataset
df = pd.read_csv('tabs/TMDB_movie_dataset_v11.csv')
df['genres'] = df['genres'].fillna('').str.split(',\s*')
df = df.explode('genres')
df['year'] = pd.to_datetime(df['release_date'], errors='coerce').dt.year
available_genres = ['Animation', 'Comedy', 'Documentary', 'Drama', 'Horror', 'Music', 'Romance', 'Thriller']

# Layout function with dropdown
def layout():
    return html.Div([
        html.H2("Genre Tab: Genre Analysis and Plots", style={'textAlign': 'center'}),

        html.Div([
            dcc.Dropdown(
                id='genre-dropdown',
                options=[{'label': genre, 'value': genre} for genre in available_genres],
                value='Drama',
                clearable=False,
                style={'width': '50%'},
                persistence=True,
                persistence_type='memory',
                searchable=False, 
            )
        ], style={'textAlign': 'center', 'marginBottom': '30px'}),
        html.Div([dcc.Graph(id='plot-11')], className='column-full'),

        html.Div([
            html.Div([dcc.Graph(id='plot-12')], className='column-half'),
            html.Div([dcc.Graph(id='plot-13')], className='column-half'),
        ], className='row'),

        html.Div([dcc.Graph(id='plot-14')], className='column-full'),
    ])

# Callback registration
def register_callbacks(app):
    @app.callback(
        Output('plot-11', 'figure'),
        Output('plot-12', 'figure'),
        Output('plot-13', 'figure'),
        Output('plot-14', 'figure'),
        Input('genre-dropdown', 'value')
    )
    def update_genre_plots(selected_genre):
        genre_df = df[df['genres'] == selected_genre].copy()

        fig1 = get_movies_per_year_for_genre(genre_df)
        fig2 = country_heatmap(genre_df, selected_genre)
        fig3 = company_heatmap(genre_df, selected_genre)
        fig4 = genre_treemap(df)

        return fig1, fig2, fig3, fig4

# Plotting function
def get_movies_per_year_for_genre(df: pd.DataFrame) -> px.bar:
    df = df.copy()
    df = df[df['year'].between(1940, 2023)]
    movies_per_year = df.groupby('year').size().reset_index(name='count').dropna()

    fig = px.bar(
        movies_per_year,
        x='year',
        y='count',
        labels={'year': 'Year', 'count': 'Number of Movies'},
        title='Number of Movies Released Per Year',
        hover_data={'year': True, 'count': True},
        color='count',
        color_continuous_scale='sunset'
    )

    fig.update_layout(
        width=1150,
        height=500,
        xaxis=dict(title='Year', tickangle=-45, rangeslider_visible=True),
        yaxis_title='Number of Movies',
        hovermode='x unified'
    )

    return fig

def country_heatmap(df, genre):
    df = df.copy()
    df = df[df['year'].between(1980, 2024)]
    df = df.explode('genres')
    df['genres'] = df['genres'].str.strip()
    df = df[df['genres'] == genre]

    if df.empty:
        print(f"No movies found for genre: {genre}")
        return go.Figure()

    df['production_countries'] = df['production_countries'].astype(str)
    df['production_countries'] = df['production_countries'].str.strip("[]").str.replace("'", "")
    df['production_countries'] = df['production_countries'].str.split(", ")
    df = df.explode('production_countries')
    df['production_countries'] = df['production_countries'].str.strip()

    df = df[df['production_countries'].notna()]
    df = df[df['production_countries'].str.lower() != 'nan']
    df = df[df['production_countries'] != '']

    bins = list(range(1980, 2024, 5))
    labels = [f"{y}-{y+4}" for y in bins[:-1]]
    df['period'] = pd.cut(df['year'], bins=bins, labels=labels, right=False)

    count_data = df.groupby(['production_countries', 'period']).size().unstack(fill_value=0)
    top_countries = ['South Korea', 'Australia', 'Canada', 'China','India','Japan', 'Germany', 'France', 'United Kingdom','United States of America']
  
    count_data = count_data.loc[top_countries]
    z_log = np.log10(count_data + 1)

    hover_text = [
        [
            f"Country: {country}<br>Period: {period}<br>{genre} Movies: {int(count_data.loc[country, period])}"
            for period in count_data.columns
        ]
        for country in count_data.index
    ]

    fig = go.Figure(data=go.Heatmap(
        z=z_log.values,
        x=count_data.columns,
        y=count_data.index,
        customdata=hover_text,
        hovertemplate="%{customdata}<extra></extra>",
        colorscale='plasma',
        colorbar=dict(
            title=f"Count",
            tickvals=[0, 1, 2, 3],
            ticktext=["1", "10", "100", "1000"]
        )
    ))
    fig.update_layout(
        title=f"Top Countries Producing {genre} Movies",
        xaxis_title="5-Year Period",
        yaxis_title="Country",
        width=550,
        height=500,
    )
    return fig

def company_heatmap(df, genre):
    target_studios = {
        'Universal Pictures': ['Universal Pictures', 'Universal Studios', 'Universal Entertainment'],
        'Paramount Pictures': ['Paramount Pictures', 'Paramount', 'Paramount Studios'],
        'Warner Bros. Pictures': ['Warner Bros.', 'Warner Brothers', 'Warner Bros. Pictures', 'Warner Bros. Entertainment'],
        'Walt Disney Studios': ['Walt Disney Pictures', 'Disney', 'Walt Disney Studios', 'Walt Disney Productions'],
        'Sony Pictures': ['Sony Pictures', 'Columbia Pictures', 'Sony Pictures Entertainment', 'TriStar Pictures'],
        'Lionsgate': ['Lionsgate', 'Lions Gate Entertainment', 'Lionsgate Films'],
        '20th Century Studios': ['20th Century Fox', '20th Century Studios', 'Twentieth Century Fox'],
        'DreamWorks Studios': ['DreamWorks', 'DreamWorks Pictures', 'DreamWorks Studios'],
        'Marvel Studios': ['Marvel Studios', 'Marvel Entertainment', 'Marvel'],
        'Pixar Animation': ['Pixar', 'Pixar Animation Studios']
    }
    df = df.copy()
    studio_map = {alias: studio for studio, variants in target_studios.items() for alias in variants}
    df = df[df['year'].between(1980, 2024)]

    df = df.explode('genres')
    df['genres'] = df['genres'].str.strip()
    df = df[df['genres'] == genre]

    if df.empty:
        print(f"No movies found for genre: {genre}")
        return go.Figure()

    df['production_companies'] = df['production_companies'].astype(str).str.strip("[]").str.replace("'", "")
    df['production_companies'] = df['production_companies'].str.split(", ")
    df = df.explode('production_companies')
    df['production_companies'] = df['production_companies'].str.strip()
    df = df[df['production_companies'].notna()]
    df = df[df['production_companies'].str.lower() != 'nan']
    df = df[df['production_companies'] != '']

    df['studio_mapped'] = df['production_companies'].map(studio_map)
    df = df[df['studio_mapped'].notna()]

    bins = list(range(1980, 2024, 5))
    labels = [f"{y}-{y+4}" for y in bins[:-1]]
    df['period'] = pd.cut(df['year'], bins=bins, labels=labels, right=False)

    # Group by mapped studio and period
    count_data = df.groupby(['studio_mapped', 'period']).size().unstack(fill_value=0)

    final_studios = list(target_studios.keys())
    count_data = count_data.reindex(final_studios).fillna(0)
    z_log = np.log10(count_data + 1)

    # Hover text
    hover_text = [
        [
            f"Company: {studio}<br>Period: {period}<br>{genre} Movies: {int(count_data.loc[studio, period])}"
            for period in count_data.columns
        ]
        for studio in count_data.index
    ]

    fig = go.Figure(data=go.Heatmap(
        z=z_log.values,
        x=count_data.columns,
        y=count_data.index,
        customdata=hover_text,
        hovertemplate="%{customdata}<extra></extra>",
        colorscale='plasma',
        colorbar=dict(
            title=f"Count",
            tickvals=[0, 1, 2, 3],
            ticktext=["1", "10", "100", "1000"]
        )
    ))

    fig.update_layout(
        title=f"Major Studios Producing {genre} Movies",
        xaxis_title="5-Year Period",
        yaxis_title="Production Company",
        width=500,
        height=500
    )
    return fig

def genre_treemap(df, metric='budget'):
    df = df.copy()
    numeric_cols = ['budget']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    df = df.dropna(subset=numeric_cols)
    df = df[(df['budget'] > 0)]

    df = df.explode('genres')
    df['genres'] = df['genres'].str.strip()
    df = df[df['genres'].notna()]
    df = df[~df['genres'].str.lower().isin(['', 'nan', 'none'])]

    # Group and aggregate
    agg_df = df.groupby('genres').agg({
        'budget': 'mean',
        'genres': 'count'
    }).rename(columns={'genres': 'count'}).reset_index()

    for col in ['budget']:
        agg_df[col] = agg_df[col].round(2)

    def format_metric(row):
        value = row[metric]
        if metric in ['budget']:
            return f"Avg {metric.capitalize()}: ${value/1e6:.1f}M"

    agg_df['label'] = (
        agg_df['genres'] + "<br>" +
        "Movies: " + agg_df['count'].astype(str) + "<br>" +
        agg_df.apply(format_metric, axis=1)
    )

    fig = px.treemap(
        agg_df,
        path=['genres'],
        values=metric,
        color=metric,
        color_continuous_scale='viridis',
        custom_data=['label']
    )

    fig.update_traces(
        hovertemplate="%{customdata[0]}<extra></extra>",
        textinfo='label'  # ← Hide static text, show only on hover
    )

    fig.update_layout(
        title=f"Treemap of Genres by Average {metric.capitalize()}",
        height=500,
        width=1150
    )

    return fig