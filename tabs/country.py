import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, callback, Dash
import pycountry
import warnings

warnings.filterwarnings("ignore")

# --- Load and preprocess data ---
df = pd.read_csv('tabs/TMDB_movie_dataset_v11.csv')
df['genres'] = df['genres'].fillna('').str.split(',\s*')
df['year'] = pd.to_datetime(df['release_date'], errors='coerce').dt.year
df = df[df['year'].between(1940, 2023)]
df = df[df['title'].isin(['IPL 2025', 'TikTok Rizz Party']) == False]
df = df.dropna(subset=["title", "production_countries", "production_companies"])
df['production_countries'] = df['production_countries'].str.split(',\s*')
df['roi'] = df['revenue'] / df['budget']
df.replace([np.inf, -np.inf], np.nan, inplace=True)
df = df.dropna(subset=['roi'])

available_genres = ['Animation', 'Comedy', 'Documentary', 'Drama', 'Horror', 'Music', 'Romance', 'Thriller']

top_countries = [
    'United States of America', 'United Kingdom', 'France', 'India', 'Germany',
    'Canada', 'China', 'Spain', 'Italy', 'Japan'
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
        html.H2("Country-wise Analysis", style={'textAlign': 'center'}),

        html.Div([
        html.Div([dcc.Graph(id='plot-21')], style={
            'width': '900px', 'display': 'inline-block'
        }),
        html.Div([
            dcc.Graph(id='plot-25')
        ], style={
            'width': '300px',
            'display': 'inline-block',
            'verticalAlign': 'top'
        })
    ], style={'display': 'flex', 'flexDirection': 'row'}),

        html.Div([
            html.Div([
                html.Label("Select Country:"),
                dcc.Dropdown(
                    id='country-dropdown',
                    options=[{'label': c, 'value': c} for c in top_countries],
                    value='United States of America',
                    clearable=False
                )
            ], style={'width': '48%', 'display': 'inline-block', 'paddingRight': '1%'}),

            html.Div([
                html.Label("Select Feature:"),
                dcc.Dropdown(
                    id='feature-dropdown',
                    options=[{'label': label, 'value': key} for key, label in features.items()],
                    value='revenue',
                    clearable=False
                )
            ], style={'width': '48%', 'display': 'inline-block', 'paddingLeft': '1%'})
        ], style={'padding': '10px 0'}),

        html.Div([
            html.Div([dcc.Graph(id='plot-22')], className='column-half'),
            html.Div([dcc.Graph(id='plot-23')], className='column-half'),
        ], className='row'),

        html.Div([dcc.Graph(id='plot-24')], className='column-full'),
    ])

# --- Callbacks ---
def register_callbacks(app):
    @app.callback(
        Output('plot-21', 'figure'),
        Output('plot-22', 'figure'),
        Output('plot-23', 'figure'),
        Input('country-dropdown', 'value')
    )
    def update_static_plots(selected_country):
        genre_df = df.copy()
        fig1, _ = get_choropleth_and_genre(genre_df)
        fig2 = top_production_companies_donut(genre_df, selected_country)
        fig3 = genre_decade_sankey_by_country(genre_df, selected_country)
        return fig1, fig2, fig3

    @app.callback(
        Output('plot-24', 'figure'),
        Input('country-dropdown', 'value'),
        Input('feature-dropdown', 'value')
    )
    def update_top10_bar_chart(selected_country, selected_feature):
        return get_top10_bar_chart(df, selected_country, selected_feature)

    @app.callback(
        Output('plot-25', 'figure'),
        Input('plot-21', 'clickData')
    )
    def update_genre_bar_on_click(clickData):
        if clickData is None:
            return go.Figure()
        country = clickData['points'][0]['hovertext']
        return get_genre_bar_by_country(df, country)

# --- Plot Functions ---
def get_genre_bar_by_country(df, country):
    df = df.copy()
    df = df.explode('production_countries')
    df = df.explode('genres')
    df['production_countries'] = df['production_countries'].str.strip()
    df['genres'] = df['genres'].str.strip()
    df = df[df['production_countries'] == country]

    genre_counts = df['genres'].value_counts().reset_index()
    genre_counts.columns = ['genre', 'count']

    fig = px.bar(
        genre_counts.head(15),
        x='genre',
        y='count',
        title=f"<b>Top Genres in {country}</b>",
        labels={'count': 'Movie Count', 'genre': 'Genre'},
        color='count',
        color_continuous_scale='tealgrn'
    )

    fig.update_layout(
        margin=dict(t=100, b=20, l=0, r=0),
        height=350,
        plot_bgcolor='white',
        paper_bgcolor='white',
        title_font=dict(size=16, family='Arial', color='black'),
        font=dict(size=12, color='black'),
    )
    return fig

def get_choropleth_and_genre(df):
    df = df.copy()
    df = df[df['production_countries'].notna()]
    df['genres'] = df['genres'].str.split(r',\s*')
    df = df.explode('production_countries').explode('genres')
    df['production_countries'] = df['production_countries'].str.strip()

    summary = df.groupby('production_countries').agg(movie_count=('title', 'count')).reset_index()
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
        hovertemplate="<b>%{hovertext}</b><br>Movies: %{customdata[0]:,}<extra></extra>",
        customdata=summary[['movie_count']].values
    )
    fig.update_layout(
        geo=dict(projection_type='natural earth', showframe=False),
        height=600 , width=800,
        coloraxis_colorbar=dict(
            title="Movies",
            tickvals=[0, 1, 2, 3, 4],
            ticktext=["1", "10", "100", "1K", "10K"]
        )
    )
    return fig, None

