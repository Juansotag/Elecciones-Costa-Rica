# Instagram Scraper Tool

A Python-based tool to scrape Instagram account metadata (followers) and recent posts (likes, comments) using [Instaloader](https://instaloader.github.io/). It supports both single-account scraping and batch processing via a text file, exporting results to CSV.

## Features

- **Account Metadata**: Fetches current follower count.
- **Recent Posts**: Retrieves posts from the last N days.
- **Engagement Metrics**: Captures likes and comments count for each post.
- **Batch Processing**: Scrapes multiple accounts from a list.
- **CSV Export**: Saves structured data to a CSV file.
- **Rate Limit Protection**: Implements random delays between accounts to avoid IP bans.

## Prerequisites

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) (recommended for fast virtual environment management) or standard `pip`.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd instagram_scraper
   ```

2. **Set up a virtual environment**:
   Using `uv` (recommended):
   ```bash
   uv venv
   .\.venv\Scripts\activate  # On Windows
   # source .venv/bin/activate # On macOS/Linux
   ```
   
   Or using standard `venv`:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**:
   ```bash
   uv pip install -r requirements.txt
   # or
   pip install -r requirements.txt
   ```

## Usage

### 1. Batch Scraping (Recommended)

This mode reads a list of accounts from a file and saves all results to a CSV.

1. **Prepare the accounts list**:
   Edit `accounts.txt` and add one Instagram username per line:
   ```text
   instagram
   nasa
   natgeo
   ```

2. **Run the scraper**:
   ```bash
   python batch_scraper.py --days <number_of_days>
   ```
   
   Example (fetch posts from the last 3 days):
   ```bash
   python batch_scraper.py --days 3
   ```

3. **Check Results**:
   Data will be saved to `results.csv` (this file is automatically created after the first run).
   - `date_fetch`: Date of execution
   - `time_fetch`: Time of execution
   - `time_window`: Input days parameter
   - `account`: Instagram username
   - `followers`: Current follower count
   - `post_timestamp`: Date/Time of the post
   - `likes`: Number of likes
   - `comments`: Number of comments

### 2. Single Account Scraping

Useful for quick checks or debugging.

```bash
python scraper.py --user <username> --days <number_of_days>
```

Example:
```bash
python scraper.py --user natgeo --days 1
```

## Rate Limits & Disclaimer

**Important**: Instagram has strict rate limits.
- This tool includes a random delay (20-40 seconds) between accounts in batch mode to mimic human behavior.
- Avoid scraping hundreds of accounts in a single run without using proxies or authenticated sessions (not currently implemented).
- Excessive scraping may lead to temporary IP blocks (HTTP 429 errors).

## License

[MIT](LICENSE)
