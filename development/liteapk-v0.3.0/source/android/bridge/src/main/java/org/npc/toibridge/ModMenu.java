package org.npc.toibridge;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.content.res.ColorStateList;
import android.graphics.drawable.GradientDrawable;
import android.text.Editable;
import android.text.TextWatcher;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.widget.*;
import java.io.*;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.zip.ZipFile;
import java.util.zip.ZipEntry;

/** In-Activity UI for the compiled native implementation. No system overlay permission. */
public final class ModMenu {
    private static ModMenu instance;
    private final Activity activity;
    private final Handler ui = new Handler(Looper.getMainLooper());
    private final SharedPreferences prefs;
    private final FrameLayout overlay;
    private final Button launcher;
    private final LinearLayout panel, page;
    private final TextView status, result;
    private final CheckBox backup;
    private final Spinner category;
    private final ArrayList<View> runtimeInputs = new ArrayList<View>();
    private boolean busy, initialized, ready;
    private boolean pendingCatalog, activeCombine, catalogRefreshNeeded;
    private EditText itemSearch, itemIdField;
    private Spinner itemTypeFilter;
    private LinearLayout itemList;
    private TextView itemInfo, itemSelected;
    private int catalogOffset=0, catalogTotal=0;
    private String selectedItemName="", selectedItemId="", catalogRequestKey="", lastDiagnostic="No operation logged yet";
    private long catalogRequestId;
    private final LinkedHashMap<Long,String> pendingActions=new LinkedHashMap<Long,String>();
    private Spinner currencyType;
    private TextView currencyCurrent;
    private static final String[] CURRENCY_KEYS={"money","contribution","city_token","immortal_token","sect_funds","sect_reputation","sect_faith"};
    private static final String[] CURRENCY_LABELS={"Spirit Stones / player money","Personal Sect Contribution","City Token","Immortal Store Token","Sect Funds (treasury)","Sect Reputation","Sect Faith Currency"};
    private final Runnable searchDebounce=new Runnable(){public void run(){submitCatalog();}};
    private static final int BG=Color.rgb(23,27,35), SURFACE=Color.rgb(48,59,74), FG=Color.rgb(244,248,255), MUTED=Color.rgb(184,203,223);
    private volatile boolean disposed;
    private long lastCapabilities = -1;
    private String bootStatus = "Initializing native component...";
    private int selected;
    private final Runnable pollTask=new Runnable(){public void run(){updatePoll();}};
    private static final String[] LABELS = {
        "God Mode", "Unlimited HP", "Unlimited Energy", "All damage", "Martial damage", "Spiritual damage",
        "Skill damage", "Ultimate damage", "Defense", "Martial resistance", "Spiritual resistance",
        "Critical rating override (not %)", "Critical damage", "Crit resistance rating (not %)",
        "Attack / shot speed", "Movement speed", "Skill cooldown factor", "Energy cost factor",
        "Global EXP", "Cultivation spot EXP", "Manual training EXP", "Combat skill EXP"
    };
    private static final double[] MIN={0,0,0,.1,.1,.1,.1,.1,.1,.1,.1,0,.1,0,1,1,0,0,1,1,1,1};
    private static final double[] MAX={1,1,1,100,100,100,100,100,100,100,100,100,100,100,10,10,1,1,100,100,100,100};
    private static final String[] STATS={"hp","hpMax","mp","mpMax","attack","defense","crit","critValue","guard","guardValue","phycicalFree","magicFree","moveSpeed","luck","life","health","healthMax","energy","energyMax","mood","moodMax","talent","abilityPoint","basisFire","basisFroze","basisThunder","basisWind","basisEarth","basisWood","basisBlade","basisSpear","basisSword","basisFist","basisPalm","basisFinger","refineElixir","refineWeapon","geomancy","symbol","herbal","mine"};

