#!/bin/bash
source /root/miniconda3/bin/activate
source /root/miniconda3/bin/deactivate
conda init bash
conda activate /root/autodl-tmp/env/VT/
python ./Core/wav_extract.py --video_path ./INPUT/
cp ./INPUT/audio.wav ./Core/MVSEP-MDX23-Colab_v2/input
python ./Core/MVSEP-MDX23-Colab_v2/inference.py --input_audio ./Core/MVSEP-MDX23-Colab_v2/input/audio.wav --large_gpu --weight_MDXv3 6 --weight_VOCFT 5 --weight_HQ3 2 --chunk_size 1000000 --overlap_demucs 0.8 --overlap_MDX 0 --overlap_MDXv3 20 --output_format 'FLOAT' --bigshifts 21 --vocals_only true --output_folder ./Core/MVSEP-MDX23-Colab_v2/output/
python ./Core/ASR.py --vocal_path ./Core/MVSEP-MDX23-Colab_v2/output/audio_vocals.wav 
python ./Core/trans_speed.py --from_lang $1 --to_lang $2 --inf ./Segments/segments_info.txt
python Core/merge.py --seg_path /root/autodl-tmp/Segments/segments_info.txt --bgm_path /root/autodl-tmp/Core/MVSEP-MDX23-Colab_v2/output/audio_instrum.wav --speed_path /root/autodl-tmp/Trans_speed_vocals/ --output_merge /root/autodl-tmp/OUTPUT/merge.wav
cp /root/autodl-tmp/OUTPUT/merge.wav /root/autodl-tmp/Core/video-retalking/examples/audio/
cp /root/autodl-tmp/INPUT/video.mp4 /root/autodl-tmp/Core/video-retalking/examples/face/
conda deactivate
conda activate /root/autodl-tmp/env/vrt/
cd /root/autodl-tmp/Core/video-retalking/
python inference.py --face ./examples/face/video.mp4 --audio ./examples/audio/merge.wav --outfile /root/autodl-tmp/OUTPUT/result.mp4