import Dashboard from '@/components/dashboard';
import {notFound} from 'next/navigation';
export function generateStaticParams(){return ['payments','analytics','data-quality','methodology'].map(section=>({section}));}
export default async function Page({params}:{params:Promise<{section:string}>}){const {section}=await params;if(!['payments','analytics','data-quality','methodology'].includes(section))notFound();return <Dashboard key={section} section={section}/>}
