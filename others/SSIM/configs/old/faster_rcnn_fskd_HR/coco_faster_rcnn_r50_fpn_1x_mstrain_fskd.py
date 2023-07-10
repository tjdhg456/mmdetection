_base_ = ['../faster_rcnn/coco_faster_rcnn_r50_fpn_1x_mstrain.py']


# model
model = dict(type='FasterRCNN_TS',
             distill_name='F_SKD',
             distill_param=1.5,
             distill_param_backbone=1.5,
             roi_head=dict(
                 type='ContRoIHead'
                ),
            )


# Distillation Params
teacher_config_path = 'result/coco/HR_TEACHER/faster_rcnn_r50_fpn_1x_mstrain/coco_faster_rcnn_r50_fpn_1x_mstrain.py'
teacher_weight_path = 'result/coco/HR_TEACHER/faster_rcnn_r50_fpn_1x_mstrain/epoch_12.pth'
backbone_pretrain = False


# Pytorch
img_norm_cfg = dict(
    mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True)


pre_train_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations', with_bbox=True),
    dict(type='RandomFlip', flip_ratio=0.5),
]

train_pipeline = [
    dict(type='Resize',
        img_scale=[(1333, 640), (1333, 672), (1333, 704), (1333, 736),
                   (1333, 768), (1333, 800)],
        multiscale_mode='value',
        keep_ratio=True),
    dict(type='Normalize', **img_norm_cfg),
    dict(type='Pad', size_divisor=32),
    dict(type='DefaultFormatBundle'),
    dict(type='Collect', keys=['img', 'gt_bboxes', 'gt_labels']),
]


# Use RepeatDataset to speed up training
data = dict(
    samples_per_gpu=2,
    workers_per_gpu=2,
    train=dict(type="CocoHRContDataset",
               pipeline=train_pipeline,
               pre_pipeline=pre_train_pipeline
               )
    )