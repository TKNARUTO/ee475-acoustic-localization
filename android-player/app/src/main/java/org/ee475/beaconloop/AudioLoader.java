package org.ee475.beaconloop;

import android.media.AudioFormat;
import android.media.MediaCodec;
import android.media.MediaExtractor;
import android.media.MediaFormat;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

final class AudioLoader {
    static final int MAX_BYTES=32*1024*1024;
    static final class Audio {
        final byte[] pcm; final int rate,channels;
        Audio(byte[] pcm,int rate,int channels){this.pcm=pcm;this.rate=rate;this.channels=channels;}
        int frames(){return pcm.length/(2*channels);}
    }
    static Audio decode(File file) throws Exception {
        MediaExtractor extractor=new MediaExtractor();MediaCodec codec=null;
        try {
            extractor.setDataSource(file.getAbsolutePath());
            int track=-1;MediaFormat format=null;
            for(int i=0;i<extractor.getTrackCount();i++) {
                MediaFormat candidate=extractor.getTrackFormat(i);
                if(candidate.getString(MediaFormat.KEY_MIME).startsWith("audio/")){track=i;format=candidate;break;}
            }
            if(track<0)throw new IOException("No audio track found");
            extractor.selectTrack(track);
            int rate=format.getInteger(MediaFormat.KEY_SAMPLE_RATE),channels=format.getInteger(MediaFormat.KEY_CHANNEL_COUNT);
            if(channels<1||channels>2)throw new IOException("Choose mono or stereo audio");
            if(format.containsKey(MediaFormat.KEY_DURATION)&&format.getLong(MediaFormat.KEY_DURATION)>120_000_000L)
                throw new IOException("Choose a short audio file, up to 120 seconds");
            String mime=format.getString(MediaFormat.KEY_MIME);
            int encoding=format.containsKey(MediaFormat.KEY_PCM_ENCODING)?format.getInteger(MediaFormat.KEY_PCM_ENCODING):AudioFormat.ENCODING_PCM_16BIT;
            ByteArrayOutputStream output=new ByteArrayOutputStream();
            if("audio/raw".equals(mime)) {
                ByteBuffer buffer=ByteBuffer.allocate(256*1024);
                while(true) {
                    buffer.clear();int size=extractor.readSampleData(buffer,0);if(size<0)break;
                    byte[] data=new byte[size];buffer.position(0);buffer.get(data);append(output,data,encoding);extractor.advance();
                }
            } else {
                format.setInteger(MediaFormat.KEY_PCM_ENCODING,AudioFormat.ENCODING_PCM_16BIT);
                codec=MediaCodec.createDecoderByType(mime);codec.configure(format,null,null,0);codec.start();
                boolean inputDone=false,outputDone=false;long deadline=System.nanoTime()+60_000_000_000L;
                MediaCodec.BufferInfo info=new MediaCodec.BufferInfo();
                while(!outputDone) {
                    if(System.nanoTime()>deadline)throw new IOException("Audio decoding timed out");
                    if(!inputDone) {
                        int index=codec.dequeueInputBuffer(10000);
                        if(index>=0) {
                            ByteBuffer input=codec.getInputBuffer(index);int size=extractor.readSampleData(input,0);
                            if(size<0){codec.queueInputBuffer(index,0,0,0,MediaCodec.BUFFER_FLAG_END_OF_STREAM);inputDone=true;}
                            else {codec.queueInputBuffer(index,0,size,extractor.getSampleTime(),0);extractor.advance();}
                        }
                    }
                    int index=codec.dequeueOutputBuffer(info,10000);
                    if(index==MediaCodec.INFO_OUTPUT_FORMAT_CHANGED) {
                        MediaFormat out=codec.getOutputFormat();rate=out.getInteger(MediaFormat.KEY_SAMPLE_RATE);channels=out.getInteger(MediaFormat.KEY_CHANNEL_COUNT);
                        encoding=out.containsKey(MediaFormat.KEY_PCM_ENCODING)?out.getInteger(MediaFormat.KEY_PCM_ENCODING):AudioFormat.ENCODING_PCM_16BIT;
                    } else if(index>=0) {
                        if(info.size>0) {
                            ByteBuffer buffer=codec.getOutputBuffer(index);buffer.position(info.offset);buffer.limit(info.offset+info.size);
                            byte[] data=new byte[info.size];buffer.get(data);append(output,data,encoding);
                        }
                        outputDone=(info.flags&MediaCodec.BUFFER_FLAG_END_OF_STREAM)!=0;codec.releaseOutputBuffer(index,false);
                    }
                }
            }
            byte[] pcm=output.toByteArray();
            if(channels<1||channels>2||pcm.length<channels*2||pcm.length%(channels*2)!=0)
                throw new IOException("Unsupported decoded audio format");
            if(rate<=0||pcm.length/(double)(2*channels*rate)>120.)throw new IOException("Choose audio up to 120 seconds");
            return new Audio(pcm,rate,channels);
        } finally {
            if(codec!=null){try{codec.stop();}catch(Exception ignored){}codec.release();}
            extractor.release();
        }
    }
    private static void append(ByteArrayOutputStream output,byte[] data,int encoding) throws IOException {
        if(encoding==AudioFormat.ENCODING_PCM_FLOAT) {
            ByteBuffer floats=ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
            byte[] converted=new byte[data.length/2];int i=0;
            while(floats.remaining()>=4) {
                float value=floats.getFloat();int sample=Math.round(Math.max(-1f,Math.min(1f,value))*32767f);
                converted[i++]=(byte)sample;converted[i++]=(byte)(sample>>8);
            }
            data=converted;
        } else if(encoding!=AudioFormat.ENCODING_PCM_16BIT)throw new IOException("This PCM encoding is not supported");
        if(output.size()+data.length>MAX_BYTES)throw new IOException("Audio is too large; choose a shorter file");
        output.write(data);
    }
}
