"""
Telegram Media Fetching and Per-Second Rate Limit Tester
Tests media download capabilities and precise per-second API limits
"""

import asyncio
import time
import os
from datetime import datetime
from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError
import getpass

class TelegramMediaRateTester:
    def __init__(self):
        # Replace with your actual credentials
        self.api_id = 12345678  # Replace with your actual API ID
        self.api_hash = "your_api_hash_here"  # Replace with your actual API Hash  
        self.phone = "+1234567890"  # Replace with your actual phone number

        self.client = None
        
    async def connect(self):
        """Connect to Telegram"""
        self.client = TelegramClient('media_test_session', self.api_id, self.api_hash)
        await self.client.connect()
        
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone)
            code = input("Enter verification code: ")
            
            try:
                await self.client.sign_in(self.phone, code)
            except SessionPasswordNeededError:
                password = getpass.getpass("Enter your 2FA password: ")
                await self.client.sign_in(password=password)
        
        print("Connected to Telegram API")
    
    async def test_media_detection_and_download(self):
        """Test media detection and download capabilities"""
        print("\n=== Testing Media Detection & Download ===")
        
        # Get first available channel/group
        dialogs = await self.client.get_dialogs()
        test_chat = None
        
        for dialog in dialogs:
            if dialog.is_group or dialog.is_channel:
                test_chat = dialog.entity
                print(f"Testing with: {dialog.name}")
                break
        
        if not test_chat:
            print("No groups/channels found for testing")
            return
        
        media_found = 0
        messages_checked = 0
        
        print("Scanning for media messages...")
        
        async for message in self.client.iter_messages(test_chat, limit=50):
            messages_checked += 1
            
            if message.media:
                media_found += 1
                print(f"\nMessage {messages_checked}: MEDIA FOUND")
                print(f"  Message ID: {message.id}")
                print(f"  Date: {message.date}")
                print(f"  Media Type: {type(message.media).__name__}")
                
                # Check different media types
                if message.photo:
                    print(f"  Photo: Yes")
                    # Test download
                    try:
                        file_path = f"test_photo_{message.id}.jpg"
                        await message.download_media(file_path)
                        file_size = os.path.getsize(file_path)
                        print(f"  Downloaded: {file_path} ({file_size} bytes)")
                        os.remove(file_path)  # Clean up
                    except Exception as e:
                        print(f"  Download failed: {e}")
                
                elif message.video:
                    print(f"  Video: Yes")
                    try:
                        print(f"  Duration: {message.video.duration}s")
                        print(f"  Size: {message.video.size} bytes")
                    except:
                        print(f"  Video details unavailable")
                
                elif message.document:
                    print(f"  Document: Yes")
                    print(f"  Size: {message.document.size} bytes")
                    # Check if document is actually a video
                    if message.document.mime_type and 'video' in message.document.mime_type:
                        print(f"  Document Type: Video")
                    elif message.document.mime_type:
                        print(f"  MIME Type: {message.document.mime_type}")
                    
                    # Try to download small document
                    if message.document.size < 1000000:  # Less than 1MB
                        try:
                            file_path = f"test_doc_{message.id}"
                            await message.download_media(file_path)
                            file_size = os.path.getsize(file_path)
                            print(f"  Downloaded: {file_path} ({file_size} bytes)")
                            os.remove(file_path)  # Clean up
                        except Exception as e:
                            print(f"  Download failed: {e}")
                    else:
                        print(f"  File too large to test download ({message.document.size} bytes)")
                
                elif message.voice:
                    print(f"  Voice: Yes")
                    print(f"  Duration: {message.voice.duration}s")
                
                elif message.sticker:
                    print(f"  Sticker: Yes")
                
                # Stop after finding 3 media files
                if media_found >= 3:
                    break
        
        print(f"\nMedia Detection Summary:")
        print(f"Messages checked: {messages_checked}")
        print(f"Media messages found: {media_found}")
        print(f"Media detection rate: {(media_found/messages_checked)*100:.1f}%")
    
    async def test_per_second_rate_limit(self):
        """Test exact per-second API call limits"""
        print("\n=== Testing Per-Second Rate Limits ===")
        
        # Test 1: Calls per second
        print("\nTest 1: Maximum calls per second")
        calls_per_second = []
        
        for second in range(5):  # Test for 5 seconds
            start_time = time.time()
            call_count = 0
            
            try:
                while time.time() - start_time < 1.0:  # Within 1 second
                    await self.client.get_me()
                    call_count += 1
                    
            except FloodWaitError as e:
                print(f"Second {second+1}: Rate limited after {call_count} calls (wait {e.seconds}s)")
                calls_per_second.append(call_count)
                await asyncio.sleep(e.seconds)
                continue
            
            print(f"Second {second+1}: {call_count} calls completed")
            calls_per_second.append(call_count)
            
            # Wait for next second
            await asyncio.sleep(1)
        
        avg_calls = sum(calls_per_second) / len(calls_per_second)
        print(f"Average calls per second: {avg_calls:.1f}")
        
        # Test 2: Message fetching per second
        print("\nTest 2: Message fetching per second")
        
        dialogs = await self.client.get_dialogs()
        test_chat = None
        for dialog in dialogs:
            if dialog.is_group or dialog.is_channel:
                test_chat = dialog.entity
                break
        
        if test_chat:
            messages_per_second = []
            
            for second in range(3):  # Test for 3 seconds
                start_time = time.time()
                message_count = 0
                
                try:
                    async for message in self.client.iter_messages(test_chat, limit=100):
                        message_count += 1
                        if time.time() - start_time >= 1.0:
                            break
                            
                except FloodWaitError as e:
                    print(f"Second {second+1}: Rate limited after {message_count} messages (wait {e.seconds}s)")
                    messages_per_second.append(message_count)
                    await asyncio.sleep(e.seconds)
                    continue
                
                elapsed = time.time() - start_time
                print(f"Second {second+1}: {message_count} messages in {elapsed:.2f}s")
                messages_per_second.append(message_count)
                
                await asyncio.sleep(1)
            
            avg_messages = sum(messages_per_second) / len(messages_per_second)
            print(f"Average messages per second: {avg_messages:.1f}")
    
    async def test_burst_vs_sustained(self):
        """Test burst calls vs sustained calls"""
        print("\n=== Testing Burst vs Sustained Calls ===")
        
        # Burst test
        print("Burst test: 20 rapid calls")
        start_time = time.time()
        burst_count = 0
        
        try:
            for i in range(20):
                await self.client.get_me()
                burst_count += 1
        except FloodWaitError as e:
            burst_time = time.time() - start_time
            print(f"Burst: {burst_count} calls in {burst_time:.2f}s before rate limit (wait {e.seconds}s)")
            await asyncio.sleep(e.seconds)
        else:
            burst_time = time.time() - start_time
            print(f"Burst: {burst_count} calls completed in {burst_time:.2f}s")
        
        # Sustained test
        print("Sustained test: 20 calls with 0.5s delay")
        start_time = time.time()
        sustained_count = 0
        
        try:
            for i in range(20):
                await self.client.get_me()
                sustained_count += 1
                await asyncio.sleep(0.5)
        except FloodWaitError as e:
            sustained_time = time.time() - start_time
            print(f"Sustained: {sustained_count} calls in {sustained_time:.2f}s before rate limit")
        else:
            sustained_time = time.time() - start_time
            print(f"Sustained: {sustained_count} calls completed in {sustained_time:.2f}s")
    
    async def run_tests(self):
        """Run all tests"""
        print("Telegram Media & Rate Limit Tester")
        print("=" * 50)
        print(f"Test started at: {datetime.now()}")
        
        await self.connect()
        
        # Test media capabilities
        await self.test_media_detection_and_download()
        
        # Test per-second limits
        await self.test_per_second_rate_limit()
        
        # Test burst vs sustained
        await self.test_burst_vs_sustained()
        
        print(f"\n{'='*50}")
        print("TESTING COMPLETED")
        print(f"{'='*50}")
        
        await self.client.disconnect()

if __name__ == "__main__":
    tester = TelegramMediaRateTester()
    asyncio.run(tester.run_tests())