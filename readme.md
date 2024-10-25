# Spotify Playlist Analyzer

This project analyzes Spotify playlists by fetching playlist items, artist genres, and track audio features. The data is then saved in JSON and Excel formats.

## Prerequisites

- Python 3.x
- `requests` library
- `pandas` library
- Spotify API credentials (`SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`)

## Setup

1. Clone the repository:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Install the required Python packages:
    ```sh
    pip install requests pandas
    ```

3. Set up your Spotify API credentials as environment variables:
    ```sh
    export SPOTIFY_CLIENT_ID='your_client_id'
    export SPOTIFY_CLIENT_SECRET='your_client_secret'
    ```

## Usage

Run the script to fetch and analyze the playlist data:
```sh
python spotifyAnalyser.py