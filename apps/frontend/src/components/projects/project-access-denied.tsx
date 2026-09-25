import { ArrowLeft, ShieldX } from 'lucide-react';
import { SmoothLink } from '@/components/navigation/smooth-link';

export function ProjectAccessDenied({
	projectId,
	feature,
}: {
	projectId: string;
	feature: string;
}) {
	return (
		<section className='project-access-denied' role='alert'>
			<span>
				<ShieldX size={24} />
			</span>
			<p className='eyebrow'>Access restricted</p>
			<h1>You don&apos;t have access to {feature}</h1>
			<p>
				Your project owner controls access to this area.
				Ask them to enable the feature for your account.
			</p>
			<SmoothLink href={`/projects/${projectId}`}>
				<ArrowLeft size={14} />
				Return to project
			</SmoothLink>
		</section>
	);
}
