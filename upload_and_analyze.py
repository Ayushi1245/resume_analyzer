import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("http://localhost:8501/")
        
        # Wait for file uploader input
        await page.wait_for_selector("input[type=file]", timeout=10000)
        print("File uploader input found.")
        
        # Upload the file
        await page.set_input_files("input[type=file]", "/Users/ayushi/Documents/notebook/resume_analyzer/dummy_resume.docx")
        print("File set.")
        
        # Wait for "Generate Dashboard Insights" button to appear
        button = await page.wait_for_selector("button:has-text('Analyze Resume')", timeout=10000)
        print("Generate button found.")
        
        # Click the button
        await button.click()
        print("Generate button clicked.")
        
        # Wait for 15 seconds for backend simulation
        await asyncio.sleep(15)
        
        # Save screenshot
        await page.screenshot(path="/Users/ayushi/Documents/notebook/resume_analyzer/analyzed_resume_result.png")
        print("Successfully uploaded and generated insights. Screenshot saved to analyzed_resume_result.png")
        
        await browser.close()

asyncio.run(main())
