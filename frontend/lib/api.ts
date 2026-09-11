'use client';
import {useEffect,useState} from 'react';
export function useApi<T>(path:string|null){
 const [data,setData]=useState<T|null>(null),[error,setError]=useState(''),[loading,setLoading]=useState(true),[retry,setRetry]=useState(0),[loadedPath,setLoadedPath]=useState<string|null>(null);
 useEffect(()=>{if(!path){setLoading(false);return;}const abort=new AbortController();setLoading(true);setError('');setData(null);
 fetch(path,{signal:abort.signal}).then(async response=>{if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(typeof body.detail==='string'?body.detail:response.status===422?'Check the date range and filters.':'We couldn’t load this view. Please try again.');}return response.json()}).then(setData).catch(e=>{if(e.name!=='AbortError')setError(e.message)}).finally(()=>{if(!abort.signal.aborted){setLoading(false);setLoadedPath(path)}});
 return()=>abort.abort();},[path,retry]);
 return {data,error,loading:loading||(path!==null&&path!==loadedPath),reload:()=>setRetry(x=>x+1)};
}
export const money=(n:number,compact=true)=>new Intl.NumberFormat('en-IE',{style:'currency',currency:'EUR',notation:compact?'compact':'standard',maximumFractionDigits:compact?2:2}).format(n);
export const number=(n:number)=>new Intl.NumberFormat('en-GB').format(n);
export const percent=(n:number|null)=>n===null?'—':`${Number(n).toFixed(1)}%`;
export const dateLabel=(value:string)=>new Intl.DateTimeFormat('en-GB',{day:'numeric',month:'short',timeZone:'UTC'}).format(new Date(value));
