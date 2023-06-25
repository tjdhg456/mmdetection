_base_ = [
    '../_base_/models/faster_rcnn_r50_fpn.py',
    '../_base_/datasets/coco_detection.py',
    '../_base_/schedules/schedule_1x.py', '../_base_/default_runtime.py'
]

# model
model = dict(type='FasterRCNN_SelfTeacher',
             distill_param_backbone=1.0,
             distill_param=1.0,
             roi_head=dict(type='ContRoIHead')
            )

img_norm_cfg = dict(
    mean=[123.675, 116.28, 103.53], std=[58.395, 57.12, 57.375], to_rgb=True)

pre_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations', with_bbox=True),
    dict(type='Resize', img_scale=(1333, 800), keep_ratio=True),
    dict(type='RandomFlip', flip_ratio=0.5)
]

crop_pipeline = [
    dict(type='DistillCrop',
        crop_size=(0.5, 0.5),
        allow_negative_crop=True),
    dict(type='Resize', img_scale=(1333, 800), override=True, keep_ratio=True),
    dict(type='Normalize', **img_norm_cfg),
    dict(type='Pad', size_divisor=32),
    dict(type='DefaultFormatBundle'),
    dict(type='Collect', keys=['img', 'gt_bboxes', 'gt_labels', 'crop_valid_inds', 'crop_loc']),
]

train_pipeline = [                        
    dict(type='Normalize', **img_norm_cfg),
    dict(type='Pad', size_divisor=32),
    dict(type='DefaultFormatBundle'),
    dict(type='Collect', keys=['img', 'gt_bboxes', 'gt_labels']),
]


data = dict(
    samples_per_gpu=4,
    workers_per_gpu=4,
    train=dict(
        type="CocoCropDataset",
        pre_pipeline=pre_pipeline,
        crop_pipeline=crop_pipeline,
        pipeline=train_pipeline),
    )

# optimizer
optimizer = dict(type='SGD', lr=0.02, momentum=0.9, weight_decay=0.0001)