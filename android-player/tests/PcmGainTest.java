import org.ee475.beaconloop.PcmGain;
import java.util.Arrays;

public final class PcmGainTest {
    static byte[] pcm(int... values){byte[] out=new byte[values.length*2];for(int i=0;i<values.length;i++){out[2*i]=(byte)values[i];out[2*i+1]=(byte)(values[i]>>8);}return out;}
    static int sample(byte[] bytes,int i){return (short)((bytes[2*i]&255)|(bytes[2*i+1]<<8));}
    static void check(boolean value,String name){if(!value)throw new AssertionError(name);}
    public static void main(String[] args) {
        int checks=0;
        byte[] original=pcm(0,1000,-1000,32767,-32768),copy=original.clone();
        check(PcmGain.gain(original,false)==1.&&Arrays.equals(PcmGain.apply(original,1.),original),"Disabled = original bytes");checks++;
        check(PcmGain.gain(pcm(0,0),true)==1.,"Silence is not boosted");checks++;
        check(Math.abs(20*Math.log10(PcmGain.gain(pcm(100,-100),true))-3.)<1e-8,"Boost capped at 3 dB");checks++;
        double gain=PcmGain.gain(original,true);byte[] out=PcmGain.apply(original,gain);
        for(int i=0;i<out.length/2;i++)check(Math.abs(sample(out,i))<=23197,"Headroom preserved");checks++;
        check(Arrays.equals(original,copy),"Original buffer untouched");checks++;
        byte[] stereo=pcm(0,1000,0,-2000,0,3000);byte[] scaled=PcmGain.apply(stereo,PcmGain.gain(stereo,true));
        check(sample(scaled,0)==0&&sample(scaled,2)==0&&sample(scaled,4)==0,"Silent stereo channel stays silent");checks++;
        for(int i=0;i<2000;i++) {
            int value=(int)Math.round(20000*Math.sin(i*.251));byte[] input=pcm(value,0);double g=PcmGain.gain(input,true);
            int result=sample(PcmGain.apply(input,g),0);check(Math.abs(result-value*g)<=.501,"Scalar gain only, quantization bound");
        }checks++;
        check(out.length==original.length,"Sample count unchanged");checks++;
        try{PcmGain.gain(new byte[1],true);throw new AssertionError("Odd input accepted");}catch(IllegalArgumentException expected){}checks++;
        System.out.println("{\"passed\":true,\"checks\":"+checks+",\"phone_device_test\":false}");
    }
}
