/**
 * PA11Y ACCESSIBILITY TESTING
 * ===========================
 * Uses Pa11y to perform comprehensive accessibility audits
 * following WCAG 2.1 Level AA standards.
 *
 * Run: node tests/pa11y_accessibility.js
 */

const pa11y = require('pa11y');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://atlas-crm.alexandratechlab.com';

// Pages to test
const PAGES = [
  { name: 'Login Page', url: '/users/login/' },
  { name: 'Landing Page', url: '/' },
];

// Pa11y configuration
const pa11yOptions = {
  standard: 'WCAG2AA',
  timeout: 60000,
  wait: 2000,
  chromeLaunchConfig: {
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--headless'],
  },
  ignore: [
    // Ignore specific rules if needed
    // 'WCAG2AA.Principle1.Guideline1_4.1_4_3.G18.Fail'
  ],
};

// Results storage
const results = {
  timestamp: new Date().toISOString(),
  standard: 'WCAG2AA',
  pages: [],
  summary: {
    totalPages: 0,
    totalErrors: 0,
    totalWarnings: 0,
    totalNotices: 0,
    passedPages: 0,
    failedPages: 0,
  },
};

async function testPage(page) {
  const fullUrl = `${BASE_URL}${page.url}`;
  console.log(`\nTesting: ${page.name}`);
  console.log(`URL: ${fullUrl}`);

  try {
    const pageResults = await pa11y(fullUrl, pa11yOptions);

    const errors = pageResults.issues.filter(i => i.type === 'error');
    const warnings = pageResults.issues.filter(i => i.type === 'warning');
    const notices = pageResults.issues.filter(i => i.type === 'notice');

    const pageResult = {
      name: page.name,
      url: fullUrl,
      errors: errors.length,
      warnings: warnings.length,
      notices: notices.length,
      passed: errors.length === 0,
      issues: pageResults.issues.slice(0, 20), // Limit to top 20 issues
    };

    // Print summary
    console.log(`  Errors: ${errors.length > 0 ? '\x1b[31m' : '\x1b[32m'}${errors.length}\x1b[0m`);
    console.log(`  Warnings: ${warnings.length > 0 ? '\x1b[33m' : '\x1b[32m'}${warnings.length}\x1b[0m`);
    console.log(`  Notices: ${notices.length}`);
    console.log(`  Status: ${pageResult.passed ? '\x1b[32mPASSED\x1b[0m' : '\x1b[31mFAILED\x1b[0m'}`);

    // Print top errors
    if (errors.length > 0) {
      console.log('\n  Top Errors:');
      errors.slice(0, 5).forEach((error, i) => {
        console.log(`    ${i + 1}. ${error.code}`);
        console.log(`       ${error.message.substring(0, 100)}...`);
      });
    }

    results.pages.push(pageResult);
    results.summary.totalPages++;
    results.summary.totalErrors += errors.length;
    results.summary.totalWarnings += warnings.length;
    results.summary.totalNotices += notices.length;

    if (pageResult.passed) {
      results.summary.passedPages++;
    } else {
      results.summary.failedPages++;
    }

    return pageResult;
  } catch (error) {
    console.error(`  Error testing ${page.name}:`, error.message);
    results.pages.push({
      name: page.name,
      url: fullUrl,
      error: error.message,
      passed: false,
    });
    results.summary.totalPages++;
    results.summary.failedPages++;
    return null;
  }
}

async function main() {
  console.log('='.repeat(60));
  console.log('PA11Y ACCESSIBILITY AUDIT - Atlas CRM');
  console.log('='.repeat(60));
  console.log(`Standard: WCAG 2.1 Level AA`);
  console.log(`Base URL: ${BASE_URL}`);
  console.log('');

  // Test all pages
  for (const page of PAGES) {
    await testPage(page);
  }

  // Generate summary
  console.log('\n' + '='.repeat(60));
  console.log('SUMMARY');
  console.log('='.repeat(60));
  console.log(`Total Pages: ${results.summary.totalPages}`);
  console.log(`Passed: \x1b[32m${results.summary.passedPages}\x1b[0m`);
  console.log(`Failed: \x1b[31m${results.summary.failedPages}\x1b[0m`);
  console.log(`Total Errors: ${results.summary.totalErrors}`);
  console.log(`Total Warnings: ${results.summary.totalWarnings}`);
  console.log(`Total Notices: ${results.summary.totalNotices}`);

  // Save report
  const reportPath = path.join(__dirname, 'reports', 'pa11y_report.json');
  fs.mkdirSync(path.dirname(reportPath), { recursive: true });
  fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));
  console.log(`\nReport saved to: ${reportPath}`);

  // Exit with error code if failures
  process.exit(results.summary.failedPages > 0 ? 1 : 0);
}

main().catch(console.error);
