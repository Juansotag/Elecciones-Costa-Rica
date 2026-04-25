# X.com Scraper

A robust Python-based web scraper for X.com (formerly Twitter) using Playwright. This tool fetches posts from a list of accounts within a specified date range, extracting detailed metrics and handling dynamic content like infinite scrolling.

## Features

- **Multi-Account Support**: Reads account handles from `accounts.txt`.
- **Date Filtering**: Scrapes posts from the last `N` days.
- **Detailed Metrics**: Extracts:
  - Post text (sanitized to single line)
  - Date and time
  - Likes, Comments, Reposts counts
  - Follower count for the account
  - Post ID and URL
- **Smart Filtering**:
  - **Includes Quotes**: Correctly identifies and includes Quote Tweets authored by the target account.
  - **Excludes Reposts**: Filters out direct Reposts to ensure only original content (and quotes) is captured.
- **Robustness**:
  - Handles login persistence (you only log in once).
  - Implements "stuck" detection and date-based stopping to prevent infinite loops.
  - Retries on network glitches.
- **Output**: Appends data to `results.csv` to preserve history across runs.

## Prerequisites

- Python 3.8+
- [Playwright](https://playwright.dev/python/)

## Installation

1.  **Clone the repository** (or download the files).

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright browsers**:
    ```bash
    playwright install chromium
    ```

## Usage

1.  **Configure Accounts**:
    Edit `accounts.txt` and add the X.com handles you want to scrape, one per line.
    ```text
    SpaceX
    NASA
    Tesla
    ```

2.  **Run the Scraper**:
    ```bash
    python main.py
    ```

3.  **Authenticate (First Run Only)**:
    -   The script will launch a browser window.
    -   If you are not logged in, it will pause and ask you to log in to X.com manually in that window.
    -   Once logged in, the script will detect the session and proceed automatically.
    -   Session data is saved in the `user_data/` directory, so you won't need to log in again frequently.

4.  **Input Date Range**:
    -   The script will ask: `Enter N (number of days to look back):`
    -   Enter a number (e.g., `7`) to scrape posts from the last week.

5.  **View Results**:
    -   Data is saved to `results.csv` in the project directory.

## Output Format (`results.csv`)

| Column | Description |
| :--- | :--- |
| `fetch_datetime` | Timestamp when the data was scraped |
| `fetch_N_days` | The `N` days parameter used for this run |
| `account` | The account handle being scraped |
| `followers` | Number of followers for the account |
| `post_datetime` | Timestamp of the post |
| `post_comments` | Number of replies/comments |
| `post_likes` | Number of likes |
| `post_reposts` | Number of reposts |
| `post_id` | Unique ID of the tweet |
| `post_text` | The content of the tweet (single line) |

## Troubleshooting

-   **Login Issues**: If the script gets stuck waiting for login, ensure you are on the Home timeline (`https://x.com/home`) after logging in.
-   **Missing Tweets**: The script uses a safe scrolling mechanism. If your internet connection is very slow, you might need to adjust the `wait_for_timeout` values in `main.py`.
-   **Strict Mode Errors**: If you see errors related to "strict mode violation", ensure you are using the latest version of the script which handles Quote Tweets correctly using `.first` locators.

## License

[MIT](LICENSE)
