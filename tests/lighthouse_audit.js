/**
 * LIGHTHOUSE PERFORMANCE & ACCESSIBILITY AUDIT
 * =============================================
 * Uses Google Lighthouse to audit:
 * - Performance
 * - Accessibility
 * - Best Practices
 * - SEO
 *
 * Run: node tests/lighthouse_audit.js
 */

const lighthouse = require('lighthouse');
const chromeLauncher = require('chrome-launcher');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://atlas-crm.alexandratechlab.com';

// Pages to audit
const PAGES_TO_AUDIT = [
  { name: 'Login Page', url: '/users/login/', auth: false },
  { name: 'Landing Page', url: '/', auth: false },
];

// Authenticated pages require login cookie
const AUTHENTICATED_PAGES = [
  { name: 'Dashboard', url: '/dashboard/super_admin/', role: 'superadmin' },
  { name: 'Orders Management', url: '/callcenter_manager/orders/', role: 'callcenter_manager' },
  { name: 'Stock Keeper Dashboard', url: '/stock_keeper/', role: 'stock_keeper' },
  { name: 'Seller Orders', url: '/sellers/orders/', role: 'seller' },
];

// Lighthouse configuration
const lighthouseConfig = {
  extends: 'lighthouse:default',
  settings: {
    onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
    formFactor: 'desktop',
    screenEmulation: {
      mobile: false,
      width: 1350,
      height: 940,
      deviceScaleFactor: 1,
      disabled: false,
    },
    throttling: {
      rttMs: 40,
      throughputKbps: 10240,
      cpuSlowdownMultiplier: 1,
    },
  },
};

// Results storage
const results = {
  timestamp: new Date().toISOString(),
  pages: [],
  summary: {
    totalPages: 0,
    passed: 0,
    failed: 0,
    warnings: 0,
  },
};

// Threshold scores
const THRESHOLDS = {
  performance: 50,
  accessibility: 70,
  'best-practices': 70,
  seo: 70,
};

async function runLighthouse(url, chrome) {
  const options = {
    logLevel: 'error',
    output: 'json',
    port: chrome.port,
  };

  const runnerResult = await lighthouse(url, options, lighthouseConfig);
  return runnerResult;
}

async function auditPage(page, chrome) {
  const fullUrl = `${BASE_URL}${page.url}`;
  console.log(`\nAuditing: ${page.name} (${fullUrl})`);

  try {
    const result = await runLighthouse(fullUrl, chrome);
    const categories = result.lhr.categories;

    const scores = {
      performance: Math.round(categories.performance.score * 100),
      accessibility: Math.round(categories.accessibility.score * 100),
      'best-practices': Math.round(categories['best-practices'].score * 100),
      seo: Math.round(categories.seo.score * 100),
    };

    // Check against thresholds
    const passed = Object.keys(THRESHOLDS).every(
      (key) => scores[key] >= THRESHOLDS[key]
    );

    const pageResult = {
      name: page.name,
      url: fullUrl,
      scores,
      passed,
      issues: [],
    };

    // Collect accessibility issues
    const accessibilityAudits = result.lhr.audits;
    const failedAudits = Object.values(accessibilityAudits).filter(
      (audit) => audit.score !== null && audit.score < 1 && audit.details?.items?.length > 0
    );

    pageResult.issues = failedAudits.slice(0, 10).map((audit) => ({
      id: audit.id,
      title: audit.title,
      description: audit.description,
      score: audit.score,
    }));

    // Print results
    console.log('  Performance:', scores.performance >= THRESHOLDS.performance ? '\x1b[32m' : '\x1b[31m', scores.performance, '\x1b[0m');
    console.log('  Accessibility:', scores.accessibility >= THRESHOLDS.accessibility ? '\x1b[32m' : '\x1b[31m', scores.accessibility, '\x1b[0m');
    console.log('  Best Practices:', scores['best-practices'] >= THRESHOLDS['best-practices'] ? '\x1b[32m' : '\x1b[31m', scores['best-practices'], '\x1b[0m');
    console.log('  SEO:', scores.seo >= THRESHOLDS.seo ? '\x1b[32m' : '\x1b[31m', scores.seo, '\x1b[0m');
    console.log('  Status:', passed ? '\x1b[32mPASSED\x1b[0m' : '\x1b[31mFAILED\x1b[0m');

    results.pages.push(pageResult);
    results.summary.totalPages++;
    if (passed) {
      results.summary.passed++;
    } else {
      results.summary.failed++;
    }

    return pageResult;
  } catch (error) {
    console.error(`  Error auditing ${page.name}:`, error.message);
    results.pages.push({
      name: page.name,
      url: fullUrl,
      error: error.message,
      passed: false,
    });
    results.summary.totalPages++;
    results.summary.failed++;
    return null;
  }
}

async function main() {
  console.log('='.repeat(60));
  console.log('LIGHTHOUSE AUDIT - Atlas CRM');
  console.log('='.repeat(60));
  console.log(`Base URL: ${BASE_URL}`);
  console.log(`Thresholds: Performance=${THRESHOLDS.performance}, Accessibility=${THRESHOLDS.accessibility}`);
  console.log('');

  // Launch Chrome
  const chrome = await chromeLauncher.launch({
    chromeFlags: ['--headless', '--disable-gpu', '--no-sandbox'],
  });

  console.log(`Chrome launched on port ${chrome.port}`);

  try {
    // Audit public pages
    console.log('\n--- PUBLIC PAGES ---');
    for (const page of PAGES_TO_AUDIT) {
      await auditPage(page, chrome);
    }

    // Note: Authenticated pages would require cookie injection
    console.log('\n--- AUTHENTICATED PAGES (skipped - requires login) ---');
    console.log('Note: Run Playwright tests for authenticated page audits');

  } finally {
    await chrome.kill();
  }

  // Generate report
  console.log('\n' + '='.repeat(60));
  console.log('SUMMARY');
  console.log('='.repeat(60));
  console.log(`Total Pages Audited: ${results.summary.totalPages}`);
  console.log(`Passed: \x1b[32m${results.summary.passed}\x1b[0m`);
  console.log(`Failed: \x1b[31m${results.summary.failed}\x1b[0m`);

  // Save JSON report
  const reportPath = path.join(__dirname, 'reports', 'lighthouse_report.json');
  fs.mkdirSync(path.dirname(reportPath), { recursive: true });
  fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));
  console.log(`\nReport saved to: ${reportPath}`);

  // Exit with error if any failures
  process.exit(results.summary.failed > 0 ? 1 : 0);
}

main().catch(console.error);
