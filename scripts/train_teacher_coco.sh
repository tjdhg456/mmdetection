# !/usr/bin/env bash
for MODEL_NAME in faster_rcnn_r50_fpn_1x_crop0.8 faster_rcnn_r50_fpn_1x_crop0.9
do
    CUDA_VISIBLE_DEVICES=0,1,2,3 python -m torch.distributed.launch \
                                        --nproc_per_node=4 \
                                        --master_port=909 \
                                        train.py \
                                        --config configs/faster_rcnn_mcdet_teacher/coco_$MODEL_NAME.py \
                                        --seed 0 \
                                        --work-dir result/coco/mcdet/teacher/$MODEL_NAME \
                                        --launcher pytorch
done