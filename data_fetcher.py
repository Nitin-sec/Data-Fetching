"""
Telegram Group Data Fetcher
Fetches messages from multiple Telegram groups within the last 6 hours
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from telethon.tl.types import Channel, Chat
import getpass
import time

class TelegramGroupFetcher:
    def __init__(self):
        self.client = None
        # HARDCODED CREDENTIALS - Replace with your actual values
        self.api_id = 21156764  # Replace with your actual API ID (integer)
        self.api_hash = "510953159b9f7d3359fe7a70a5cbf566"  # Replace with your actual API Hash
        self.phone = "+918178657157"  # Replace with your actual phone number (with country code)
        
    def get_credentials(self):
        """Validate hardcoded credentials"""
        print("=== Using Hardcoded Telegram API Credentials ===")
        print(f"API ID: {self.api_id}")
        print(f"API Hash: {self.api_hash[:8]}{'*' * (len(self.api_hash) - 8)}")  # Partially hide hash for security
        print(f"Phone: {self.phone[:3]}{'*' * (len(self.phone) - 3)}")  # Partially hide phone for security
        print()
        
        # Basic validation
        if not isinstance(self.api_id, int) or self.api_id <= 0:
            print("Error: API ID must be a valid positive integer!")
            print("Please update the api_id value in the code.")
            return False
            
        if not self.api_hash or self.api_hash == "your_api_hash_here":
            print("Error: Please replace 'your_api_hash_here' with your actual API Hash!")
            return False
            
        if not self.phone or self.phone == "+1234567890":
            print("Error: Please replace '+1234567890' with your actual phone number!")
            return False
            
        return True
    
    def get_group_names(self):
        """Get group names from user input"""
        print("\n=== Group Names ===")
        print("Enter the names of the groups you want to fetch data from.")
        print("Type 'done' when you're finished adding groups.")
        print()
        
        groups = []
        while True:
            group_name = input(f"Group {len(groups) + 1} name (or 'done' to finish): ").strip()
            if group_name.lower() == 'done':
                break
            if group_name:
                groups.append(group_name)
                print(f"Added: {group_name}")
        
        if not groups:
            print("Error: You must specify at least one group!")
            return None
            
        return groups
    
    async def connect_client(self):
        """Connect to Telegram and authenticate"""
        try:
            # Create client
            self.client = TelegramClient('session_name', self.api_id, self.api_hash)
            
            print("\nConnecting to Telegram...")
            await self.client.connect()
            
            # Check if already authorized
            if not await self.client.is_user_authorized():
                print(f"Sending code to {self.phone}...")
                await self.client.send_code_request(self.phone)
                
                # Get verification code
                code = input("Enter the verification code you received: ").strip()
                
                try:
                    await self.client.sign_in(self.phone, code)
                except SessionPasswordNeededError:
                    # Two-factor authentication is enabled
                    password = getpass.getpass("Enter your 2FA password: ")
                    await self.client.sign_in(password=password)
                    
            print("Successfully connected to Telegram!")
            return True
            
        except Exception as e:
            print(f"Error connecting to Telegram: {e}")
            return False
    
    async def find_group(self, group_name):
        """Find a group by name"""
        try:
            async for dialog in self.client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    if dialog.name.lower() == group_name.lower():
                        return dialog.entity
                    # Also check if the group name is contained in the dialog name
                    if group_name.lower() in dialog.name.lower():
                        return dialog.entity
            return None
        except Exception as e:
            print(f"Error finding group '{group_name}': {e}")
            return None
    
    async def fetch_messages_from_group(self, group, group_name, time_limit):
        """Fetch messages from a specific group within the time limit"""
        try:
            messages = []
            print(f"\nFetching messages from '{group_name}'...")
            
            async for message in self.client.iter_messages(group, limit=None):
                # Check if message is within time limit
                if message.date < time_limit:
                    break
                    
                messages.append({
                    'id': message.id,
                    'date': message.date,
                    'sender_id': message.sender_id,
                    'text': message.text or '',
                    'media': bool(message.media),
                    'forward_from': message.forward.original_fwd.from_id if message.forward else None,
                    'group_name': group_name
                })
                
                # Add a small delay to avoid hitting rate limits
                if len(messages) % 100 == 0:
                    await asyncio.sleep(0.1)
            
            print(f"Found {len(messages)} messages in '{group_name}' from the last 6 hours")
            return messages
            
        except FloodWaitError as e:
            print(f"Rate limited. Waiting {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)
            return await self.fetch_messages_from_group(group, group_name, time_limit)
        except Exception as e:
            print(f"Error fetching messages from '{group_name}': {e}")
            return []
    
    def format_message_output(self, message):
        """Format a message for terminal output"""
        output = []
        output.append("=" * 80)
        output.append(f"GROUP: {message['group_name']}")
        output.append(f"MESSAGE ID: {message['id']}")
        output.append(f"DATE: {message['date'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
        output.append(f"SENDER ID: {message['sender_id']}")
        
        if message['forward_from']:
            output.append(f"FORWARDED FROM: {message['forward_from']}")
        
        if message['media']:
            output.append("MEDIA: Yes")
        
        output.append("MESSAGE:")
        if message['text']:
            # Split long messages into multiple lines for better readability
            text_lines = message['text'].split('\n')
            for line in text_lines:
                if len(line) > 120:
                    # Break very long lines
                    while len(line) > 120:
                        output.append(f"  {line[:120]}")
                        line = line[120:]
                    if line:
                        output.append(f"  {line}")
                else:
                    output.append(f"  {line}")
        else:
            output.append("  [No text content]")
        
        return '\n'.join(output)
    
    async def run(self):
        """Main execution function"""
        print("Telegram Group Data Fetcher")
        print("=" * 40)
        
        # Get credentials
        if not self.get_credentials():
            return
        
        # Get group names
        group_names = self.get_group_names()
        if not group_names:
            return
        
        # Connect to Telegram
        if not await self.connect_client():
            return
        
        try:
            # Calculate time limit (6 hours ago) with UTC timezone
            time_limit = datetime.now(timezone.utc) - timedelta(hours=6)
            print(f"\nFetching messages newer than: {time_limit.strftime('%Y-%m-%d %H:%M:%S')}")
            
            all_messages = []
            
            # Process each group
            for group_name in group_names:
                print(f"\nSearching for group: '{group_name}'...")
                
                group = await self.find_group(group_name)
                if not group:
                    print(f"Group '{group_name}' not found! Make sure you're a member of this group.")
                    continue
                
                print(f"Found group: {group.title}")
                
                # Fetch messages
                messages = await self.fetch_messages_from_group(group, group_name, time_limit)
                all_messages.extend(messages)
            
            # Sort messages by date (newest first)
            all_messages.sort(key=lambda x: x['date'], reverse=True)
            
            # Display results
            print(f"\n{'='*80}")
            print(f"SUMMARY")
            print(f"{'='*80}")
            print(f"Total messages found: {len(all_messages)}")
            print(f"Time range: Last 6 hours from {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Groups processed: {len(group_names)}")
            
            if all_messages:
                print(f"\n{'='*80}")
                print(f"MESSAGES")
                print(f"{'='*80}")
                
                for message in all_messages:
                    print(self.format_message_output(message))
                    print()  # Add spacing between messages
            else:
                print("\nNo messages found in the specified time range.")
                
        except Exception as e:
            print(f"Error during execution: {e}")
        finally:
            # Disconnect from Telegram
            if self.client:
                await self.client.disconnect()
                print("\nDisconnected from Telegram.")

# Main execution
if __name__ == "__main__":
    fetcher = TelegramGroupFetcher()
    asyncio.run(fetcher.run())