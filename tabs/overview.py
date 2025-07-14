import pandas as pd
import plotly.express as px
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go

import warnings
warnings.filterwarnings("ignore")

df = pd.read_csv('tabs/TMDB_movie_dataset_v11.csv')
df['genres'] = df['genres'].fillna('').str.split(',\s*')
df = df.explode('genres')
df['year'] = pd.to_datetime(df['release_date'], errors='coerce').dt.year
available_genres = ['Animation', 'Comedy', 'Documentary', 'Drama', 'Horror', 'Music', 'Romance', 'Thriller']

# Layout function
def layout():
    return html.Div([
        html.H2("Overview Tab: Brief Overview and Initial Plots", style={'textAlign': 'center'}),
        # Row 1: Two side-by-side plots
        html.Div([
            dcc.Graph(id='plot-1')
        ], className='column-full'),
        html.Div([
            html.Div([dcc.Graph(id='plot-2')], className='column-half'),
            html.Div([dcc.Graph(id='plot-3')], className='column-half'),
        ], className='row'),
        html.Div([
            dcc.Graph(id='plot-4')
        ], className='column-full'),
        html.Div([
            dcc.Graph(id='plot-5')
        ], className='column-full'),
    ])

def register_callbacks(app):
    @app.callback(
        Output('plot-1', 'figure'),
        Output('plot-2', 'figure'),
        Output('plot-3', 'figure'),
        Output('plot-4', 'figure'),
        Output('plot-5', 'figure'),
        Input('plot-1', 'id')  # Dummy input to trigger update once
    )
    def update_genre_plots(_):
        fig1 = get_movies_per_year(df)
        fig2 = get_genre_sunburst(df, start_year=2020, end_year=2023, genres=available_genres)
        fig3 = heatmap(df)
        fig4 = streamplot(df)
        fig5 = scatterplot(df)
        return fig1, fig2, fig3, fig4, fig5

# movies each year
def get_movies_per_year(df: pd.DataFrame) -> px.bar:
    df = df.copy()
    df = df[df['year'] >= 1940]
    df = df[df['year'] <= 2023]
    movies_per_year = df.groupby('year').size().reset_index(name='count').dropna()
    # Plot
    fig = px.bar(
        movies_per_year,
        x='year',
        y='count',
        labels={'year': 'Year', 'count': 'Number of Movies'},
        title=f'Number of Movies Released Per Year',
        hover_data={'year': True, 'count': True},
        color='count',
        color_continuous_scale='sunset'
    )

    fig.update_layout(
        width=1150,
        height=500,
        xaxis=dict(
            title='Year',
            tickangle=-45,
            rangeslider_visible=True,
        ),
        yaxis_title='Number of Movies',
        hovermode='x unified'
    )

    return fig

# sunburst plot
def get_genre_sunburst(
    df: pd.DataFrame,
    start_year: int = 2020,
    end_year: int = 2023,
    genres: list = None
) -> px.sunburst:
    """
    Returns a Plotly Sunburst chart showing year-wise genre distribution.

    Parameters:
    - df: DataFrame containing at least 'release_date' and 'genres' columns
    - start_year: Start year for filtering (inclusive)
    - end_year: End year for filtering (inclusive)
    - genres: List of genres to include (default: top 6 predefined)

    Returns:
    - fig: Plotly Sunburst figure
    """
    df = df.copy()

    # Convert release_date to datetime safely
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df['year'] = df['release_date'].dt.year

    # Filter years
    df = df[df['year'].between(start_year, end_year)]

    # Drop rows with missing year or genres
    df_cleaned = df.dropna(subset=['year', 'genres']).copy()
    df_cleaned['year'] = df_cleaned['year'].astype(int)

    # Split genres and explode
    df_cleaned['genre_list'] = df_cleaned['genres'].apply(lambda x: [g.strip() for g in x.split(',')])
    df_exploded = df_cleaned.explode('genre_list')

    # Filter to selected genres
    df_exploded = df_exploded[df_exploded['genre_list'].isin(genres)]

    # Group by year and genre
    genre_counts = (
        df_exploded.groupby(['year', 'genre_list'])
        .size()
        .reset_index(name='count')
    )

    if genre_counts.empty:
        return px.sunburst(title="No data available for selected genres and years.")

    # Create Sunburst
    fig = px.sunburst(
        genre_counts,
        path=['year', 'genre_list'],
        values='count',
        title=f'Year-wise Genre Evolution ({start_year}–{end_year})',
        color='count',
        color_continuous_scale='inferno'
    )

    fig.update_layout(margin=dict(t=50, l=0, r=0, b=0))
    fig.update_layout(
        width=550,
        height=500)
    return fig

