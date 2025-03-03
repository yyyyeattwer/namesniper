import aiohttp
import asyncio
import random
import string
import os
import signal

# Configurations
USERNAME_LENGTHS = [4, 5] # customize to ur liking
CHECKS_PER_BATCH = 130 
CONCURRENT_TASKS = 50  
RETRY_ATTEMPTS = 5  
DELAY_BETWEEN_BATCHES = 0.5 

# Output files
HITS_FILE = "hits.txt"
LOG_FILE = "log.txt"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36"
]

# track usernames
checked_usernames = set()

# generate users
def generate_unique_usernames(count):
    new_usernames = set()
    while len(new_usernames) < count:
        username = ''.join(random.choices(string.ascii_lowercase, k=random.choice(USERNAME_LENGTHS)))
        if username not in checked_usernames:
            checked_usernames.add(username)
            new_usernames.add(username)
    return list(new_usernames)

# checks if a username is available
async def check_username_availability(session, username):
    url = f"https://auth.roblox.com/v1/usernames/validate?username={username}&birthday=2000-01-01"
    headers = {"User-Agent": random.choice(USER_AGENTS)}

    for _ in range(RETRY_ATTEMPTS):
        try:
            async with session.get(url, headers=headers, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return username, data.get("code") == 0
        except:
            await asyncio.sleep(0.5) 
    return username, False

# process usernames
async def process_usernames():
    async with aiohttp.ClientSession() as session:
        while True:
            usernames = generate_unique_usernames(CHECKS_PER_BATCH)
            tasks = [check_username_availability(session, username) for username in usernames]

            results = await asyncio.gather(*tasks)

            with open(HITS_FILE, "a") as hits, open(LOG_FILE, "a") as log:
                for username, available in results:
                    log.write(username + "\n")
                    if available:
                        hits.write(username + "\n")
                        print(f"[✅] Available: {username}")
                    else:
                        print(f"[❌] Taken: {username}")

            print(f"\n✅ Batch complete. Waiting {DELAY_BETWEEN_BATCHES}s before next batch...")
            await asyncio.sleep(DELAY_BETWEEN_BATCHES)

# clean up files on exit
def cleanup():
    print("\n🧹 Cleaning up before exit...")
    for file in [LOG_FILE, HITS_FILE]:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"🗑️ Deleted {file}")
        except Exception as e:
            print(f"⚠️ Error deleting {file}: {e}")


def signal_handler(sig, frame):
    cleanup()
    print("Exiting..")
    exit(0)


signal.signal(signal.SIGINT, signal_handler)  # Handle CTRL+C
signal.signal(signal.SIGTERM, signal_handler)  # Handle process termination


async def main():
    await process_usernames()  # Runs indefinitely


try:
    asyncio.run(main())
except KeyboardInterrupt:
    cleanup()
    print("Script stopped by user.")
