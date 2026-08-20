import { z } from 'zod';

const clientSchema = z.object({});

const serverSchema = clientSchema.extend({
	BACKEND_API_URL: z.string().url().default('http://localhost:8000'),
});

export const clientEnv = clientSchema.parse({});

export const serverEnv = serverSchema.parse({
	BACKEND_API_URL: process.env.BACKEND_API_URL,
});
