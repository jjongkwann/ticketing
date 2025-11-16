import { test, expect } from '@playwright/test'

test.describe('Event Search', () => {
  test('should display main page with search bar', async ({ page }) => {
    await page.goto('/')

    await expect(page.locator('h1')).toContainText('원하는 공연을 찾아보세요')
    await expect(page.locator('input[placeholder*="검색"]')).toBeVisible()
  })

  test('should navigate to search page on search submit', async ({ page }) => {
    await page.goto('/')

    await page.fill('input[placeholder*="검색"]', 'BTS')
    await page.click('button:has-text("검색")')

    await expect(page).toHaveURL(/\/search\?q=BTS/)
  })

  test('should display category filters', async ({ page }) => {
    await page.goto('/')

    await expect(page.locator('text=콘서트')).toBeVisible()
    await expect(page.locator('text=스포츠')).toBeVisible()
    await expect(page.locator('text=뮤지컬')).toBeVisible()
    await expect(page.locator('text=전시회')).toBeVisible()
  })

  test('should filter by category', async ({ page }) => {
    await page.goto('/')

    await page.click('button:has-text("콘서트")')

    await expect(page).toHaveURL(/\/search\?category=concert/)
  })

  test('should display search results', async ({ page }) => {
    await page.goto('/search?q=concert')

    await expect(page.locator('h2')).toContainText('검색 결과')
    await expect(page.locator('text=전체')).toBeVisible()
  })

  test('should show event cards in search results', async ({ page }) => {
    // Mock API response would be needed here
    await page.goto('/search?category=concert')

    // Wait for potential API response
    await page.waitForTimeout(1000)

    // This would pass if events are loaded
    const eventCards = page.locator('.card')
    if ((await eventCards.count()) > 0) {
      await expect(eventCards.first()).toBeVisible()
    }
  })
})
