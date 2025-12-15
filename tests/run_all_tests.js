#!/usr/bin/env node
/**
 * COMPREHENSIVE TEST RUNNER
 * =========================
 * Runs all tests using multiple open source tools:
 * 1. Playwright - E2E functional tests
 * 2. axe-core - Accessibility testing (via Playwright)
 * 3. Lighthouse - Performance & SEO audits
 * 4. Pa11y - WCAG accessibility compliance
 * 5. Mocha/Chai - API endpoint tests
 *
 * Run: node tests/run_all_tests.js
 */

const { spawn, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const RESULTS_DIR = path.join(__dirname, 'reports');

// Ensure reports directory exists
if (!fs.existsSync(RESULTS_DIR)) {
  fs.mkdirSync(RESULTS_DIR, { recursive: true });
}

// Results storage
const masterReport = {
  timestamp: new Date().toISOString(),
  duration: 0,
  tools: [],
  summary: {
    totalTests: 0,
    passed: 0,
    failed: 0,
    skipped: 0,
  },
  allPassed: false,
};

// Helper to run a command and capture output
function runCommand(name, command, args = []) {
  return new Promise((resolve) => {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`Running: ${name}`);
    console.log(`Command: ${command} ${args.join(' ')}`);
    console.log('='.repeat(60));

    const startTime = Date.now();
    const proc = spawn(command, args, {
      stdio: 'pipe',
      shell: true,
      cwd: path.join(__dirname, '..'),
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data) => {
      const text = data.toString();
      stdout += text;
      process.stdout.write(text);
    });

    proc.stderr.on('data', (data) => {
      const text = data.toString();
      stderr += text;
      process.stderr.write(text);
    });

    proc.on('close', (code) => {
      const duration = Date.now() - startTime;
      resolve({
        name,
        command: `${command} ${args.join(' ')}`,
        exitCode: code,
        duration,
        stdout,
        stderr,
        passed: code === 0,
      });
    });

    proc.on('error', (error) => {
      resolve({
        name,
        command: `${command} ${args.join(' ')}`,
        exitCode: 1,
        duration: Date.now() - startTime,
        error: error.message,
        passed: false,
      });
    });
  });
}

