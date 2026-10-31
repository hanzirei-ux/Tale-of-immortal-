import org.npc.toibridge.ControlUiState;
public final class ControlUiStateTest {
    private static int checks;
    private static void check(boolean ok,String message){checks++;if(!ok)throw new AssertionError(message);}
    public static void main(String[] args){
        final ControlUiState state=new ControlUiState();final int[] submits={0};
        final Runnable callback=new Runnable(){public void run(){if(state.callbacksAllowed())submits[0]++;}};
        callback.run();check(submits[0]==1,"user change submits once");
        state.programmatic(new Runnable(){public void run(){callback.run();state.programmatic(callback);}});
        check(submits[0]==1,"programmatic/nested checkbox rollback never resubmits");
        check(state.callbacksAllowed(),"guard restored after rollback");
        try{state.programmatic(new Runnable(){public void run(){throw new IllegalStateException("simulated setter");}});}catch(IllegalStateException expected){}
        check(state.callbacksAllowed(),"guard restored even on setter exception");
        long old=state.beginOperation();state.record(5,"OUT_OF_RANGE Spiritual x150");
        long defense=state.beginOperation();state.record(8,"APPLIED Defense x16");
        check(!state.isLatest(old)&&state.isLatest(defense),"older asynchronous receipt cannot replace newer control result");
        check(state.last(8).equals("APPLIED Defense x16"),"Defense displays own current successful result");
        check(state.last(5).equals("OUT_OF_RANGE Spiritual x150"),"Spiritual failure remains scoped to Spiritual");
        state.record(5,"APPLIED Spiritual x2");check(!state.last(5).contains("OUT_OF_RANGE"),"valid retry clears its previous error");
        check(state.last(0).equals("NOT_APPLIED"),"untouched controls are not advertised as applied");
        System.out.println("PASS Java UI guard/result state: "+checks+" checks; no Android rendering test");
    }
}