def top_production_companies_donut(df, country):
    df = df.copy()
    df['production_countries'] = df['production_countries'].astype(str).str.strip("[]").str.replace("'", "")
    df['production_countries'] = df['production_countries'].str.split(", ")
    df = df.explode('production_countries')
    df['production_countries'] = df['production_countries'].str.strip()

    df['production_companies'] = df['production_companies'].astype(str).str.strip("[]").str.replace("'", "")
    df['production_companies'] = df['production_companies'].str.split(", ")
    df = df.explode('production_companies')
    df['production_companies'] = df['production_companies'].str.strip()

    df = df[df['production_companies'].notna()]
    df = df[~df['production_companies'].str.lower().isin(['', 'nan', 'none'])]
    df = df[df['production_countries'] == country]

    if df.empty:
        return px.pie(names=[], values=[])

    company_counts = df['production_companies'].value_counts().nlargest(7).reset_index()
    company_counts.columns = ['production_company', 'count']

    fig = px.pie(
        company_counts,
        names='production_company',
        values='count',
        hole=0.5,
        title=f"Top 7 Production Companies",
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    fig.update_traces(
        textinfo='percent',
        hovertemplate='%{label}<br>Movies: %{value}<br>Share: %{percent}<extra></extra>'
    )

    fig.update_layout(showlegend=True, height=400, width=400)
    return fig


def get_top10_bar_chart(df, country, feature):
    df = df.copy()
    df = df.explode('production_countries')
    df['production_countries'] = df['production_countries'].str.strip()
    label = features.get(feature, feature)
    df = df[df['production_countries'] == country].dropna(subset=[feature])
    top10 = df.sort_values(by=feature, ascending=False).head(10)

    if top10.empty:
        return go.Figure(layout={'title': f"No data for {country} - {label}"})

    fig = px.bar(
        top10,
        y='title',
        x=feature,
        color=feature,
        orientation='h',
        color_continuous_scale='viridis',
        title=f"Top 10 Movies in {country}",
        labels={feature: label, 'title': 'Movie'}
    )

    fig.update_layout(
        yaxis=dict(autorange='reversed'),
        xaxis_title=label,
        yaxis_title=None,
        plot_bgcolor='white',
        paper_bgcolor='white',
        title_font=dict(size=18, family='Arial'),
        coloraxis_colorbar=dict(title=label),
        height=500
    )
    return fig

def get_iso_alpha3_enhanced(country_name):
    manual_mapping = {
        'United States of America': 'USA', 'UK': 'GBR',
        'United Kingdom': 'GBR', 'Russia': 'RUS',
        'South Korea': 'KOR', 'North Korea': 'PRK',
        'Czech Republic': 'CZE', 'Iran': 'IRN',
        'Venezuela': 'VEN', 'Bolivia': 'BOL',
        'Taiwan': 'TWN', 'Moldova': 'MDA',
        'Vietnam': 'VNM', 'Macedonia': 'MKD'
    }
    if country_name in manual_mapping:
        return manual_mapping[country_name]
    try:
        return pycountry.countries.lookup(country_name).alpha_3
    except:
        return None




def genre_decade_sankey_by_country(df, country):
    df = df.copy()

    # Parse release_date and extract decade
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df = df[df['release_date'].notna()]
    df = df[df['release_date'].dt.year >= 1980]  # Filter for valid years
    df['decade'] = (df['release_date'].dt.year // 10 * 10).astype('Int64').astype(str) + 's'

    # Clean and explode production countries
    df['production_countries'] = df['production_countries'].astype(str).str.strip("[]").str.replace("'", "")
    df['production_countries'] = df['production_countries'].str.split(", ")
    df = df.explode('production_countries')
    df['production_countries'] = df['production_countries'].str.strip()
    df = df[df['production_countries'] == country]

    if df.empty:
        print(f"No data for country: {country}")
        return go.Figure()

    # Parse and explode genres
    df['genres'] = df['genres'].astype(str).str.strip("[]").str.replace("'", "")
    df['genres'] = df['genres'].str.split(", ")
    df = df.explode('genres')
    df['genres'] = df['genres'].str.strip()

    # Remove invalid genres
    df = df[df['genres'].notna()]
    df = df[~df['genres'].str.lower().isin(['', 'nan', 'none'])]

    # Determine top 5 genres for this country
    top_genres = df['genres'].value_counts().nlargest(5).index.tolist()
    df = df[df['genres'].isin(top_genres)]

    # Group genre → decade
    df2 = df.groupby(['genres', 'decade']).size().reset_index(name='count')
    df2['source'] = df2['genres']
    df2['target'] = df2['decade']

    # Map nodes to indices
    all_nodes = pd.unique(df2[['source', 'target']].values.ravel())
    node_map = {name: i for i, name in enumerate(all_nodes)}
    df2['source_id'] = df2['source'].map(node_map)
    df2['target_id'] = df2['target'].map(node_map)

    # Assign colors
    palette = px.colors.qualitative.Set3
    color_map = {name: palette[i % len(palette)] for i, name in enumerate(all_nodes)}
    node_colors = [color_map[name] for name in all_nodes]

    # Sankey diagram
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
        title_text=f"Genre → Decade Flow for {country} (Top 5 Genres)",
        font_size=10,
        height=400,
        width=550
    )
    return fig