// Generate HTML report
function generateHTMLReport() {
  const html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Atlas CRM - Comprehensive Test Report</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }
    .container { max-width: 1200px; margin: 0 auto; }
    h1 { color: #333; margin-bottom: 10px; }
    .timestamp { color: #666; margin-bottom: 20px; }
    .summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 30px; }
    .summary-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
    .summary-card h3 { font-size: 32px; margin-bottom: 5px; }
    .summary-card p { color: #666; }
    .passed { color: #22c55e; }
    .failed { color: #ef4444; }
    .tool-section { background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }
    .tool-header { padding: 15px 20px; background: #f8f9fa; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
    .tool-name { font-weight: 600; font-size: 18px; }
    .status-badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; }
    .status-passed { background: #dcfce7; color: #166534; }
    .status-failed { background: #fee2e2; color: #991b1b; }
    .tool-details { padding: 15px 20px; }
    .detail-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
    .detail-row:last-child { border-bottom: none; }
    .output-section { margin-top: 15px; }
    .output-section h4 { margin-bottom: 10px; color: #666; }
    pre { background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 12px; max-height: 300px; overflow-y: auto; }
    .tools-used { background: white; border-radius: 8px; padding: 20px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .tools-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin-top: 15px; }
    .tool-badge { background: #f0f9ff; border: 1px solid #bae6fd; padding: 10px; border-radius: 6px; text-align: center; }
    .tool-badge strong { display: block; color: #0369a1; margin-bottom: 3px; }
    .tool-badge span { font-size: 12px; color: #666; }
    .overall-status { text-align: center; padding: 30px; background: white; border-radius: 8px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .overall-status h2 { font-size: 48px; margin-bottom: 10px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Atlas CRM - Comprehensive Test Report</h1>
    <p class="timestamp">Generated: ${masterReport.timestamp}</p>
    <p class="timestamp">Total Duration: ${(masterReport.duration / 1000).toFixed(2)}s</p>

    <div class="overall-status">
      <h2 class="${masterReport.allPassed ? 'passed' : 'failed'}">
        ${masterReport.allPassed ? 'ALL TESTS PASSED' : 'SOME TESTS FAILED'}
      </h2>
      <p>${masterReport.summary.passed} of ${masterReport.summary.totalTests} test suites passed</p>
    </div>

    <div class="tools-used">
      <h3>Open Source Tools Used</h3>
      <div class="tools-grid">
        <div class="tool-badge">
          <strong>Playwright</strong>
          <span>E2E Testing</span>
        </div>
        <div class="tool-badge">
          <strong>axe-core</strong>
          <span>Accessibility</span>
        </div>
        <div class="tool-badge">
          <strong>Lighthouse</strong>
          <span>Performance</span>
        </div>
        <div class="tool-badge">
          <strong>Pa11y</strong>
          <span>WCAG Audit</span>
        </div>
        <div class="tool-badge">
          <strong>Mocha/Chai</strong>
          <span>API Testing</span>
        </div>
      </div>
    </div>

    <div class="summary">
      <div class="summary-card">
        <h3>${masterReport.summary.totalTests}</h3>
        <p>Total Test Suites</p>
      </div>
      <div class="summary-card">
        <h3 class="passed">${masterReport.summary.passed}</h3>
        <p>Passed</p>
      </div>
      <div class="summary-card">
        <h3 class="failed">${masterReport.summary.failed}</h3>
        <p>Failed</p>
      </div>
      <div class="summary-card">
        <h3>${(masterReport.duration / 1000).toFixed(1)}s</h3>
        <p>Duration</p>
      </div>
    </div>

    ${masterReport.tools
      .map(
        (tool) => `
    <div class="tool-section">
      <div class="tool-header">
        <span class="tool-name">${tool.name}</span>
        <span class="status-badge ${tool.passed ? 'status-passed' : 'status-failed'}">
          ${tool.passed ? 'PASSED' : 'FAILED'}
        </span>
      </div>
      <div class="tool-details">
        <div class="detail-row">
          <span>Command</span>
          <code>${tool.command}</code>
        </div>
        <div class="detail-row">
          <span>Exit Code</span>
          <span>${tool.exitCode}</span>
        </div>
        <div class="detail-row">
          <span>Duration</span>
          <span>${(tool.duration / 1000).toFixed(2)}s</span>
        </div>
        ${
          tool.stdout
            ? `
        <div class="output-section">
          <h4>Output</h4>
          <pre>${escapeHtml(tool.stdout.slice(-5000))}</pre>
        </div>
        `
            : ''
        }
        ${
          tool.stderr && tool.stderr.trim()
            ? `
        <div class="output-section">
          <h4>Errors</h4>
          <pre>${escapeHtml(tool.stderr.slice(-2000))}</pre>
        </div>
        `
            : ''
        }
      </div>
    </div>
    `
      )
      .join('')}

    <footer style="text-align: center; padding: 20px; color: #666;">
      <p>Atlas CRM Test Suite - Generated by Comprehensive Test Runner</p>
      <p>Tools: Playwright, axe-core, Lighthouse, Pa11y, Mocha, Chai</p>
    </footer>
  </div>
</body>
</html>
  `;

  return html;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

async function main() {
  console.log('\n');
  console.log('*'.repeat(60));
  console.log('*  ATLAS CRM - COMPREHENSIVE TEST SUITE                    *');
  console.log('*  Using Multiple Open Source Testing Tools                *');
  console.log('*'.repeat(60));
  console.log('\nTools being used:');
  console.log('  1. Playwright - End-to-End functional testing');
  console.log('  2. axe-core - Accessibility testing (via Playwright)');
  console.log('  3. Lighthouse - Performance, SEO, Best Practices audits');
  console.log('  4. Pa11y - WCAG 2.1 AA accessibility compliance');
  console.log('  5. Mocha/Chai - API endpoint testing');
  console.log('');

  const startTime = Date.now();

  // Run all test suites
  const results = [];

  // 1. Playwright E2E Tests (includes axe-core)
  results.push(
    await runCommand(
      'Playwright E2E + axe-core Accessibility',
      'npx',
      ['playwright', 'test', 'tests/comprehensive_functionality.spec.js', '--reporter=list']
    )
  );

  // 2. Mocha API Tests
  results.push(
    await runCommand(
      'Mocha/Chai API Endpoint Tests',
      'npx',
      ['mocha', 'tests/api_endpoints.test.js', '--timeout', '30000']
    )
  );

  // 3. Lighthouse Audit
  results.push(
    await runCommand('Lighthouse Performance Audit', 'node', [
      'tests/lighthouse_audit.js',
    ])
  );

  // 4. Pa11y Accessibility
  results.push(
    await runCommand('Pa11y WCAG Accessibility Audit', 'node', [
      'tests/pa11y_accessibility.js',
    ])
  );

  // Calculate totals
  masterReport.duration = Date.now() - startTime;
  masterReport.tools = results;
  masterReport.summary.totalTests = results.length;
  masterReport.summary.passed = results.filter((r) => r.passed).length;
  masterReport.summary.failed = results.filter((r) => !r.passed).length;
  masterReport.allPassed = masterReport.summary.failed === 0;

  // Generate HTML report
  const htmlReport = generateHTMLReport();
  const reportPath = path.join(RESULTS_DIR, 'comprehensive_report.html');
  fs.writeFileSync(reportPath, htmlReport);

  // Save JSON report
  const jsonPath = path.join(RESULTS_DIR, 'comprehensive_report.json');
  fs.writeFileSync(jsonPath, JSON.stringify(masterReport, null, 2));

  // Print summary
  console.log('\n');
  console.log('*'.repeat(60));
  console.log('*  TEST SUMMARY                                            *');
  console.log('*'.repeat(60));
  console.log(`\nTotal Duration: ${(masterReport.duration / 1000).toFixed(2)}s`);
  console.log(`Test Suites: ${masterReport.summary.totalTests}`);
  console.log(`Passed: \x1b[32m${masterReport.summary.passed}\x1b[0m`);
  console.log(`Failed: \x1b[31m${masterReport.summary.failed}\x1b[0m`);
  console.log('');
  console.log('Results by tool:');
  results.forEach((r) => {
    const status = r.passed ? '\x1b[32mPASSED\x1b[0m' : '\x1b[31mFAILED\x1b[0m';
    console.log(`  ${r.name}: ${status}`);
  });
  console.log('');
  console.log(`HTML Report: ${reportPath}`);
  console.log(`JSON Report: ${jsonPath}`);
  console.log('');

  if (masterReport.allPassed) {
    console.log('\x1b[32m*** ALL TESTS PASSED ***\x1b[0m');
  } else {
    console.log('\x1b[31m*** SOME TESTS FAILED - CHECK REPORTS ***\x1b[0m');
  }

  process.exit(masterReport.allPassed ? 0 : 1);
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
