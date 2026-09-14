import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
	typedRoutes: true,
	experimental: {
		// The application accepts 20 MiB files; multipart requests need some headroom.
		middlewareClientMaxBodySize: '22mb',
	},
};

export default nextConfig;
