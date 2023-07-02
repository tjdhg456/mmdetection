# !/usr/bin/env bash
for MODEL_NAME in faster_rcnn_r101_fpn_2x_mstrain_r50_fpn_2x_0.9_0.9,0.6 faster_rcnn_r50_fpn_2x_0.9_0.9,0.6_naive
do
    CUDA_VISIBLE_DEVICES=0,1,2,3 python -m torch.distributed.launch \
                                        --nproc_per_node=4 \
                                        --master_port=928 \
                                        train.py \
                                        --config configs/faster_rcnn_mcdet_student/coco_$MODEL_NAME.py \
                                        --seed 0 \
                                        --work-dir result/coco/mcdet/student/$MODEL_NAME \
                                        --launcher pytorch
done



#### SSIM
for MODEL_NAME in faster_rcnn_r101_2x_mstrain_r50_fpn_2x_SSIM+FSKD_0.9_0.9,0.6
do
    CUDA_VISIBLE_DEVICES=0,1,2,3 python -m torch.distributed.launch \
                                        --nproc_per_node=4 \
                                        --master_port=928 \
                                        train.py \
                                        --config others/SSIM/configs/faster_rcnn_ssim_student/coco_$MODEL_NAME.py \
                                        --seed 0 \
                                        --work-dir result/coco/ssim/student/$MODEL_NAME \
                                        --launcher pytorch
done


for MODEL_NAME in faster_rcnn_r101_2x_mstrain_r50_fpn_2x_SSIM_0.9_0.9,0.6
do
    CUDA_VISIBLE_DEVICES=4,5,6,7 python -m torch.distributed.launch \
                                        --nproc_per_node=4 \
                                        --master_port=91 \
                                        train.py \
                                        --config others/SSIM/configs/faster_rcnn_ssim_student/coco_$MODEL_NAME.py \
                                        --seed 0 \
                                        --work-dir result/coco/ssim/student/$MODEL_NAME \
                                        --launcher pytorch
done