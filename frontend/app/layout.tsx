import type { Metadata } from 'next';
import './globals.css';
import './readability.css';
import './navigation.css';
export const metadata: Metadata = {title:'Payment Intelligence | Operations analytics',description:'Payment performance, failures and recovery. A real analytics platform with a transparent synthetic dataset.',icons:{icon:'/favicon.svg'}};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
