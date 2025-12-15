const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  const page = await context.newPage();
  
  try {
    // Go to login page
    await page.goto('https://atlas-crm.alexandratechlab.com/users/login/', { timeout: 30000 });
    
    // Fill login form
    await page.fill('input[name="email"]', 'superadmin@atlas.com');
    await page.fill('input[name="password"]', 'Atlas@2024!');
    
    // Click submit and wait for navigation
    await Promise.all([
      page.waitForNavigation({ timeout: 10000 }).catch(() => null),
      page.click('button[type="submit"]')
    ]);
    
    await page.waitForTimeout(2000);
    console.log('After login URL:', page.url());
    
    // Check if we're on dashboard
    if (page.url().includes('dashboard') || !page.url().includes('login')) {
      console.log('LOGIN SUCCESS!');
      
      // Now test audit logs page
      await page.goto('https://atlas-crm.alexandratechlab.com/settings/audit-logs/', { timeout: 30000 });
      await page.waitForLoadState('networkidle');
      
      console.log('Audit logs URL:', page.url());
      
      // Check content
      const content = await page.content();
      if (content.includes('Server Error') || content.includes('500')) {
        console.log('ERROR: Audit logs page has server error!');
      } else if (content.includes('Audit Logs') || content.includes('audit')) {
        console.log('SUCCESS: Audit logs page loads correctly!');
      } else {
        console.log('Page title:', await page.title());
        console.log('Content sample:', content.substring(0, 500));
      }
    } else {
      console.log('LOGIN FAILED - still on login page');
      const errorMsg = await page.$$eval('.text-red-500, .error, .text-red-600', 
        elements => elements.map(el => el.innerText.trim()).filter(t => t.length > 0)
      );
      console.log('Error messages:', errorMsg);
    }
    
  } catch (e) {
    console.log('Error:', e.message);
  } finally {
    await browser.close();
  }
})();
