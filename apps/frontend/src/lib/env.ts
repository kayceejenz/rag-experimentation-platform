import { z } from 'zod';

const clientSchema = z.object({});

const serverSchema = clientSchema.extend({
	BACKEND_API_URL: z.string().url().default('http://localhost:8000'),
	NEXTAUTH_SECRET: z
		.string()
		.default(
			'ioaneuing9a8neignaeoiniqaneoeifnqoiaweniurqnwenrqowenoiweno',
		),
	NEXTAUTH_URL: z.string().url().optional(),
});

export const clientEnv = clientSchema.parse({});

export const serverEnv = serverSchema.parse({
	BACKEND_API_URL: process.env.BACKEND_API_URL,
	NEXTAUTH_SECRET: process.env.NEXTAUTH_SECRET,
	NEXTAUTH_URL: process.env.NEXTAUTH_URL,
});
