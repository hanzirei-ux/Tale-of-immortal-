"""Targeted continuation of the existing v0.3 Android UI; no replacement Activity."""
def update(s):
    s=s.replace('import java.util.Locale;','import java.util.LinkedHashMap;\nimport org.json.JSONArray;\nimport org.json.JSONObject;')
    s=s.replace('    private String lastReceipt="", selectedItemName="";','''    private String selectedItemName="", selectedItemId="", catalogRequestKey="", lastDiagnostic="No operation logged yet";
    private long catalogRequestId;
    private final LinkedHashMap<Long,String> pendingActions=new LinkedHashMap<Long,String>();
    private Spinner currencyType;
    private TextView currencyCurrent;
    private static final String[] CURRENCY_KEYS={"money","contribution","city_token","immortal_token","sect_funds","sect_reputation","sect_faith"};
    private static final String[] CURRENCY_LABELS={"Spirit Stones / player money","Personal Sect Contribution","City Token","Immortal Store Token","Sect Funds (treasury)","Sect Reputation","Sect Faith Currency"};''')
    s=s.replace('"Skills / Artifacts","Diagnostics"','"Skills / Artifacts","Currency & Contribution","Diagnostics"')
    s=s.replace('        itemList=null;itemInfo=null;itemSelected=null;itemSearch=null;itemTypeFilter=null;itemIdField=null;','''        itemList=null;itemInfo=null;itemSelected=null;itemSearch=null;itemTypeFilter=null;itemIdField=null;
        currencyType=null;currencyCurrent=null;selectedItemName="";selectedItemId="";''')
    s=s.replace('Base-stat edits; save persistence requires testing. Current/max HP and battle modifiers are separate. Inventory capacity cannot be reduced in this build.','Base-stat edits are permanent. Current/max HP and battle modifiers are separate. Back up your save first.')
    a=s.index('            text(page,"INVENTORY CAPACITY');b=s.index('        }else if(selected==3)',a)
    s=s[:a]+'''            text(page,"INVENTORY CAPACITY — Effective slots, including ring/plugin bonuses. SET/ADD/SUBTRACT protects occupied slots. Limit: 2,000.",13);
            final Spinner slotMode=spinner(page,new String[]{"SET","ADD","SUBTRACT"});slotMode.setSelection(1);
            final EditText slots=number(page,"50");slots.setHint("Slot amount (whole number)");
            LinearLayout slotButtons=row(page);
            button(slotButtons,"READ capacity",new View.OnClickListener(){public void onClick(View v){request("capacity","slots",-1,0,false);}});
            button(slotButtons,"APPLY",new View.OnClickListener(){public void onClick(View v){
                try{int amount=Integer.parseInt(slots.getText().toString().trim());if(amount<0||amount>2000)throw new NumberFormatException();
                    request("capacity","slots",slotMode.getSelectedItemPosition(),amount,true);
                }catch(NumberFormatException ex){result.setText("Enter a whole number 0..2000");}
            }});
            text(page,"The saved bonus belongs to this player. Reset only disables runtime cheats. Save/load persistence needs testing; do not remove this library while using expanded storage.",12);
'''+s[b:]
    s=s.replace('        }else{\n            text(page,"Exact LiteAPK','        }else if(selected==5){\n            buildCurrencyEditor();\n        }else{\n            text(page,"Exact LiteAPK')
    s=s.replace('            button(row(page),"Retry initialization"','''            TextView details=text(page,lastDiagnostic,12);details.setTextIsSelectable(true);
            button(row(page),"Copy last operation / error",new View.OnClickListener(){public void onClick(View v){android.content.ClipboardManager c=(android.content.ClipboardManager)activity.getSystemService(android.content.Context.CLIPBOARD_SERVICE);if(c!=null)c.setPrimaryClip(android.content.ClipData.newPlainText("TOI diagnostics",lastDiagnostic));}});
            button(row(page),"Retry initialization"''')
    s=s.replace('itemIdField.setHint("Selected item ID (editable)");','itemIdField.setHint("Tap an item to select its ID");itemIdField.setKeyListener(null);itemIdField.setFocusable(false);')
    a=s.index('                request("item",itemIdField.getText()');b=s.index('\n            }catch(NumberFormatException',a)
    s=s[:a]+'''                final String id=selectedItemId,name=selectedItemName;final int quantity=n;
                if(id.isEmpty()){result.setText("Tap a catalog item before adding it");return;}
                confirm("Add selected item",name+" (#"+id+")\\nQuantity: "+quantity,new Runnable(){public void run(){request("item",id,0,quantity,true);}});'''+s[b:]
    s=s.replace('        String reply=NativeBridge.request("catalog",key,0,0,false);\n        pendingCatalog=reply.startsWith("QUEUED");','''        String reply=NativeBridge.request("catalog",key,0,0,false);
        catalogRequestId=queuedId(reply);catalogRequestKey=key;pendingCatalog=catalogRequestId!=0;''')
    s=s.replace('                selectedItemName=name;','                selectedItemName=name;selectedItemId=id;')
    s=s.replace('        final SeekBar slider=new SeekBar(activity);slider.setMax(1000);','        final SeekBar slider=new SeekBar(activity);slider.setProgressTintList(ColorStateList.valueOf(Color.rgb(81,183,225)));slider.setThumbTintList(ColorStateList.valueOf(FG));slider.setMax(1000);')
    s=s.replace('        if("catalog".equals(kind))pendingCatalog=reply.startsWith("QUEUED");','        long id=queuedId(reply);if(id!=0)pendingActions.put(Long.valueOf(id),kind+" ["+key+"]");')
    s=s.replace('                File lib=new File(','                if(NativeBridge.bridgeVersion()!=3)throw new IOException("DEX/native API mismatch: install both v0.3 files together");\n                File lib=new File(')
    a=s.index('            String receipt=NativeBridge.result();');b=s.index('\n        }\n        if(panel.getVisibility()',a)
    s=s[:a]+'''            try{
                JSONArray replies=new JSONArray(NativeBridge.takeGameResults());
                for(int i=0;i<replies.length();i++){
                    JSONObject r=replies.getJSONObject(i);long id=r.getLong("id");
                    String kind=r.getString("kind"),key=r.getString("key"),state=r.getString("state"),message=r.getString("message");
                    if("catalog".equals(kind)){
                        if(id!=catalogRequestId)continue;pendingCatalog=false;
                        if(!catalogRefreshNeeded&&key.equals(catalogRequestKey)){
                            if("CATALOG".equals(state))renderCatalog(message);else if(itemInfo!=null)itemInfo.setText(state+": "+message);
                        }
                        if(catalogRefreshNeeded){catalogRefreshNeeded=false;submitCatalog();}
                    }else{
                        pendingActions.remove(Long.valueOf(id));result.setText(kind+" — "+state+"\\n"+message);
                        result.setTextColor("FAILED".equals(state)||"BLOCKED".equals(state)||"REJECTED".equals(state)?Color.rgb(255,174,164):MUTED);
                        if("currency".equals(kind)&&currencyCurrent!=null&&currencyType!=null&&key.equals(CURRENCY_KEYS[currencyType.getSelectedItemPosition()]))currencyCurrent.setText(state+"\\n"+message);
                        appendDiagnostic(kind+" ["+key+"] "+state+"\\n"+message);
                    }
                }
            }catch(Exception ex){result.setText("Receipt decode error: "+ex.getClass().getSimpleName()+": "+ex.getMessage());}
'''+s[b:]
    s=s.replace('ui.postDelayed(pollTask,1000);','ui.postDelayed(pollTask,pendingCatalog||!pendingActions.isEmpty()?100:1000);')
    s=s.replace('result.setMaxLines(4);result.setTextIsSelectable(true);','result.setMaxLines(4);result.setMovementMethod(new android.text.method.ScrollingMovementMethod());result.setTextIsSelectable(true);')
    i=s.index('    /** Actual item configuration')
    helpers='''    private long queuedId(String reply){if(reply==null||!reply.startsWith("QUEUED:"))return 0;try{return Long.parseLong(reply.substring(7));}catch(NumberFormatException e){return 0;}}
    private void confirm(String title,String message,final Runnable action){
        TextView heading=new TextView(activity);heading.setText(title);heading.setTextColor(FG);heading.setTextSize(18);heading.setPadding(dp(20),dp(16),dp(20),dp(4));heading.setBackgroundColor(BG);
        TextView body=new TextView(activity);body.setText(message);body.setTextColor(FG);body.setTextSize(16);body.setPadding(dp(20),dp(12),dp(20),dp(16));body.setBackgroundColor(BG);
        final AlertDialog dialog=new AlertDialog.Builder(activity,android.R.style.Theme_Material_Dialog_Alert).setCustomTitle(heading).setView(body)
            .setNegativeButton("Cancel",null).setPositiveButton("Confirm",new android.content.DialogInterface.OnClickListener(){public void onClick(android.content.DialogInterface d,int which){action.run();}}).create();
        dialog.setOnShowListener(new android.content.DialogInterface.OnShowListener(){public void onShow(android.content.DialogInterface d){dialog.getWindow().setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(BG));dialog.getButton(AlertDialog.BUTTON_POSITIVE).setTextColor(FG);dialog.getButton(AlertDialog.BUTTON_NEGATIVE).setTextColor(MUTED);}});dialog.show();
    }
    private void buildCurrencyEditor(){
        text(page,"Personal balances and sect treasury are separate. READ shows the actual player/sect target. Changes use native game transactions.",13);
        currencyType=spinner(page,CURRENCY_LABELS);currencyCurrent=text(page,"Select a resource, then READ.",14);currencyCurrent.setTextIsSelectable(true);
        final Spinner mode=spinner(page,new String[]{"SET","ADD","SUBTRACT"});mode.setSelection(1);
        final EditText amount=number(page,"100000");amount.setHint("Non-negative whole amount");LinearLayout actions=row(page);
        button(actions,"READ / Refresh",new View.OnClickListener(){public void onClick(View v){request("currency",CURRENCY_KEYS[currencyType.getSelectedItemPosition()],-1,0,false);}});
        button(actions,"APPLY",new View.OnClickListener(){public void onClick(View v){try{
            final int index=currencyType.getSelectedItemPosition(),op=mode.getSelectedItemPosition();
            final long value=Long.parseLong(amount.getText().toString().trim());long max=index==4||index==6?1000000000000L:2000000000L;if(value<0||value>max)throw new NumberFormatException();
            final String key=CURRENCY_KEYS[index];confirm("Confirm resource edit",CURRENCY_LABELS[index]+"\\n"+(op==0?"SET":op==1?"ADD":"SUBTRACT")+" "+value+"\\nSect treasury edits require READ first.",new Runnable(){public void run(){request("currency",key,op,value,true);}});
        }catch(NumberFormatException ex){result.setText("Whole amount required. Personal/reputation limit: 2 billion; treasury/faith: 1 trillion.");}}});
        currencyType.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){public void onItemSelected(AdapterView<?> p,View v,int pos,long id){if(currencyCurrent!=null)currencyCurrent.setText("READ "+CURRENCY_LABELS[pos]+" to inspect its balance and target.");}public void onNothingSelected(AdapterView<?> p){}});
        text(page,"Personal contribution uses #10011; sect treasury uses Int64. City and Immortal Store tokens are separate. Lifetime earned totals/achievement counters are excluded. Check persistence after save/load.",12);
    }
    private void appendDiagnostic(String message){
        lastDiagnostic=message;android.util.Log.i("TOIModMenu",message);File file=new File(activity.getFilesDir(),"toimod-v03-diagnostics.txt");
        try{if(file.length()>131072)file.delete();FileOutputStream out=new FileOutputStream(file,true);try{out.write((System.currentTimeMillis()+" "+message+"\\n\\n").getBytes("UTF-8"));}finally{out.close();}}catch(IOException ignored){}
    }
'''
    s=s[:i]+helpers+s[i:]
    for expected in ['buildCurrencyEditor();','NativeBridge.takeGameResults()','NativeBridge.bridgeVersion()!=3','catalogRequestId','setCustomTitle(heading)']:
        if expected not in s:raise ValueError('Missing Java integration: '+expected)
    for obsolete in ['String receipt=NativeBridge.result();','lastReceipt=receipt','request("capacity","slots",0,amount,true)']:
        if obsolete in s:raise ValueError('Obsolete Java integration left behind: '+obsolete)
    return s