# heatmap plot
def heatmap(df, numeric_cols = ['vote_average', 'vote_count', 'budget', 'revenue', 'popularity'], title='Interactive Correlation Heatmap'):
    """
    Plots an interactive correlation heatmap for selected numeric columns in a DataFrame.

    Parameters:
    - df (pd.DataFrame): The input DataFrame.
    - numeric_cols (list of str): List of numeric column names to include.
    - title (str): Title for the heatmap.

    Returns:
    - fig (plotly.graph_objects.Figure): The Plotly heatmap figure.
    """
    df= df.copy()
    df_numeric = df[numeric_cols].dropna()

    # Compute correlation matrix
    corr = df_numeric.corr().round(2)

    # Create heatmap
    fig = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale='YlGnBu',
        zmin=-1,
        zmax=1,
        title=title
    )

    fig.update_layout(
        width=500,height=500
    )
    return fig

# streamplot
def streamplot(df: pd.DataFrame) -> go.Figure:
    df = df.copy()
    df['release_date'] = pd.to_datetime(df['release_date'])
    df = df[(df['release_date'].dt.year >= 1940) & (df['release_date'].dt.year <= 2025)]
    df['genres'] = df['genres'].apply(lambda x: [genre.strip() for genre in x.split(',')] if pd.notnull(x) else [])
    df['year'] = df['release_date'].dt.year
    df = df.dropna(subset=['year'])

    # Explode genres
    df_exploded = df.explode('genres')

    # Count per year and genre
    genre_counts = df_exploded.groupby(['year', 'genres']).size().reset_index(name='count')
    total_per_year = genre_counts.groupby('year')['count'].sum().reset_index(name='total')
    genre_counts = genre_counts.merge(total_per_year, on='year')
    genre_counts['percentage'] = (genre_counts['count'] / genre_counts['total']) * 100

    # Get top 8 genres overall
    top_genres = available_genres
    filtered = genre_counts[genre_counts['genres'].isin(top_genres)]

    # Mark direction and adjust %
    top_half = top_genres[1::2]
    bottom_half = top_genres[::2]
    filtered['direction'] = filtered['genres'].apply(lambda g: 'up' if g in top_half else 'down')
    filtered['adjusted_percentage'] = filtered.apply(
        lambda row: row['percentage'] if row['direction'] == 'up' else -row['percentage'],
        axis=1
    )

    # Prepare for stacked area plot
    years = sorted(filtered['year'].unique())
    fig = go.Figure()

    # Stack values for positive and negative areas
    up_df = filtered[filtered['direction'] == 'up']
    down_df = filtered[filtered['direction'] == 'down']

    # Build stacks for upward
    cumulative = pd.Series([0] * len(years), index=years)
    for genre in top_half:
        data = up_df[up_df['genres'] == genre].set_index('year')['adjusted_percentage'].reindex(years, fill_value=0)
        fig.add_trace(go.Scatter(
            x=years,
            y=(cumulative + data).values,
            mode='lines',
            name=genre,
            fill='tonexty'
        ))
        cumulative += data

    # Build stacks for downward
    cumulative = pd.Series([0] * len(years), index=years)
    for genre in bottom_half:
        data = down_df[down_df['genres'] == genre].set_index('year')['adjusted_percentage'].reindex(years, fill_value=0)
        fig.add_trace(go.Scatter(
            x=years,
            y=(cumulative + data).values,
            mode='lines',
            name=genre,
            fill='tonexty'
        ))
        cumulative += data

    # Layout
    fig.update_layout(
        title='Symmetric Streamgraph of Top 8 Genres Over Time',
        xaxis_title='Year',
        yaxis_title='Percentage Share',
        width=1150,
        height=500,
        hovermode='x unified'
    )
    return fig

def scatterplot(df):
    df = df.copy()
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df = df[df['release_date'].dt.year.between(1990, 2025)]
    df = df.dropna(subset=['runtime', 'vote_average', 'revenue', 'budget', 'popularity'])
    df = df[
        (df['runtime'] > 50) & (df['runtime'] < 200) &
        (df['vote_average'] > 0) &
        (df['revenue'] > 0) &
        (df['budget'] > 0) &
        (df['popularity'] > 0)
    ]
    fig = px.scatter(
        df,
        x='runtime',
        y='vote_average',
        color='vote_average',
        color_continuous_scale='Viridis',
        hover_name='title',
        labels={'runtime': 'Runtime (min)', 'vote_average': 'Average Vote'},
        title='🎬 Runtime vs Rating of Movies (1990–2025)'
    )

    fig.update_layout(template='plotly_white')

    return fig

