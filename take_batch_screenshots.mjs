import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

console.log('Navigating to http://localhost:5173...');
await page.goto('http://localhost:5173');
await page.waitForLoadState('networkidle');

// Take screenshot of main page with all tabs
console.log('Taking screenshot of main page...');
await page.screenshot({ 
  path: '/tmp/01_main_page_all_tabs.png',
  fullPage: true 
});

// Click on Batch Process tab
console.log('Clicking on Batch Process tab...');
await page.click('button:has-text("Batch Process")');
await page.waitForTimeout(1500); // Wait for tab content to load

// Take screenshot of batch process tab
console.log('Taking screenshot of Batch Process tab...');
await page.screenshot({ 
  path: '/tmp/02_batch_process_initial.png',
  fullPage: true 
});

// Try to find and click "Add Another Document" button
try {
  console.log('Looking for "Add Another Document" button...');
  const addButton = await page.waitForSelector('button:has-text("Add Another Document")', { timeout: 5000 });
  
  if (addButton) {
    console.log('Found button, clicking...');
    await addButton.click();
    await page.waitForTimeout(1000);
    
    // Take screenshot after adding another document
    console.log('Taking screenshot with multiple documents...');
    await page.screenshot({ 
      path: '/tmp/03_batch_process_two_docs.png',
      fullPage: true 
    });
    
    // Click add button one more time
    console.log('Adding one more document...');
    await addButton.click();
    await page.waitForTimeout(1000);
    
    console.log('Taking screenshot with three documents...');
    await page.screenshot({ 
      path: '/tmp/04_batch_process_three_docs.png',
      fullPage: true 
    });
  }
} catch (error) {
  console.log('Could not find "Add Another Document" button:', error.message);
}

console.log('Done! Screenshots saved to /tmp/');
await browser.close();