    public static void install(final Activity activity) {
        activity.runOnUiThread(new Runnable(){public void run(){
            if(instance!=null && instance.activity==activity)return;
            if(instance!=null)instance.release();
            instance=new ModMenu(activity);
        }});
    }
    public static void detach(Activity a){if(instance!=null&&instance.activity==a){instance.release();instance=null;}}
    private void release(){disposed=true;ui.removeCallbacksAndMessages(null);if(initialized)try{NativeBridge.closeMenu();}catch(Throwable ignored){}if(overlay.getParent() instanceof android.view.ViewGroup)((android.view.ViewGroup)overlay.getParent()).removeView(overlay);}
    private ModMenu(Activity a) {
        activity=a;prefs=a.getSharedPreferences("toi_modmenu_v02",0);
        FrameLayout decor=(FrameLayout)a.getWindow().getDecorView();
        overlay=new FrameLayout(a);overlay.setElevation(dp(100));overlay.setClipChildren(false);
        decor.addView(overlay,new FrameLayout.LayoutParams(-1,-1));
        launcher=button("TOI",null);launcher.setElevation(dp(102));launcher.setTextSize(14);launcher.setAlpha(.88f);
        final FrameLayout.LayoutParams iconParams=new FrameLayout.LayoutParams(dp(56),dp(48));
        overlay.addView(launcher,iconParams);
        panel=new LinearLayout(a);panel.setOrientation(LinearLayout.VERTICAL);panel.setPadding(dp(10),dp(8),dp(10),dp(8));
        panel.setClickable(true);panel.setFocusable(true);panel.setBackgroundColor(Color.argb(251,23,27,35));panel.setElevation(dp(101));
        FrameLayout.LayoutParams panelParams=new FrameLayout.LayoutParams(dp(390),dp(420),Gravity.TOP|Gravity.RIGHT);panelParams.setMargins(dp(4),dp(4),dp(4),dp(4));
        overlay.addView(panel,panelParams);panel.setVisibility(View.GONE);
        text(panel,"Tale of Immortal v0.3 — Player only | Test build",15);
        category=new Spinner(a);
        category.setAdapter(spinnerAdapter(new String[]{"Combat","EXP / Cultivation","Player Stats / Inventory","Items / Recipes","Skills / Artifacts","Currency & Contribution","Diagnostics"}));
        category.setBackground(boxBackground(SURFACE));
        panel.addView(category,new LinearLayout.LayoutParams(-1,dp(48)));
        category.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){public void onItemSelected(AdapterView<?> p,View v,int position,long id){selected=position;buildPage();}public void onNothingSelected(AdapterView<?> p){}});
        LinearLayout top=row(panel);
        button(top,"Hide",new View.OnClickListener(){public void onClick(View v){panel.setVisibility(View.GONE);}});
        button(top,"Reset",new View.OnClickListener(){public void onClick(View v){resetRuntime();}});
        button(top,"Load",new View.OnClickListener(){public void onClick(View v){loadSaved();buildPage();}});
        backup=new CheckBox(a);backup.setText("Save backup completed (required for permanent edits)");backup.setTextColor(FG);backup.setButtonTintList(ColorStateList.valueOf(Color.rgb(81,183,225)));backup.setTextSize(12);panel.addView(backup);
        status=text(panel,bootStatus,10);status.setMaxLines(2);
        ScrollView scroll=new ScrollView(a);page=new LinearLayout(a);page.setOrientation(LinearLayout.VERTICAL);scroll.addView(page);panel.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        result=text(panel,"No gameplay result verified yet",12);result.setMaxLines(4);result.setMovementMethod(new android.text.method.ScrollingMovementMethod());result.setTextIsSelectable(true);result.setTextColor(MUTED);
        launcher.setOnTouchListener(new View.OnTouchListener(){float sx,sy,ox,oy;boolean moved;
            public boolean onTouch(View v,MotionEvent e){
                if(e.getAction()==MotionEvent.ACTION_DOWN){sx=e.getRawX();sy=e.getRawY();ox=v.getX();oy=v.getY();moved=false;return true;}
                if(e.getAction()==MotionEvent.ACTION_MOVE){float dx=e.getRawX()-sx,dy=e.getRawY()-sy;if(Math.abs(dx)+Math.abs(dy)>dp(6))moved=true;v.setX(clamp(ox+dx,0,overlay.getWidth()-v.getWidth()));v.setY(clamp(oy+dy,0,overlay.getHeight()-v.getHeight()));return true;}
                if(e.getAction()==MotionEvent.ACTION_UP){if(!moved){panel.setVisibility(panel.getVisibility()==View.VISIBLE?View.GONE:View.VISIBLE);panel.bringToFront();launcher.bringToFront();poll();}prefs.edit().putFloat("icon_x",v.getX()/Math.max(1,overlay.getWidth()-v.getWidth())).putFloat("icon_y",v.getY()/Math.max(1,overlay.getHeight()-v.getHeight())).apply();return true;}return true;
            }});
        overlay.addOnLayoutChangeListener(new View.OnLayoutChangeListener(){public void onLayoutChange(View v,int l,int t,int r,int b,int ol,int ot,int or,int ob){if((r-l)!=(or-ol)||(b-t)!=(ob-ot))layout();}});
        ui.post(new Runnable(){public void run(){layout();beginInitialization();}});
    }
    private int dp(float v){return (int)(activity.getResources().getDisplayMetrics().density*v+.5f);}
    private float clamp(float value,float min,float max){return Math.max(min,Math.min(Math.max(min,max),value));}
    private void layout(){
        launcher.setX(clamp(prefs.getFloat("icon_x",.02f)*(overlay.getWidth()-launcher.getWidth()),0,overlay.getWidth()-launcher.getWidth()));
        launcher.setY(clamp(prefs.getFloat("icon_y",.2f)*(overlay.getHeight()-launcher.getHeight()),0,overlay.getHeight()-launcher.getHeight()));
        FrameLayout.LayoutParams p=(FrameLayout.LayoutParams)panel.getLayoutParams();p.width=Math.min(dp(390),Math.max(dp(220),overlay.getWidth()-dp(8)));p.height=Math.max(dp(180),overlay.getHeight()-dp(8));panel.setLayoutParams(p);overlay.bringToFront();launcher.bringToFront();
    }
    private LinearLayout row(LinearLayout parent){LinearLayout l=new LinearLayout(activity);l.setOrientation(LinearLayout.HORIZONTAL);parent.addView(l,new LinearLayout.LayoutParams(-1,-2));return l;}
    private GradientDrawable boxBackground(int color){
        GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(5));
        d.setStroke(dp(1),Color.rgb(87,109,130));return d;
    }
    private TextView text(LinearLayout parent,String value,int size){
        TextView t=new TextView(activity);t.setText(value);t.setTextColor(FG);t.setTextSize(size);
        t.setPadding(dp(3),dp(5),dp(3),dp(5));parent.addView(t);return t;
    }
    private Button button(String label,View.OnClickListener click){
        Button b=new Button(activity);b.setText(label);b.setAllCaps(false);b.setTextColor(FG);
        b.setTextSize(13);b.setMinHeight(dp(44));b.setBackground(boxBackground(SURFACE));
        if(click!=null)b.setOnClickListener(click);return b;
    }
    private Button button(LinearLayout parent,String label,View.OnClickListener click){
        Button b=button(label,click);LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,dp(46),1);
        lp.setMargins(dp(2),dp(2),dp(2),dp(2));parent.addView(b,lp);return b;
    }
    private EditText edit(LinearLayout parent,String value,boolean numeric){
        EditText e=new EditText(activity);e.setSingleLine(true);e.setTextColor(FG);e.setHintTextColor(MUTED);
        e.setTextSize(15);e.setPadding(dp(12),0,dp(12),0);e.setBackground(boxBackground(SURFACE));
        e.setInputType(numeric?InputType.TYPE_CLASS_NUMBER|InputType.TYPE_NUMBER_FLAG_DECIMAL|InputType.TYPE_NUMBER_FLAG_SIGNED:InputType.TYPE_CLASS_TEXT);
        e.setText(value);LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(48));lp.setMargins(dp(2),dp(3),dp(2),dp(4));parent.addView(e,lp);return e;
    }
    private EditText number(LinearLayout parent,String value){return edit(parent,value,true);}
    private ArrayAdapter<String> spinnerAdapter(String[] labels){
        return new ArrayAdapter<String>(activity,android.R.layout.simple_spinner_item,labels){
            @Override public View getView(int pos,View recycled,android.view.ViewGroup parent){
                TextView v=(TextView)super.getView(pos,recycled,parent);v.setTextColor(FG);v.setTextSize(15);
                v.setPadding(dp(12),dp(8),dp(8),dp(8));v.setText(labels[pos]+"  ▾");return v;
            }
            @Override public View getDropDownView(int pos,View recycled,android.view.ViewGroup parent){
                TextView v=(TextView)super.getDropDownView(pos,recycled,parent);v.setTextColor(FG);
                v.setTextSize(15);v.setPadding(dp(12),dp(12),dp(12),dp(12));v.setBackgroundColor(SURFACE);return v;
            }
        };
    }
    private Spinner spinner(LinearLayout parent,String[] labels){
        Spinner s=new Spinner(activity);s.setAdapter(spinnerAdapter(labels));s.setBackground(boxBackground(SURFACE));
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(48));lp.setMargins(dp(2),dp(3),dp(2),dp(3));parent.addView(s,lp);return s;
    }
    private void buildPage(){
        if(page==null)return;
        ui.removeCallbacks(searchDebounce);
        page.removeAllViews();runtimeInputs.clear();
        itemList=null;itemInfo=null;itemSelected=null;itemSearch=null;itemTypeFilter=null;itemIdField=null;
        currencyType=null;currencyCurrent=null;selectedItemName="";selectedItemId="";
        if(selected==0||selected==1){
            text(page,"Saved settings are loaded only when you tap Load. Reset disables runtime effects; persistent edits remain.",12);
            int start=selected==0?0:18,end=selected==0?18:22;
            for(int id=start;id<end;id++)controlRow(id);
            final CheckBox combine=new CheckBox(activity);combine.setButtonTintList(ColorStateList.valueOf(Color.rgb(81,183,225)));combine.setText("Multiply global × category (cap ×100)");combine.setTextColor(FG);combine.setChecked(activeCombine);
            combine.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener(){public void onCheckedChanged(CompoundButton b,boolean c){if(ready&&NativeBridge.setCombine(c?1:0)){activeCombine=c;prefs.edit().putBoolean("combine",c).apply();}}});page.addView(combine);
            text(page,"Default: an enabled specific category replaces global. EXP category hooks keep NPC gains unchanged.",12);
        }else if(selected==2){
            text(page,"Base-stat edits are permanent. Current/max HP and battle modifiers are separate. Back up your save first.",12);
            final Spinner stat=spinner(page,STATS),operation=spinner(page,new String[]{"SET","ADD","SUBTRACT","MULTIPLY"});final EditText value=number(page,"100");
            LinearLayout buttons=row(page);button(buttons,"Read",new View.OnClickListener(){public void onClick(View v){request("read",STATS[stat.getSelectedItemPosition()],0,0,false);}});
            button(buttons,"Apply",new View.OnClickListener(){public void onClick(View v){try{request("stat",STATS[stat.getSelectedItemPosition()],operation.getSelectedItemPosition(),Double.parseDouble(value.getText().toString()),true);}catch(NumberFormatException ex){result.setText("Enter a valid number");}}});
            text(page,"INVENTORY CAPACITY — Effective slots, including ring/plugin bonuses. SET/ADD/SUBTRACT protects occupied slots. Limit: 2,000.",13);
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
        }else if(selected==3){
            buildItemBrowser();
        }else if(selected==4){
            final EditText exp=number(page,"100");
            button(row(page),"Add cultivation EXP",new View.OnClickListener(){public void onClick(View v){try{int n=Integer.parseInt(exp.getText().toString());if(n<1||n>9999999)throw new NumberFormatException();request("gm","jingyan_"+n,0,0,true);}catch(NumberFormatException e){result.setText("EXP must be 1..9999999");}}});
            gmButton("Recover stamina","huifu");gmButton("Learn manuals already in bag","xueximiji");gmButton("Max manual cultivation","xiulianmiji");gmButton("Max bag manual entries","citiaomanji");gmButton("Add grade-1 breakthrough materials","tupocailiao_1");gmButton("Repair player's artifacts","xiulifabao_0");
            final EditText jade=number(page,"1000");button(row(page),"Set Bagua Jade protection points",new View.OnClickListener(){public void onClick(View v){try{int n=Integer.parseInt(jade.getText().toString());if(n<0||n>9999999)throw new NumberFormatException();request("gm","shuangyupei_"+n,0,0,true);}catch(NumberFormatException e){result.setText("Points must be 0..9999999");}}});
            gmButton("Unlock Eye of Providence skills","haotianyanjiesuojineng");
            text(page,"Each button invokes the game's GM implementation. Results still need device/save-load testing. NPC editing is excluded.",12);
        }else if(selected==5){
            buildCurrencyEditor();
        }else{
            text(page,"Exact LiteAPK IL2CPP and metadata hashes are required. Every hook checks the actual mapped prologue before installation. No device test has been performed here.",12);
            text(page,"Controls without a successfully installed native adapter remain disabled. The startup protector library and original native lifecycle are retained.",12);
            TextView details=text(page,lastDiagnostic,12);details.setTextIsSelectable(true);
            button(row(page),"Copy last operation / error",new View.OnClickListener(){public void onClick(View v){android.content.ClipboardManager c=(android.content.ClipboardManager)activity.getSystemService(android.content.Context.CLIPBOARD_SERVICE);if(c!=null)c.setPrimaryClip(android.content.ClipData.newPlainText("TOI diagnostics",lastDiagnostic));}});
            button(row(page),"Retry initialization",new View.OnClickListener(){public void onClick(View v){beginInitialization();}});
        }
    }
    private long queuedId(String reply){if(reply==null||!reply.startsWith("QUEUED:"))return 0;try{return Long.parseLong(reply.substring(7));}catch(NumberFormatException e){return 0;}}
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
            final String key=CURRENCY_KEYS[index];confirm("Confirm resource edit",CURRENCY_LABELS[index]+"\n"+(op==0?"SET":op==1?"ADD":"SUBTRACT")+" "+value+"\nSect treasury edits require READ first.",new Runnable(){public void run(){request("currency",key,op,value,true);}});
        }catch(NumberFormatException ex){result.setText("Whole amount required. Personal/reputation limit: 2 billion; treasury/faith: 1 trillion.");}}});
        currencyType.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){public void onItemSelected(AdapterView<?> p,View v,int pos,long id){if(currencyCurrent!=null)currencyCurrent.setText("READ "+CURRENCY_LABELS[pos]+" to inspect its balance and target.");}public void onNothingSelected(AdapterView<?> p){}});
        text(page,"Personal contribution uses #10011; sect treasury uses Int64. City and Immortal Store tokens are separate. Lifetime earned totals/achievement counters are excluded. Check persistence after save/load.",12);
    }
    private void appendDiagnostic(String message){
        lastDiagnostic=message;android.util.Log.i("TOIModMenu",message);File file=new File(activity.getFilesDir(),"toimod-v03-diagnostics.txt");
        try{if(file.length()>131072)file.delete();FileOutputStream out=new FileOutputStream(file,true);try{out.write((System.currentTimeMillis()+" "+message+"\n\n").getBytes("UTF-8"));}finally{out.close();}}catch(IOException ignored){}
    }
    /** Actual item configuration, 40 rows per page. Only a tapped row selects an ID. */
    private void buildItemBrowser(){
        text(page,"Browse actual item IDs. Pick All Types to scroll every item or filter by category. Search suggestions update as you type.",12);
        itemTypeFilter=spinner(page,new String[]{"All Types","Pills","Manuals","Equipment","Materials / Herbs","Other","Recipe (Alchemy books)"});
        itemSearch=edit(page,"",false);itemSearch.setHint("Search partial item name or ID...");
        itemInfo=text(page,"Loading catalog...",12);itemInfo.setTextColor(MUTED);
        final ScrollView listScroll=new ScrollView(activity);listScroll.setFillViewport(false);
        itemList=new LinearLayout(activity);itemList.setOrientation(LinearLayout.VERTICAL);listScroll.addView(itemList);
        LinearLayout.LayoutParams listSize=new LinearLayout.LayoutParams(-1,dp(216));listSize.setMargins(dp(2),dp(3),dp(2),dp(3));
        page.addView(listScroll,listSize);
        LinearLayout nav=row(page);
        button(nav,"Previous",new View.OnClickListener(){public void onClick(View v){catalogOffset=Math.max(0,catalogOffset-40);scheduleCatalog();}});
        button(nav,"Next",new View.OnClickListener(){public void onClick(View v){if(catalogOffset+40<catalogTotal){catalogOffset+=40;scheduleCatalog();}}});
        itemSelected=text(page,"No item selected",13);
        itemIdField=number(page,"");itemIdField.setHint("Tap an item to select its ID");itemIdField.setKeyListener(null);itemIdField.setFocusable(false);
        final EditText qty=number(page,"1");qty.setHint("Quantity 1..9999");
        button(row(page),"Add selected item / recipe book",new View.OnClickListener(){public void onClick(View v){
            try{int n=Integer.parseInt(qty.getText().toString().trim());if(n<1||n>9999)throw new NumberFormatException();
                final String id=selectedItemId,name=selectedItemName;final int quantity=n;
                if(id.isEmpty()){result.setText("Tap a catalog item before adding it");return;}
                confirm("Add selected item",name+" (#"+id+")\nQuantity: "+quantity,new Runnable(){public void run(){request("item",id,0,quantity,true);}});
            }catch(NumberFormatException ex){result.setText("Quantity must be 1..9999");}
        }});
        text(page,"Recipe filters use actual Alchemy formula IDs matched to item IDs. Forge/Talisman recipe filtering is not mapped yet. Adding a recipe item does not learn it.",12);
        itemTypeFilter.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){
            public void onItemSelected(android.widget.AdapterView<?> p,View v,int pos,long id){catalogOffset=0;scheduleCatalog();}
            public void onNothingSelected(android.widget.AdapterView<?> p){}
        });
        itemSearch.addTextChangedListener(new TextWatcher(){
            public void beforeTextChanged(CharSequence s,int st,int count,int after){}
            public void onTextChanged(CharSequence s,int st,int before,int count){catalogOffset=0;scheduleCatalog();}
            public void afterTextChanged(Editable e){}
        });
        scheduleCatalog();
    }
    private void scheduleCatalog(){
        if(selected!=3 || itemSearch==null)return;
        ui.removeCallbacks(searchDebounce);
        if(itemInfo!=null)itemInfo.setText("Searching actual catalog...");
        ui.postDelayed(searchDebounce,330);
    }
    private void submitCatalog(){
        if(selected!=3||itemTypeFilter==null||itemSearch==null||itemList==null)return;
        if(!ready){if(itemInfo!=null)itemInfo.setText("Waiting for Unity native adapter...");return;}
        if(pendingCatalog){catalogRefreshNeeded=true;return;}
        int[] types={-1,1,2,3,5,6,254};
        int filter=types[Math.max(0,Math.min(types.length-1,itemTypeFilter.getSelectedItemPosition()))];
        String search=itemSearch.getText().toString().trim().replace('|',' ');
        if(search.length()>80)search=search.substring(0,80);
        String key="@"+filter+"|"+search+"|"+catalogOffset;
        String reply=NativeBridge.request("catalog",key,0,0,false);
        catalogRequestId=queuedId(reply);catalogRequestKey=key;pendingCatalog=catalogRequestId!=0;
        if(itemInfo!=null)itemInfo.setText(pendingCatalog?"Loading matching items...":reply);
        if(pendingCatalog)poll();
    }
    private void renderCatalog(String receipt){
        if(itemList==null||itemInfo==null||selected!=3)return;
        String[] lines=receipt.split("\n",-1);
        String[] header=lines[0].split("\t",-1);
        if(header.length!=4){itemInfo.setText("Malformed native catalog header");return;}
        try{catalogTotal=Integer.parseInt(header[1]);catalogOffset=Integer.parseInt(header[2]);}
        catch(NumberFormatException ex){itemInfo.setText("Malformed native catalog count");return;}
        itemList.removeAllViews();
        int displayed=0;
        for(int i=1;i<lines.length;i++){
            if(lines[i].isEmpty())continue;
            final String[] col=lines[i].split("\t",-1);
            if(col.length<4||!col[0].matches("[0-9]+"))continue;
            final String id=col[0],name=col[1];
            String label=(name.isEmpty()?"Unnamed item":name)+"  •  #"+id+"  (type "+col[2]+", Lv "+col[3]+")";
            Button choose=button(label,new View.OnClickListener(){public void onClick(View v){
                if(itemIdField!=null)itemIdField.setText(id);
                selectedItemName=name;selectedItemId=id;
                if(itemSelected!=null)itemSelected.setText("Selected: "+name+" (#"+id+")");
            }});
            choose.setGravity(Gravity.LEFT|Gravity.CENTER_VERTICAL);
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(48));lp.setMargins(0,dp(2),0,dp(2));
            itemList.addView(choose,lp);displayed++;
        }
        if(catalogTotal==0)itemInfo.setText("No items match this category/search");
        else itemInfo.setText("Showing "+(catalogOffset+1)+"–"+(catalogOffset+displayed)+" of "+catalogTotal+" items · scroll to choose");
        if(displayed==0)text(itemList,"No matching items in this category.",13);
    }
    private void controlRow(final int id){
        final CheckBox enable=new CheckBox(activity);enable.setButtonTintList(ColorStateList.valueOf(Color.rgb(81,183,225)));boolean current=ready&&NativeBridge.controlEnabled(id);enable.setChecked(current);enable.setText(LABELS[id]+" ["+MIN[id]+".."+MAX[id]+"]"+(current?" — ON":" — OFF"));enable.setTextColor(Color.WHITE);enable.setTextSize(13);
        page.addView(enable);final EditText value=number(page,prefs.getString("v"+id,defaultValue(id)));
        if(id<3)value.setVisibility(View.GONE);
        final SeekBar slider=new SeekBar(activity);slider.setProgressTintList(ColorStateList.valueOf(Color.rgb(81,183,225)));slider.setThumbTintList(ColorStateList.valueOf(FG));slider.setMax(1000);double initial;try{initial=Double.parseDouble(value.getText().toString());}catch(Exception e){initial=1;}
        slider.setProgress((int)Math.max(0,Math.min(1000,1000*(initial-MIN[id])/(MAX[id]-MIN[id]))));if(id>=3)page.addView(slider);
        slider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){public void onProgressChanged(SeekBar s,int n,boolean user){if(user)value.setText(String.format(java.util.Locale.US,"%.3f",MIN[id]+(MAX[id]-MIN[id])*n/1000.0));}public void onStartTrackingTouch(SeekBar s){}public void onStopTrackingTouch(SeekBar s){}});
        enable.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener(){public void onCheckedChanged(CompoundButton b,boolean on){apply(id,on,value,enable);}});
        Button apply=button(row(page),"Apply value",new View.OnClickListener(){public void onClick(View v){apply(id,enable.isChecked(),value,enable);}});
        enable.setTag(Integer.valueOf(id));value.setTag(Integer.valueOf(id));slider.setTag(Integer.valueOf(id));apply.setTag(Integer.valueOf(id));
        runtimeInputs.add(enable);runtimeInputs.add(value);runtimeInputs.add(slider);runtimeInputs.add(apply);updateEnabled();
    }
    private void apply(int id,boolean on,EditText field,CheckBox label){
        try{double value=id<3?1:Double.parseDouble(field.getText().toString());if(!ready||!NativeBridge.setControl(id,on,value)){label.setChecked(ready&&NativeBridge.controlEnabled(id));result.setText("Rejected or hook unavailable");return;}prefs.edit().putBoolean("e"+id,on).putString("v"+id,Double.toString(value)).apply();label.setText(LABELS[id]+" ["+MIN[id]+".."+MAX[id]+"]"+(on?" — ON":" — OFF"));}
        catch(NumberFormatException ex){label.setChecked(ready&&NativeBridge.controlEnabled(id));result.setText("Enter a finite value within the displayed range");}
    }
    private void updateEnabled(){for(View v:runtimeInputs){Integer id=(Integer)v.getTag();v.setEnabled(ready && (lastCapabilities&(1L<<id.intValue()))!=0);}}
    private String defaultValue(int id){return id==11||id==13?"0":"1";}
    private void resetRuntime(){if(!ready)return;NativeBridge.resetControls();activeCombine=false;SharedPreferences.Editor e=prefs.edit().putBoolean("combine",false);for(int i=0;i<22;i++)e.putBoolean("e"+i,false).putString("v"+i,defaultValue(i));e.apply();buildPage();}
    private void loadSaved(){if(!ready){result.setText("Wait for native adapters");return;}for(int i=0;i<22;i++)if((lastCapabilities&(1L<<i))!=0)try{NativeBridge.setControl(i,prefs.getBoolean("e"+i,false),Double.parseDouble(prefs.getString("v"+i,defaultValue(i))));}catch(Exception ignored){}activeCombine=prefs.getBoolean("combine",false);NativeBridge.setCombine(activeCombine?1:0);result.setText("Saved runtime settings applied; persistent edits not repeated");}
    private void gmButton(String label,final String command){button(row(page),label,new View.OnClickListener(){public void onClick(View v){request("gm",command,0,0,true);}});}
    private void request(final String kind,final String key,final int operation,final double value,boolean persistent){
        if(!ready){result.setText("Native adapters are not ready");return;}
        if(persistent&&!backup.isChecked()){result.setText("Back up the save, then check the acknowledgment");return;}
        String reply=NativeBridge.request(kind,key,operation,value,backup.isChecked());
        result.setText(reply);
        long id=queuedId(reply);if(id!=0)pendingActions.put(Long.valueOf(id),kind+" ["+key+"]");
        poll();
    }
    private void beginInitialization(){
        if(busy)return;busy=true;
        new Thread(new Runnable(){public void run(){String message;
            try{
                if(NativeBridge.bridgeVersion()!=3)throw new IOException("DEX/native API mismatch: install both v0.3 files together");
                File lib=new File(activity.getApplicationInfo().nativeLibraryDir,"libil2cpp.so");
                if(!lib.isFile()){
                    lib=new File(activity.getCacheDir(),"toi_baseline_libil2cpp.so");
                    if(!lib.isFile()||lib.length()!=144951312L){
                        String[] splits=activity.getApplicationInfo().splitSourceDirs;
                        ArrayList<String> apks=new ArrayList<String>();apks.add(activity.getApplicationInfo().sourceDir);
                        if(splits!=null)for(String split:splits)apks.add(split);
                        boolean copied=false;
                        for(String apk:apks){ZipFile z=new ZipFile(apk);try{ZipEntry entry=z.getEntry("lib/arm64-v8a/libil2cpp.so");if(entry!=null){InputStream in=z.getInputStream(entry);FileOutputStream out=new FileOutputStream(lib);try{byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)out.write(b,0,n);}finally{in.close();out.close();}copied=true;break;}}finally{z.close();}}
                        if(!copied)throw new IOException("ARM64 IL2CPP not found in APK or ABI splits");
                    }
                }
                File metadata=new File(activity.getFilesDir(),"toimod/global-metadata.dat");
                if(!metadata.isFile()){
                    metadata=new File(activity.getCacheDir(),"toi_baseline_metadata.dat");
                    if(!metadata.isFile()||metadata.length()!=42923616L){
                        InputStream in=null;String[] paths={"bin/Data/Managed/Metadata/global-metadata.dat","toimod/global-metadata.dat"};
                        for(String path:paths)try{in=activity.getAssets().open(path);break;}catch(IOException ignored){}
                        if(in==null)throw new IOException("Metadata asset missing; see installation instructions");
                        FileOutputStream out=new FileOutputStream(metadata);try{byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)out.write(b,0,n);}finally{in.close();out.close();}
                    }
                }
                message=NativeBridge.prepare(lib.getAbsolutePath(),metadata.getAbsolutePath());initialized=message.startsWith("BASELINE_MATCHED");
            }catch(Throwable e){message="INIT FAILED: "+e.getClass().getSimpleName()+": "+e.getMessage();}
            final String resultMessage=message;ui.post(new Runnable(){public void run(){if(disposed)return;bootStatus=resultMessage;status.setText(bootStatus);busy=false;poll();}});
        }},"TOI-Prepare").start();
    }
    private void poll(){
        ui.removeCallbacks(pollTask);ui.post(pollTask);
    }
    private void updatePoll(){
        if(disposed)return;
        if(initialized){String s=NativeBridge.status();lastCapabilities=NativeBridge.capabilities();
            boolean previousReady=ready;ready=lastCapabilities!=0;status.setText(s);updateEnabled();
            if(!previousReady&&ready&&selected==3)scheduleCatalog();
            try{
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
                        pendingActions.remove(Long.valueOf(id));result.setText(kind+" — "+state+"\n"+message);
                        result.setTextColor("FAILED".equals(state)||"BLOCKED".equals(state)||"REJECTED".equals(state)?Color.rgb(255,174,164):MUTED);
                        if("currency".equals(kind)&&currencyCurrent!=null&&currencyType!=null&&key.equals(CURRENCY_KEYS[currencyType.getSelectedItemPosition()]))currencyCurrent.setText(state+"\n"+message);
                        appendDiagnostic(kind+" ["+key+"] "+state+"\n"+message);
                    }
                }
            }catch(Exception ex){result.setText("Receipt decode error: "+ex.getClass().getSimpleName()+": "+ex.getMessage());}

        }
        if(panel.getVisibility()==View.VISIBLE&&!activity.isFinishing())ui.postDelayed(pollTask,pendingCatalog||!pendingActions.isEmpty()?100:1000);
    }
}
