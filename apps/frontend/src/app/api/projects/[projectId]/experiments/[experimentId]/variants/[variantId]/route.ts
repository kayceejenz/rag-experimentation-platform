import {NextResponse} from 'next/server';
import {getAuthUser} from '@/lib/api/auth';
import {backendFetch} from '@/lib/api/backend';
import {apiError,proxyResponse} from '@/lib/api/proxy-response';

type P={params:Promise<{projectId:string;experimentId:string;variantId:string}>};

export async function DELETE(_:Request,{params}:P){
  const user=await getAuthUser();
  if(!user)return NextResponse.json({error:'Unauthorized'},{status:401});
  try{
    const {projectId,experimentId,variantId}=await params;
    return proxyResponse(await backendFetch(user.accessToken,`/projects/${projectId}/experiments/${experimentId}/variants/${variantId}`,{method:'DELETE'}));
  }catch(error){return apiError(error)}
}
