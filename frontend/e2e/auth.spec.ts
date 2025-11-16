import { test, expect } from '@playwright/test'

test.describe('Authentication Flow', () => {
  test('should display login page', async ({ page }) => {
    await page.goto('/login')

    await expect(page.locator('h2')).toContainText('Ticketing Pro')
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
  })

  test('should show validation errors on empty submit', async ({ page }) => {
    await page.goto('/login')

    await page.click('button[type="submit"]')

    await expect(page.locator('text=이메일을 입력해주세요')).toBeVisible()
    await expect(page.locator('text=비밀번호를 입력해주세요')).toBeVisible()
  })

  test('should navigate to register page', async ({ page }) => {
    await page.goto('/login')

    await page.click('text=회원가입')

    await expect(page).toHaveURL('/register')
    await expect(page.locator('h2')).toContainText('Ticketing Pro')
  })

  test('should display register form', async ({ page }) => {
    await page.goto('/register')

    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[name="name"]')).toBeVisible()
    await expect(page.locator('input[type="tel"]')).toBeVisible()
    await expect(page.locator('input[type="password"]').first()).toBeVisible()
  })

  test('should validate password strength on register', async ({ page }) => {
    await page.goto('/register')

    await page.fill('input[type="email"]', 'test@example.com')
    await page.fill('input[name="name"]', 'Test User')
    await page.fill('input[type="tel"]', '010-1234-5678')
    await page.locator('input[type="password"]').first().fill('weak')
    await page.click('button[type="submit"]')

    await expect(page.locator('text=비밀번호는 최소 8자 이상이어야 합니다')).toBeVisible()
  })
})
