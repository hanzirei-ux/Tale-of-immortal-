#!/usr/bin/env python3
"""Apply a narrowly-scoped read-only catalog export UI integration to GitHub v0.3.1 source.

Use on a fresh copy of development/liteapk-v0.3.1/source. Does not modify native code.
Refuses when expected anchors are missing or version is different. Creates .backup file.
"""
import pathlib
import sys

ADD_METHODS = r'''
    // Read-only export: uses the existing verified Unity-thread catalog request path.
    private void startReadOnlyCatalogExport(){
        if(catalogExport!=null){showResult("Export already in progress");return;}
        if(!ready){showResult("Load a player save and wait for the native catalog");return;}
        try{
            File dir=activity.getExternalFilesDir("toi_catalog_exports");
            if(dir==null)dir=new File(activity.getFilesDir(),"toi_catalog_exports");
            File destination=new File(dir,"toi_item_catalog_"+System.currentTimeMillis()+".jsonl");
            catalogExport=new ReadOnlyCatalogExport(destination,100000);
            sendReadOnlyCatalogPage(0);
        }catch(Exception ex){endReadOnlyCatalogExport("Export could not start: "+ex.getMessage(),false);}
    }
    private void sendReadOnlyCatalogPage(int offset){
        String reply=NativeBridge.request("catalog","@-1||"+offset,0,0,false);
        catalogExportRequestId=queuedId(reply);
        if(catalogExportRequestId==0){endReadOnlyCatalogExport("Catalog request rejected: "+reply,false);return;}
        poll();
    }
    private void receiveReadOnlyCatalogPage(String state,String message){
        if(catalogExport==null)return;
        if(!"CATALOG".equals(state)){endReadOnlyCatalogExport("Native catalog error: "+state+" "+message,false);return;}
        try{
            int next=catalogExport.acceptPage(message);
            if(next<0){endReadOnlyCatalogExport("Read-only item catalog exported: "+catalogExport.outputFile().getAbsolutePath()+" ("+catalogExport.rowsWritten()+" items)",true);return;}
            // Request only one page at a time. Never scan thousands of managed objects on Android UI thread.
            sendReadOnlyCatalogPage(next);
            if(catalogExport!=null)showResult("Exporting items: "+catalogExport.rowsWritten()+" / "+catalogExport.total());
        }catch(Exception ex){endReadOnlyCatalogExport("Catalog export aborted: "+ex.getMessage(),false);}
    }
    private void endReadOnlyCatalogExport(String message,boolean completed){
        catalogExportRequestId=0;
        if(catalogExport!=null){try{catalogExport.close();}catch(IOException ignored){} catalogExport=null;}
        if(!disposed)showResult(message);
        if(!completed)appendDiagnostic(message);
    }
'''


def insert_once(s, anchor, insertion, before=False):
    if anchor not in s or s.count(anchor)!=1:
        raise ValueError('Expected exactly one v0.3.1 source anchor: '+anchor[:130])
    return s.replace(anchor, insertion+anchor if before else anchor+insertion, 1)


def transform(src):
    if 'ReadOnlyCatalogExport catalogExport;' in src:
        raise ValueError('Exporter already integrated, refusing double insertion')
    if 'takeGameResults()' not in src or 'catalogRequestId' not in src:
        raise ValueError('This is not the supported GitHub v0.3.1 ModMenu.java')
    src=insert_once(src, '    private long catalogRequestId;', '\n    private ReadOnlyCatalogExport catalogExport;\n    private long catalogExportRequestId;')
    # Close output before releasing Unity/Native bridge.
    src=insert_once(src, 'private void release(){disposed=true;', 'if(catalogExport!=null){try{catalogExport.close();}catch(IOException ignored){} catalogExport=null;}catalogExportRequestId=0;',False)
    # The fields are not persisted to the game save; output is a standalone file.
    src=insert_once(src, '        itemTypeFilter.setOnItemSelectedListener(',
        '        button(row(page),"Export ALL item IDs (read-only)",new View.OnClickListener(){public void onClick(View v){startReadOnlyCatalogExport();}});\n',True)
    src=insert_once(src, '    private void submitCatalog(){', ADD_METHODS+'\n',True)
    # Responses are consumed once by this poller. Intercept export receipts first.
    src=insert_once(src, '                    if("catalog".equals(kind)){', '''                    if("catalog".equals(kind)&&catalogExport!=null&&id==catalogExportRequestId){
                        catalogExportRequestId=0;
                        receiveReadOnlyCatalogPage(state,message);
                        continue;
                    }
''',True)
    old='if(panel.getVisibility()==View.VISIBLE&&!activity.isFinishing())ui.postDelayed(pollTask,pendingCatalog||!pendingActions.isEmpty()?100:1000);'
    new='if((panel.getVisibility()==View.VISIBLE||catalogExportRequestId!=0)&&!activity.isFinishing())ui.postDelayed(pollTask,pendingCatalog||!pendingActions.isEmpty()||catalogExportRequestId!=0?100:1000);'
    src=insert_once(src,old,'',False).replace(old,new,1)
    return src

def main():
    if len(sys.argv)!=2:
        raise SystemExit('Usage: python tools/integrate_v031.py <repo-root>/android/bridge/src/main/java/org/npc/toibridge/ModMenu.java')
    source=pathlib.Path(sys.argv[1]); orig=source.read_text(encoding='utf-8')
    updated=transform(orig)
    backup=source.with_suffix(source.suffix+'.pre_readonly_export')
    if backup.exists():raise SystemExit('Backup already exists; refusing to overwrite')
    backup.write_text(orig,encoding='utf-8')
    source.write_text(updated,encoding='utf-8')
    print('Integrated export UI; original saved:',backup)

if __name__=='__main__':main()
