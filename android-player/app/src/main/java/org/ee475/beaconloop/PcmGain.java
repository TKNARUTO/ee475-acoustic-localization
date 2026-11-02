package org.ee475.beaconloop;

/** A single bounded gain, common to every channel; no EQ, pitch or time change. */
public final class PcmGain {
    private PcmGain() {}
    public static double gain(byte[] pcm, boolean enabled) {
        if ((pcm.length & 1) != 0) throw new IllegalArgumentException("Incomplete PCM sample");
        if (!enabled) return 1.0;
        int peak = 0;
        for (int i=0; i<pcm.length; i+=2) {
            int sample=(short)((pcm[i]&255)|(pcm[i+1]<<8));
            peak=Math.max(peak,Math.abs(sample));
        }
        if (peak==0) return 1.0;
        return Math.min(Math.pow(10,3.0/20),Math.pow(10,-3.0/20)*32767/peak);
    }
    public static byte[] apply(byte[] source, double gain) {
        if (gain==1.0) return source;
        byte[] result=new byte[source.length];
        for (int i=0; i<source.length; i+=2) {
            int sample=(short)((source[i]&255)|(source[i+1]<<8));
            int value=(int)Math.round(sample*gain);
            value=Math.max(-32768,Math.min(32767,value));
            result[i]=(byte)value;result[i+1]=(byte)(value>>8);
        }
        return result;
    }
}
