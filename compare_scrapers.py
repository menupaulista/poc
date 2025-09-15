#!/usr/bin/env python3
"""Utility script to compare original vs modular scraper performance."""

import asyncio
import time
import subprocess
import sys
from pathlib import Path


async def run_command(cmd, description):
    """Run a command and measure execution time."""
    print(f"\n🚀 {description}")
    print("=" * 50)

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=300
        )
        end_time = time.time()
        duration = end_time - start_time

        if result.returncode == 0:
            print(f"✅ Success! Duration: {duration:.2f}s")
            print("Output:")
            print(result.stdout[-500:])  # Last 500 characters
        else:
            print(f"❌ Failed! Duration: {duration:.2f}s")
            print("Error:")
            print(result.stderr)

        return duration, result.returncode == 0

    except subprocess.TimeoutExpired:
        print("⏰ Timeout after 5 minutes")
        return 300, False


async def main():
    """Compare both scrapers."""
    print("🔍 Comparing Original vs Modular Scraper")
    print("Testing with 20 items each...")

    # Original scraper
    original_cmd = 'python scraper.py --seed-url "https://doisporum.net/" --max-items 20 --csv-path "compare_original.csv" --jsonl-path "compare_original.jsonl"'
    original_duration, original_success = await run_command(
        original_cmd, "Running Original Scraper"
    )

    # Wait a bit between tests
    await asyncio.sleep(2)

    # Modular scraper
    modular_cmd = 'python main_modular.py --seed-url "https://doisporum.net/" --max-items 20 --csv-path "compare_modular.csv" --jsonl-path "compare_modular.jsonl"'
    modular_duration, modular_success = await run_command(
        modular_cmd, "Running Modular Scraper"
    )

    # Summary
    print("\n📊 COMPARISON SUMMARY")
    print("=" * 50)
    print(
        f"Original Scraper: {original_duration:.2f}s {'✅' if original_success else '❌'}"
    )
    print(
        f"Modular Scraper:  {modular_duration:.2f}s {'✅' if modular_success else '❌'}"
    )

    if original_success and modular_success:
        if modular_duration < original_duration:
            improvement = (
                (original_duration - modular_duration) / original_duration
            ) * 100
            print(f"🎉 Modular is {improvement:.1f}% faster!")
        elif original_duration < modular_duration:
            slowdown = (
                (modular_duration - original_duration) / original_duration
            ) * 100
            print(
                f"⚠️  Modular is {slowdown:.1f}% slower (expected due to import overhead)"
            )
        else:
            print("⚖️  Both scrapers have similar performance")

    # File comparison
    try:
        original_csv = Path("compare_original.csv")
        modular_csv = Path("compare_modular.csv")

        if original_csv.exists() and modular_csv.exists():
            original_size = original_csv.stat().st_size
            modular_size = modular_csv.stat().st_size

            print(f"\nFile sizes:")
            print(f"Original CSV: {original_size:,} bytes")
            print(f"Modular CSV:  {modular_size:,} bytes")

            if abs(original_size - modular_size) < 100:
                print("✅ Output files are very similar in size")
            else:
                print("⚠️  Output files have different sizes - check content")
    except Exception as e:
        print(f"Could not compare file sizes: {e}")

    print("\n🎯 Modular Benefits:")
    print("• Better code organization and maintainability")
    print("• Easier testing and debugging")
    print("• Follows SOLID principles")
    print("• More extensible and reusable")
    print("• Cleaner separation of concerns")


if __name__ == "__main__":
    asyncio.run(main())
