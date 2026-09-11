'use client';
import {useEffect,useRef} from 'react';
import type {Filters} from './types';
type Registry={registerTool:(tool:{name:string;description:string;inputSchema:object;annotations:{readOnlyHint:boolean;untrustedContentHint:boolean};execute:(input:unknown)=>unknown},options:{signal:AbortSignal})=>void|Promise<void>};

export function usePaymentViewTool(view:unknown,filters:Filters,section:string,loading:boolean){
 const current=useRef({view,filters,section,loading});
 current.current={view,filters,section,loading};
 useEffect(()=>{
  const registry=(document as Document&{modelContext?:Registry}).modelContext;
  if(!registry?.registerTool)return;
  const lifecycle=new AbortController();
  try{Promise.resolve(registry.registerTool({name:'read_payment_view',description:'Read the currently loaded payment analytics view and its applied filters. Does not modify records, filters, or navigation.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true,untrustedContentHint:false},execute(input){if(!input||typeof input!=='object'||Array.isArray(input)||Object.keys(input).length)throw new Error('Expected an empty object.');if(current.current.loading)throw new Error('The view is still loading.');return current.current;}},{signal:lifecycle.signal})).catch(()=>{});}catch{/* Optional browser capability; the visible app remains fully functional. */}
  return()=>lifecycle.abort();
 },[]);
}
