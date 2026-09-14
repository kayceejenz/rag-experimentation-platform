import { expect, test } from '@playwright/test';

test('a protected route leads to an accessible invitation-only sign-in page', async ({
	page,
}) => {
	const pageErrors: string[] = [];
	page.on('pageerror', error => pageErrors.push(error.message));

	await page.goto('/projects/example');

	await expect(page).toHaveURL(/\/auth\/signin\?.*callbackUrl=/);
	await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
	await expect(page.getByLabel('Email')).toBeVisible();
	await expect(page.getByLabel('Password')).toBeVisible();

	await page.getByRole('tab', { name: 'Create account' }).click();
	await expect(page.getByRole('heading', { name: 'Create your account' })).toBeVisible();
	await expect(page.getByLabel('Invitation code')).toBeVisible();
	await expect(page.getByText('Registration is available by invitation.')).toBeVisible();
	expect(pageErrors).toEqual([]);
});
