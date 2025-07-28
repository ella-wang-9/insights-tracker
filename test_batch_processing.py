#!/usr/bin/env python3
"""Test script for batch processing functionality using Playwright"""

import asyncio
from playwright.async_api import async_playwright
import time

async def test_batch_processing():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # Navigate to the app
        await page.goto('http://localhost:5173')
        await page.wait_for_load_state('networkidle')
        
        print("1. Going to Schema Builder tab...")
        await page.click('button:has-text("Schema Builder")')
        await page.wait_for_timeout(1000)
        
        print("2. Selecting default schema template...")
        # Look for Product Feedback Template
        template_selector = page.locator('text="Product Feedback Template"').first
        if await template_selector.is_visible():
            await template_selector.click()
            print("   ✓ Selected Product Feedback Template")
        else:
            print("   ! Product Feedback Template not found, looking for any template...")
            # Click the first available template
            await page.locator('.cursor-pointer').first.click()
        
        await page.wait_for_timeout(1000)
        
        print("3. Going to Batch Process tab...")
        await page.click('button:has-text("Batch Process")')
        await page.wait_for_timeout(1000)
        
        print("4. Filling Document 1...")
        # Find the first textarea
        textarea1 = page.locator('textarea').nth(0)
        await textarea1.fill("Meeting with TechCorp on March 15, 2024. They need MLflow for model tracking.")
        
        print("5. Adding another document...")
        await page.click('button:has-text("Add Another Document")')
        await page.wait_for_timeout(500)
        
        print("6. Filling Document 2...")
        textarea2 = page.locator('textarea').nth(1)
        await textarea2.fill("DataCorp discussion on April 22, 2024. Interested in Unity Catalog for data governance.")
        
        print("7. Adding another document...")
        await page.click('button:has-text("Add Another Document")')
        await page.wait_for_timeout(500)
        
        print("8. Changing Document 3 to File type...")
        # Click the third Select trigger (shadcn/ui component)
        select_trigger3 = page.locator('[role="combobox"]').nth(2)
        await select_trigger3.click()
        await page.wait_for_timeout(500)
        
        # Click on the File option in the dropdown
        await page.locator('[role="option"]:has-text("File")').click()
        await page.wait_for_timeout(500)
        
        print("9. Taking screenshot with file upload option...")
        await page.screenshot(path='batch_process_file_upload.png')
        print("   ✓ Screenshot saved: batch_process_file_upload.png")
        
        print("10. Changing Document 3 back to Text...")
        # Click the third Select trigger again
        await select_trigger3.click()
        await page.wait_for_timeout(500)
        
        # Click on the Text option in the dropdown
        await page.locator('[role="option"]:has-text("Text")').click()
        await page.wait_for_timeout(500)
        
        print("11. Filling Document 3...")
        textarea3 = page.locator('textarea').nth(2)
        await textarea3.fill("CloudCorp meeting May 5, 2024. Need Vector Search for recommendations.")
        
        print("12. Clicking Analyze & Download...")
        analyze_button = page.locator('button:has-text("Analyze & Download")')
        await analyze_button.click()
        
        # Wait for response
        print("13. Waiting for analysis results...")
        await page.wait_for_timeout(3000)
        
        # Check for any error messages or success indicators
        error_msg = page.locator('.text-red-500, .text-destructive')
        success_msg = page.locator('.text-green-500, .text-success')
        
        if await error_msg.count() > 0:
            error_text = await error_msg.first.text_content()
            print(f"   ! Error occurred: {error_text}")
        elif await success_msg.count() > 0:
            success_text = await success_msg.first.text_content()
            print(f"   ✓ Success: {success_text}")
        else:
            print("   ? No clear success/error message found")
        
        # Check if download started
        download_started = False
        try:
            # Wait for download event
            async with page.expect_download(timeout=5000) as download_info:
                download = await download_info.value
                print(f"   ✓ Download started: {download.suggested_filename}")
                download_started = True
        except:
            print("   ? No download detected")
        
        print("14. Taking final screenshot...")
        await page.screenshot(path='batch_process_final.png')
        print("   ✓ Screenshot saved: batch_process_final.png")
        
        # Keep browser open for a moment
        await page.wait_for_timeout(2000)
        
        await browser.close()
        print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(test_batch_processing())