import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, callback
import pycountry

import warnings
warnings.filterwarnings("ignore")

# --- Load and preprocess data ---
df = pd.read_csv('tabs/TMDB_movie_dataset_v11.csv')
df['genres'] = df['genres'].fillna('').str.split(',\s*')
df = df[df['genres'].notna()]
df = df[~df['genres'].str.lower().isin(['', 'nan', 'none'])]
df['year'] = pd.to_datetime(df['release_date'], errors='coerce').dt.year
df = df[df['year'].between(1940, 2023)]
df = df[df['title'].isin(['IPL 2025', 'TikTok Rizz Party']) == False]
df = df.dropna(subset=["title", "production_countries", "production_companies"])
df['production_companies'] = df['production_companies'].str.split(',\s*')
df['roi'] = df['revenue'] / df['budget']
df.replace([np.inf, -np.inf], np.nan, inplace=True)
available_genres = ['Animation', 'Comedy', 'Documentary', 'Drama', 'Horror', 'Music', 'Romance', 'Thriller']

top_companies = [
        'Universal Pictures', 'Warner Bros. Pictures', 'Walt Disney Studios', 'Sony Pictures',
        'Lionsgate', '20th Century Studios', 'DreamWorks Studios', 'Marvel Studios', 'Pixar Animation'
]

features = {
    'revenue': 'Revenue',
    'budget': 'Budget',
    'roi': 'Return on Investment (ROI)',
    'popularity': 'Popularity'
}

# --- Layout ---
def layout():
    return html.Div([
        html.H2("Company - wise Analysis: Genre Distribution and ROI Analysis", style={'textAlign': 'center'}),
        html.Div([
            html.Div([
                html.Label("Select a Company:"),
                dcc.Dropdown(
                    id='company-dropdown',
                    options=[{'label': c, 'value': c} for c in top_companies],
                    value='Universal Pictures',
                    clearable=False,
                    searchable=False, 
                )
            ], style={'width': '48%', 'display': 'inline-block', 'paddingRight': '1%'}),

            html.Div([
                html.Label("Select Genre:"),
                dcc.Dropdown(
                    id='feature-dropdown',
                    options=[{'label': genre, 'value': genre} for genre in available_genres],
                    value='Animation',
                    clearable=False,
                    searchable=False, 
                )
            ], style={'width': '48%', 'display': 'inline-block', 'paddingLeft': '1%'})
        ], style={'padding': '10px 0'}),
        html.Div([
            html.Div([dcc.Graph(id='plot-31')], className='column-half'),
            html.Div([dcc.Graph(id='plot-32')], className='column-half'),
        ], className='row'),
        html.Div([
            html.Div([dcc.Graph(id='plot-33')], className='column-half'),
            html.Div([dcc.Graph(id='plot-34')], className='column-half'),
        ], className='row'),
    ])

# --- Callbacks ---
def register_callbacks(app):
    @app.callback(
        Output('plot-31', 'figure'),
        Output('plot-32', 'figure'),
        Output('plot-33', 'figure'),
        Output('plot-34', 'figure'),
        Input('company-dropdown', 'value'),
        Input('feature-dropdown', 'value')
    )
    def update_static_plots(selected_company, selected_genre):
        genre_df = df.copy()
        fig1 = companywrtgenre(genre_df, selected_genre)
        fig2 = sankey(genre_df, selected_company)
        fig3 = topwrtroi(genre_df, selected_company)
        fig4 = genredist(genre_df, selected_company)
        return fig1, fig2, fig3, fig4

    def update_top10_bar_chart(selected_country, selected_feature):
        pass

