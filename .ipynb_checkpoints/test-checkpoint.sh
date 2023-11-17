#!/bin/bash
source /root/miniconda3/bin/activate
source /root/miniconda3/bin/deactivate
conda init bash
conda activate /root/autodl-tmp/env/VT/
python ./Core/trans_speed.py --from_lang $1 --to_lang $2 --inf ./Segments/segments_info.txt