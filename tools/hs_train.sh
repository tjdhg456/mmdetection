# #--------------------------------   FASTER RCNN TEACHER   --------------------------------#

# MODEL_NAME='coco_faster_rcnn_r50_dc5_1x'
# MODEL_NAME='coco_faster_rcnn_r101_fpn_1x'
# MODEL_NAME='coco_faster_rcnn_r101_fpn_2x'
# MODEL_NAME='coco_faster_rcnn_x101_32x4d_fpn_1x'
# MODEL_NAME='coco_faster_rcnn_r50_fpn_2x'
# CUDA_VISIBLE_DEVICES=4,5,6,7 python -m torch.distributed.launch \
#                                 --nproc_per_node=4 \
#                                 --master_port 1025 \
#                                 train.py \
#                                 --config configs/faster_rcnn/${MODEL_NAME}.py \
#                                 --seed 0 \
#                                 --work-dir result/coco/${MODEL_NAME} \
#                                 --launcher pytorch



# #--------------------------------   FASTER RCNN STUDENT   --------------------------------#

# MODEL_NAME='faster_rcnn_r50_dc5_1x_fskd'
# CUDA_VISIBLE_DEVICES=3,4,5,6 python -m torch.distributed.launch \
#                                 --nproc_per_node=4 \
#                                 --master_port 1026 \
#                                 train.py \
#                                 --config configs/faster_rcnn_kd/coco_${MODEL_NAME}.py \
#                                 --seed 0 \
#                                 --work-dir result/coco/${MODEL_NAME} \
#                                 --launcher pytorch


# #--------------------------------   MASK RCNN TEACHER   --------------------------------#

# MODEL_NAME='coco_mask_rcnn_r50_fpn_1x'
# MODEL_NAME='coco_mask_rcnn_r101_fpn_1x'
# CUDA_VISIBLE_DEVICES=4,5,6,7 python -m torch.distributed.launch \
#                                 --nproc_per_node=4 \
#                                 --master_port 1028 \
#                                 train.py \
#                                 --config configs/mask_rcnn/${MODEL_NAME}.py \
#                                 --seed 0 \
#                                 --work-dir result/coco/${MODEL_NAME} \
#                                 --launcher pytorch


# #--------------------------------   MASK RCNN STUDENT   --------------------------------#

# MODEL_NAME='mask_rcnn_r50_fpn_1x_fskd'
# MODEL_NAME='mask_rcnn_r101_fpn_1x_fskd'
# CUDA_VISIBLE_DEVICES=2,3,4,5 python -m torch.distributed.launch \
#                                 --nproc_per_node=4 \
#                                 --master_port 1027 \
#                                 train.py \
#                                 --config configs/mask_rcnn_kd/coco_${MODEL_NAME}.py \
#                                 --seed 0 \
#                                 --work-dir result/coco/${MODEL_NAME} \
#                                 --launcher pytorch



# #--------------------------------   SPARSE RCNN TEACHER   --------------------------------#
                                # --resume-from result/coco/${MODEL_NAME}/epoch_2.pth  \

# MODEL_NAME='sparse_rcnn_r101_fpn_300_proposals_crop_mstrain_480-800_3x'
# MODEL_NAME='sparse_rcnn_r101_fpn_300_proposals_crop_mstrain_480-800_3x'
MODEL_NAME='sparse_rcnn_r50_fpn_mstrain_480-800_3x'
CUDA_VISIBLE_DEVICES=0,5,6,7 python -m torch.distributed.launch \
                                --nproc_per_node=4 \
                                --master_port 1027 \
                                train.py \
                                --config configs/sparse_rcnn/coco_${MODEL_NAME}.py \
                                --seed 0 \
                                --work-dir result/coco/${MODEL_NAME} \
                                --launcher pytorch

#--------------------------------   SPARSE RCNN STUDENT   --------------------------------#