# --- Plot Functions ---
def companywrtgenre(df, genre):
    df = df.copy()
    df = df.explode('genres')
    df['genres'] = df['genres'].str.strip()
    df = df[df['genres'].str.lower() == genre.lower()]
    df['production_companies'] = df['production_companies'].astype(str).str.strip("[]").str.replace("'", "")
    df['production_companies'] = df['production_companies'].str.split(", ")
    df = df.explode('production_companies')
    df['production_companies'] = df['production_companies'].str.strip()

    # Remove invalid entries
    df = df[
        df['production_companies'].notna() &
        ~df['production_companies'].str.lower().isin(['', 'nan', 'none'])
    ]

    if df.empty:
        raise ValueError(f"No data available for genre: {genre}")

    top_companies = (
        df['production_companies']
        .value_counts()
        .nlargest(7)
        .reset_index()
    )
    top_companies.columns = ['production_company', 'movie_count']

    fig = px.bar(
        top_companies,
        x='movie_count',
        y='production_company',
        orientation='h',
        # text='movie_count',
        title=f"Top 7 Companies for {genre.title()}",
        labels={'movie_count': 'Number of Movies', 'production_company': 'Production Company'},
        color='production_company',
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    fig.update_traces(
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Movies: %{x}<extra></extra>'
    )

    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False,
        template='plotly_white',
        height=500,
        width=500
    )
    return fig

def sankey(df, company_name):
    df = df.copy()
    df = df[df['year'].between(1980, 2023)]
    df = df.explode('production_companies')
    df['production_companies'] = df['production_companies'].str.strip()

    df = df[df['production_companies'].str.lower() == company_name.lower()]

    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df = df[df['release_date'].notna()]
    df['decade'] = (df['release_date'].dt.year // 10 * 10).astype('Int64').astype(str) + 's'

    df = df.explode('genres')
    df['genres'] = df['genres'].str.strip()

    top_genres = df['genres'].value_counts().nlargest(5).index
    df = df[df['genres'].isin(top_genres)]

    df2 = df.groupby(['genres', 'decade']).size().reset_index(name='count')
    df2['source'] = df2['genres']
    df2['target'] = df2['decade']

    all_nodes = pd.unique(df2[['source', 'target']].values.ravel())
    node_map = {name: i for i, name in enumerate(all_nodes)}
    df2['source_id'] = df2['source'].map(node_map)
    df2['target_id'] = df2['target'].map(node_map)

    # Step 7: Assign distinct colors
    palette = px.colors.qualitative.Set3
    color_map = {name: palette[i % len(palette)] for i, name in enumerate(all_nodes)}
    node_colors = [color_map[name] for name in all_nodes]

    # Step 8: Plot Sankey
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=list(all_nodes),
            color=node_colors
        ),
        link=dict(
            source=df2['source_id'],
            target=df2['target_id'],
            value=df2['count']
        )
    )])

    fig.update_layout(
        title_text=f"Flow for {company_name}",
        font_size=10,
        height=500,
        width=500,
    )

    return fig

def topwrtroi(df, company_name):
    df = df.copy()
    df = df.explode('production_companies')
    df['production_companies'] = df['production_companies'].str.strip()

    df = df[df['production_companies'].str.lower() == company_name.lower()]
    top_movies = df[['title', 'roi']].dropna().sort_values(by='roi', ascending=False).head(5)

    if top_movies.empty:
        raise ValueError(f"No valid ROI data found for company: {company_name}")

    # Plot
    fig = px.bar(
        top_movies.sort_values('roi'),
        x='roi',
        y='title',
        orientation='h',
        color='roi',
        color_continuous_scale='sunset',
        title=f"Top 5 Movies by ROI — {company_name}",
        labels={'roi': 'Return on Investment', 'title': 'Movie Title'}
    )

    fig.update_layout(
        yaxis_title='',
        xaxis_title='ROI',
        coloraxis_showscale=False,
        height=500,
        width=500,
        template='plotly_white'
    )

    return fig

def genredist(df, company_name):
    df = df.copy()
    df = df.explode('production_companies')
    df['production_companies'] = df['production_companies'].str.strip()
    df = df[df['production_companies'].str.lower() == company_name.lower()]
    df = df.explode('genres')
    df['genres'] = df['genres'].str.strip()

    if df.empty:
        raise ValueError(f"No genre data found for company: {company_name}")

    top_genres = df['genres'].value_counts().nlargest(7).reset_index()
    top_genres.columns = ['genre', 'count']

    # Create donut chart
    fig = px.pie(
        top_genres,
        names='genre',
        values='count',
        hole=0.5,
        title=f"Top 7 Genres Produced by {company_name}",
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    fig.update_traces(
        textinfo='percent',
        hovertemplate='%{label}<br>Movies: %{value}<extra></extra>'
    )

    fig.update_layout(
        height=500,
        width=500,
        template='plotly_white'
    )

    return fig