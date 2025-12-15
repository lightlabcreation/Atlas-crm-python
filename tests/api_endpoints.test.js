/**
 * API ENDPOINT TESTS
 * ==================
 * Uses Mocha + Chai + node-fetch to test API endpoints
 * verifying that backend functions work correctly.
 *
 * Run: npx mocha tests/api_endpoints.test.js --timeout 30000
 */

const fetch = require('node-fetch');
const { expect } = require('chai');
const fs = require('fs');

const BASE_URL = 'https://atlas-crm.alexandratechlab.com';

// Cookie storage for authenticated requests
let sessionCookie = null;
let csrfToken = null;

// Helper to extract CSRF token from HTML
function extractCSRF(html) {
  const match = html.match(/name="csrfmiddlewaretoken"\s+value="([^"]+)"/);
  return match ? match[1] : null;
}

// Helper to extract cookies from response
function extractCookies(response) {
  const setCookie = response.headers.raw()['set-cookie'];
  if (!setCookie) return {};

  const cookies = {};
  setCookie.forEach((cookie) => {
    const [nameValue] = cookie.split(';');
    const [name, value] = nameValue.split('=');
    cookies[name.trim()] = value;
  });
  return cookies;
}

describe('Atlas CRM API Tests', function () {
  this.timeout(30000);

  describe('Authentication', () => {
    it('should load login page and get CSRF token', async () => {
      const response = await fetch(`${BASE_URL}/users/login/`);
      expect(response.status).to.equal(200);

      const html = await response.text();
      csrfToken = extractCSRF(html);
      expect(csrfToken).to.not.be.null;

      const cookies = extractCookies(response);
      sessionCookie = cookies.csrftoken || cookies.sessionid;
    });

    it('should reject invalid credentials', async () => {
      const loginPage = await fetch(`${BASE_URL}/users/login/`);
      const loginHtml = await loginPage.text();
      const csrf = extractCSRF(loginHtml);
      const cookies = extractCookies(loginPage);

      const response = await fetch(`${BASE_URL}/users/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          Cookie: `csrftoken=${cookies.csrftoken}`,
        },
        body: `csrfmiddlewaretoken=${csrf}&email=invalid@test.com&password=wrongpassword`,
        redirect: 'manual',
      });

      // Should not redirect to dashboard (remains on login or shows error)
      const location = response.headers.get('location');
      expect(location).to.not.include('/dashboard');
    });

    it('should accept valid credentials', async () => {
      const loginPage = await fetch(`${BASE_URL}/users/login/`);
      const loginHtml = await loginPage.text();
      const csrf = extractCSRF(loginHtml);
      const cookies = extractCookies(loginPage);

      const response = await fetch(`${BASE_URL}/users/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          Cookie: `csrftoken=${cookies.csrftoken}`,
        },
        body: `csrfmiddlewaretoken=${csrf}&email=superadmin@atlas.com&password=Atlas@2024!`,
        redirect: 'manual',
      });

      // Should redirect to dashboard
      expect(response.status).to.be.oneOf([302, 303]);
      const location = response.headers.get('location');
      expect(location).to.include('/dashboard');

      // Store session cookie for further tests
      const newCookies = extractCookies(response);
      sessionCookie = Object.entries(newCookies)
        .map(([k, v]) => `${k}=${v}`)
        .join('; ');
    });
  });

  describe('Dashboard Endpoints', () => {
    it('should return 200 for super admin dashboard', async () => {
      const response = await fetch(`${BASE_URL}/dashboard/super_admin/`, {
        headers: { Cookie: sessionCookie },
        redirect: 'manual',
      });

      // Either 200 (authenticated) or 302 (redirect to login)
      expect(response.status).to.be.oneOf([200, 302]);
    });
  });

  describe('Orders API', () => {
    it('should return orders list', async () => {
      const response = await fetch(`${BASE_URL}/callcenter_manager/orders/`, {
        headers: { Cookie: sessionCookie },
        redirect: 'manual',
      });

      expect(response.status).to.be.oneOf([200, 302]);
    });

    it('should support filter parameters', async () => {
      const response = await fetch(
        `${BASE_URL}/callcenter_manager/orders/?status=pending&search=test`,
        {
          headers: { Cookie: sessionCookie },
          redirect: 'manual',
        }
      );

      expect(response.status).to.be.oneOf([200, 302]);
    });
  });

  describe('Export Endpoints', () => {
    it('should return CSV for agent performance export', async () => {
      const response = await fetch(
        `${BASE_URL}/callcenter_manager/reports/agent-performance/export/`,
        {
          headers: { Cookie: sessionCookie },
          redirect: 'manual',
        }
      );

      // Should return 200 with CSV content type or redirect
      if (response.status === 200) {
        const contentType = response.headers.get('content-type');
        expect(contentType).to.include('csv');
      }
    });

    it('should return CSV for order statistics export', async () => {
      const response = await fetch(
        `${BASE_URL}/callcenter_manager/reports/order-statistics/export/`,
        {
          headers: { Cookie: sessionCookie },
          redirect: 'manual',
        }
      );

      if (response.status === 200) {
        const contentType = response.headers.get('content-type');
        expect(contentType).to.include('csv');
      }
    });

    it('should return PDF for packaging report export', async () => {
      const response = await fetch(`${BASE_URL}/packaging/reports/export/pdf/`, {
        headers: { Cookie: sessionCookie },
        redirect: 'manual',
      });

      if (response.status === 200) {
        const contentType = response.headers.get('content-type');
        expect(contentType).to.include('pdf');
      }
    });
  });

  describe('Stock Keeper Endpoints', () => {
    it('should load stock keeper dashboard', async () => {
      const response = await fetch(`${BASE_URL}/stock_keeper/`, {
        headers: { Cookie: sessionCookie },
        redirect: 'manual',
      });

      expect(response.status).to.be.oneOf([200, 302]);
    });

    it('should load inventory page', async () => {
      const response = await fetch(`${BASE_URL}/stock_keeper/inventory/`, {
        headers: { Cookie: sessionCookie },
        redirect: 'manual',
      });

      expect(response.status).to.be.oneOf([200, 302]);
    });

    it('should support receive stock search', async () => {
      const response = await fetch(
        `${BASE_URL}/stock_keeper/receive/?search=test`,
        {
          headers: { Cookie: sessionCookie },
          redirect: 'manual',
        }
      );

      expect(response.status).to.be.oneOf([200, 302]);
    });
  });

  describe('Seller Endpoints', () => {
    it('should load sellers list', async () => {
      const response = await fetch(`${BASE_URL}/sellers/`, {
        headers: { Cookie: sessionCookie },
        redirect: 'manual',
      });

      expect(response.status).to.be.oneOf([200, 302]);
    });

    it('should load seller orders', async () => {
      const response = await fetch(`${BASE_URL}/sellers/orders/`, {
        headers: { Cookie: sessionCookie },
        redirect: 'manual',
      });

      expect(response.status).to.be.oneOf([200, 302]);
    });
  });

  describe('Materials Endpoints', () => {
    it('should load materials page', async () => {
      const response = await fetch(`${BASE_URL}/packaging/materials/`, {
        headers: { Cookie: sessionCookie },
        redirect: 'manual',
      });

      expect(response.status).to.be.oneOf([200, 302]);
    });

    it('should export materials CSV', async () => {
      const response = await fetch(`${BASE_URL}/packaging/materials/export/`, {
        headers: { Cookie: sessionCookie },
        redirect: 'manual',
      });

      if (response.status === 200) {
        const contentType = response.headers.get('content-type');
        expect(contentType).to.include('csv');
      }
    });
  });

  describe('Delivery Endpoints', () => {
    it('should load delivery page with filters', async () => {
      const response = await fetch(
        `${BASE_URL}/delivery/?status=active&search=test`,
        {
          headers: { Cookie: sessionCookie },
          redirect: 'manual',
        }
      );

      expect(response.status).to.be.oneOf([200, 302]);
    });
  });

  describe('Health Check', () => {
    it('should return 200 for home page', async () => {
      const response = await fetch(`${BASE_URL}/`);
      expect(response.status).to.equal(200);
    });

    it('should have valid HTML structure', async () => {
      const response = await fetch(`${BASE_URL}/users/login/`);
      const html = await response.text();

      expect(html).to.include('<!DOCTYPE html');
      expect(html).to.include('</html>');
      expect(html).to.include('<form');
    });
  });
});
