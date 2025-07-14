import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import requests
import os
from pathlib import Path
import warnings
import gdown
warnings.filterwarnings("ignore")

def download_dataset():
    """
    Download the TMDB dataset from Google Drive and save it to the tabs directory.
    """
    # Google Drive file ID extracted from the shared link
    # Link: https://drive.google.com/file/d/1_yoz0hHydQkJKt8qNMFxykHJ0UOjj1hB/view?usp=sharing
    file_id = "1_yoz0hHydQkJKt8qNMFxykHJ0UOjj1hB"
    
    # Local file path
    tabs_dir = Path("tabs")
    tabs_dir.mkdir(exist_ok=True)
    local_file_path = tabs_dir / "TMDB_movie_dataset_v11.csv"
    
    # Check if file already exists
    if local_file_path.exists():
        print(f"Dataset already exists at {local_file_path}")
        return
    
    try:
        print("Downloading dataset from Google Drive...")
        
        # Use gdown for more reliable Google Drive downloads
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, str(local_file_path), quiet=False)
        
        print(f"Dataset successfully downloaded to {local_file_path}")
            
    except Exception as e:
        print(f"Error downloading dataset: {str(e)}")
        print("Please manually download the dataset and place it in the tabs/ directory as 'TMDB_movie_dataset_v11.csv'")

# Download dataset before initializing the app
download_dataset()

# Import tab modules after dataset is available
from tabs import overview, genre, country, company

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Cinescope Dash App"

# ✅ Register callbacks from each tab
overview.register_callbacks(app)
genre.register_callbacks(app)
country.register_callbacks(app)
company.register_callbacks(app)

# Define the main app layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),

    html.Div([
        html.H2("Navigation Window", className="sidebar-title"),
        html.Hr(),
        dcc.Link("Overview Tab", href="/overview", className="sidebar-link"),
        html.Br(),
        dcc.Link("Genre Tab", href="/genre", className="sidebar-link"),
        html.Br(),
        dcc.Link("Country Tab", href="/country", className="sidebar-link"),
        html.Br(),
        dcc.Link("Company Tab", href="/company", className="sidebar-link"),
    ], className="sidebar"),

    html.Div(id='page-content', className="content")
])

# Route different tabs
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname in ['/', '/overview']:
        return overview.layout() if callable(overview.layout) else overview.layout
    elif pathname == '/genre':
        return genre.layout() if callable(genre.layout) else genre.layout
    elif pathname == '/country':
        return country.layout() if callable(country.layout) else country.layout
    elif pathname == '/company':
        return company.layout() if callable(company.layout) else company.layout
    else:
        return html.H3("404: Page not found. Please use the sidebar to navigate.")

if __name__ == '__main__':
    app.run(debug=True)
