# Telegram Group Data Fetcher

Fetches messages from multiple Telegram groups within the last 6 hours.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get Telegram API credentials:**
   - Go to https://my.telegram.org/apps
   - Create a new application
   - Note down your API ID and API Hash

3. **Update credentials in code:**
   - Open `data_fetcher.py`
   - Replace placeholder values with your actual credentials:
     ```python
     self.api_id = your_actual_api_id
     self.api_hash = "your_actual_api_hash"
     self.phone = "+your_phone_number"
     ```

## Usage

```bash
python data_fetcher.py
```

## Security

- Never commit `*.session` files to git
- Keep your API credentials private
- The `.gitignore` file excludes sensitive files automatically

## Rate Limits

- Run 2-4 times per day maximum
- Space runs at least 2-3 hours apart
- The script handles rate limiting automatically