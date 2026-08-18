import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
	typedRoutes: true,
	serverExternalPackages: ['next-auth'],
};

export default nextConfig;
