"""
Helper script to generate a Pyrogram String Session for the Voice Chat Assistant.
Run this script:
    .\venv\Scripts\python.exe generate_session.py
"""

import asyncio
from pathlib import Path
import re
from pyrogram import Client
import config

async def main():
    print("=" * 60)
    print(" Telegram Assistant Session String Generator (Pyrogram v2)")
    print("=" * 60)

    api_id = config.API_ID
    api_hash = config.API_HASH

    if api_id and api_hash:
        print(f"ℹ️ Found credentials in .env (API_ID: {api_id})")
        use_env = input("Use these credentials from .env? (Y/n, default Y): ").strip().lower()
        if use_env in ("n", "no"):
            api_id = None

    if not api_id or not api_hash:
        try:
            api_id_input = input("Enter your API_ID: ").strip()
            api_id = int(api_id_input)
            api_hash = input("Enter your API_HASH: ").strip()
        except ValueError:
            print("\n❌ Error: API_ID must be an integer.")
            return

    print("\nStarting authentication client...")
    print("Telegram will ask for your phone number and send a confirmation code.\n")

    async with Client(
        name="assistant_session_generator",
        api_id=api_id,
        api_hash=api_hash,
        in_memory=True
    ) as app:
        session_str = await app.export_session_string()
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Assistant Session String generated.")
        print("=" * 60)

        # Option to automatically save to .env
        env_path = Path(__file__).resolve().parent / ".env"
        if env_path.exists():
            save_env = input("Automatically save this SESSION_STRING to your .env file? (Y/n, default Y): ").strip().lower()
            if save_env not in ("n", "no"):
                content = env_path.read_text(encoding="utf-8")
                if re.search(r"^SESSION_STRING=.*$", content, flags=re.MULTILINE):
                    new_content = re.sub(r"^SESSION_STRING=.*$", f"SESSION_STRING={session_str}", content, flags=re.MULTILINE)
                else:
                    new_content = content + f"\nSESSION_STRING={session_str}\n"
                env_path.write_text(new_content, encoding="utf-8")
                print("✅ Successfully saved SESSION_STRING into .env!")

        print("\n" + "=" * 60)
        print("Your SESSION_STRING (backup copy):")
        print(session_str)
        print("=" * 60)
        print("⚠️ Keep this session string SECRET! Never share it publicly.\n")

if __name__ == "__main__":
    asyncio.run(main())
