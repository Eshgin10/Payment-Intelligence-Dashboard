'use client';
import Link from 'next/link';
import {useEffect,useRef,useState} from 'react';
import {Menu,X,ArrowUpRight} from 'lucide-react';

const pages=[['','Overview'],['payments','Payments'],['analytics','Analytics'],['data-quality','Data Quality'],['methodology','Methodology']];

export default function Header({section}:{section:string}){
 const dialog=useRef<HTMLDialogElement>(null);
 const [open,setOpen]=useState(false);
 useEffect(()=>{
  if(!open)return;
  const previous=document.body.style.overflow;
  document.body.style.overflow='hidden';
  dialog.current?.showModal();
  return()=>{dialog.current?.close();document.body.style.overflow=previous;};
 },[open]);
 const close=()=>setOpen(false);
 const logo=<><span className="site-logo-mark" aria-hidden="true"><img src="/payment-intelligence-mark.png" width="1280" height="1280" alt=""/></span><span className="site-logo-name">Payment<br/>Intelligence</span></>;
 return <>
  <header className="site-header">
   <Link href="/" className="site-logo" aria-label="Payment Intelligence home">{logo}</Link>
   <button className="menu-toggle" aria-label="Open navigation menu" aria-expanded={open} aria-controls="site-navigation" onClick={()=>setOpen(true)}><Menu size={32} strokeWidth={1.5}/></button>
  </header>
  <dialog ref={dialog} id="site-navigation" className="navigation-overlay" aria-label="Main navigation" onCancel={close}>
   <div className="navigation-header">
    <Link href="/" className="site-logo" aria-label="Payment Intelligence home" onClick={close}>{logo}</Link>
    <button className="menu-toggle" aria-label="Close navigation menu" onClick={close} autoFocus><X size={32} strokeWidth={1.5}/></button>
   </div>
   <nav className="fullscreen-links" aria-label="Main navigation">
    {pages.map(([path,label],index)=><Link key={path} href={`/${path}`} aria-current={section===path?'page':undefined} onClick={close}><span className="nav-number">0{index+1}</span><span>{label}</span><ArrowUpRight aria-hidden="true"/></Link>)}
   </nav>
  </dialog>
 </>;
}
