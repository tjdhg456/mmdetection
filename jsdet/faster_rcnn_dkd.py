from mmdet.models.builder import DETECTORS
from mmdet.models.detectors.two_stage import TwoStageDetector
#from mmdet.registry import MODELS
import torch
import torch.nn.functional as F
from mmdet.models import build_detector
import copy
import numpy as np
from mmdet.core import bbox2roi
from .kd_trans import build_kd_trans, hcl
#from .mdistiller.distillers.DKD import dkd_loss


@DETECTORS.register_module()
class FasterRCNN_DKDreviewkd(TwoStageDetector):
    """Implementation of `Faster R-CNN <https://arxiv.org/abs/1506.01497>`_"""
    def __init__(self,
                 backbone,
                 rpn_head,
                 roi_head,
                 train_cfg,
                 test_cfg,
                 teacher_cfg,
                 neck=None,
                 pretrained=None,
                 init_cfg=None):
        super(FasterRCNN_DKDreviewkd, self).__init__(
            backbone=backbone,
            neck=neck,
            rpn_head=rpn_head,
            roi_head=roi_head,
            train_cfg=train_cfg,
            test_cfg=test_cfg,
            pretrained=pretrained,
            init_cfg=init_cfg)

        teacher_cfg.model.type = 'FasterRCNNCont'
        teacher_cfg.model.roi_head.type = 'ContRoIHead'
        self.teacher_cfg = teacher_cfg
        #self.dkd_loss = dkd_loss
        self.kd_trans = build_kd_trans(train_cfg)
        self.hcl = hcl

    def _kl_loss(self, preds_S,preds_T):
        """Calculate the KL Divergence."""
        kl_loss = F.kl_div(
            preds_S, preds_T, size_average=False,
            reduction='batchmean') * 1.0**2
        return kl_loss
    
    def _cat_mask(self,tckd, gt_mask, non_gt_mask):
        """Calculate preds of target (pt) & preds of non-target (pnt)."""
        t1 = (tckd * gt_mask).sum(dim=1, keepdims=True)
        t2 = (tckd * non_gt_mask).sum(dim=1, keepdims=True)
        return torch.cat([t1, t2], dim=1)
    
    def _get_nckd_loss(self, preds_S, preds_T, gt_mask):
        """Calculate non-target class knowledge distillation."""
        # implementation to mask out gt_mask, faster than index
        s_nckd = F.log_softmax(preds_S / 1.0 - 1000.0 * gt_mask, dim=1)
        t_nckd = F.softmax(preds_T / 1.0 - 1000.0 * gt_mask, dim=1)
        return self._kl_loss(s_nckd, t_nckd)
    
    def _get_tckd_loss(self, preds_S, preds_T, gt_labels, gt_mask):
        """Calculate target class knowledge distillation."""
        non_gt_mask = self._get_non_gt_mask(preds_S, gt_labels)
        s_tckd = F.softmax(preds_S / 1.0, dim=1)
        t_tckd = F.softmax(preds_T / 1.0, dim=1)
        mask_student = torch.log(self._cat_mask(s_tckd, gt_mask, non_gt_mask)+1e-6)
        mask_teacher = self._cat_mask(t_tckd, gt_mask, non_gt_mask)
        return self._kl_loss(mask_student, mask_teacher)

    def dkd_loss(self, logits_student, logits_teacher, target, alpha, beta, temperature):
        gt_mask = self._get_gt_mask(logits_student, target)
        tckd_loss = self._get_tckd_loss(logits_student, logits_teacher, target, gt_mask)
        nckd_loss = self._get_nckd_loss(logits_student, logits_teacher, gt_mask)
        loss = alpha * tckd_loss + beta * nckd_loss
        return loss

    def _get_gt_mask(self, logits, target):
        """Calculate groundtruth mask on logits with target class tensor.

        Args:
            logits (torch.Tensor): The prediction logits with shape (N, C).
            target (torch.Tensor): The gt_label target with shape (N, C).

        Return:
            torch.Tensor: The masked logits.
        """
        target = target.reshape(-1)
        return torch.zeros_like(logits).scatter_(1, target.unsqueeze(1),
                                                 1).bool()
    def _get_non_gt_mask(self, logits,target):

        """Calculate non-groundtruth mask on logits with target class tensor.

        Args:
            logits (torch.Tensor): The prediction logits with shape (N, C).
            target (torch.Tensor): The gt_label target with shape (N, C).

        Return:
            torch.Tensor: The masked logits.
        """
        target = target.reshape(-1)
        return torch.ones_like(logits).scatter_(1, target.unsqueeze(1),
                                                0).bool()

    
    def update_teacher(self, state_dict): 
        # Load Teacher Model
        self.teacher = build_detector(self.teacher_cfg.model,
                                      train_cfg=None,
                                      test_cfg=None)
        
        # Load Pretrained Teacher Weights
        self.teacher.load_state_dict(state_dict, strict=True)
        
        # Freeze Param
        for param in self.teacher.parameters():
            param.requires_grad = False

    def forward_student_roi_head(self, roi_head, features, proposals, gt_bboxes, gt_labels, img_metas):

        roi_losses, gt_bboxes_feats, bbox_results = self.roi_head.forward_train(features, img_metas, proposals,
                                                 gt_bboxes, gt_labels)
        predictions = bbox_results['cls_score']
        
        return predictions
    
    def forward_teacher_roi_head(self, roi_head, features, proposals, gt_bboxes, gt_labels, img_metas):

        roi_losses, gt_bboxes_feats, bbox_results = self.teacher.roi_head.forward_train(features, img_metas, proposals,
                                                 gt_bboxes, gt_labels)
        predictions = bbox_results['cls_score']
        
        return predictions
    
    def extract_feat(self, img):
        """Directly extract features from the backbone+neck."""
        x = self.backbone(img)
        #feas_stu = [list(x)[0], list(x)[1], list(x)[2], list(x)[3]]
        
        if self.with_neck:
            x = self.neck(x)

        return x#, feas_stu

    
    def forward_train(self,
                      img,
                      img_metas,
                      gt_bboxes,
                      gt_labels,
                      gt_bboxes_ignore=None,
                      gt_masks=None,
                      proposals=None,
                      **kwargs):
        """
        Args:
            img (Tensor): of shape (N, C, H, W) encoding input images.
                Typically these should be mean centered and std scaled.

            img_metas (list[dict]): list of image info dict where each dict
                has: 'img_shape', 'scale_factor', 'flip', and may also contain
                'filename', 'ori_shape', 'pad_shape', and 'img_norm_cfg'.
                For details on the values of these keys see
                `mmdet/datasets/pipelines/formatting.py:Collect`.

            gt_bboxes (list[Tensor]): Ground truth bboxes for each image with
                shape (num_gts, 4) in [tl_x, tl_y, br_x, br_y] format.

            gt_labels (list[Tensor]): class indices corresponding to each box

            gt_bboxes_ignore (None | list[Tensor]): specify which bounding
                boxes can be ignored when computing the loss.

            gt_masks (None | Tensor) : true segmentation masks for each box
                used if the architecture supports a segmentation task.

            proposals : override rpn proposals with custom proposals. Use when
                `with_rpn` is False.

        Returns:
            dict[str, Tensor]: a dictionary of loss components
        """
        x = self.extract_feat(img)

        losses = dict()

        # RPN forward and loss
        if self.with_rpn:
            proposal_cfg = self.train_cfg.get('rpn_proposal',
                                              self.test_cfg.rpn)
            rpn_losses, proposal_list = self.rpn_head.forward_train(
                x,
                img_metas,
                gt_bboxes,
                gt_labels=None,
                gt_bboxes_ignore=gt_bboxes_ignore,
                proposal_cfg=proposal_cfg,
                **kwargs)
            losses.update(rpn_losses)
        else:
            proposal_list = proposals

        roi_losses, gt_bboxes_feats, bbox_results = self.roi_head.forward_train(x, img_metas, proposal_list,
                                                 gt_bboxes, gt_labels,
                                                 gt_bboxes_ignore, gt_masks,
                                                 **kwargs)
        losses.update(roi_losses)


        return losses, gt_bboxes_feats, x, proposal_list, gt_bboxes, gt_labels, img_metas
    
    def train_step(self, data, optimizer):
        """The iteration step during training.

        This method defines an iteration step during training, except for the
        back propagation and optimizer updating, which are done in an optimizer
        hook. Note that in some complicated cases or models, the whole process
        including back propagation and optimizer updating is also defined in
        this method, such as GAN.

        Args:
            data (dict): The output of dataloader.
            optimizer (:obj:`torch.optim.Optimizer` | dict): The optimizer of
                runner is passed to ``train_step()``. This argument is unused
                and reserved.

        Returns:
            dict: It should contain at least 3 keys: ``loss``, ``log_vars``, \
                ``num_samples``.

                - ``loss`` is a tensor for back propagation, which can be a
                  weighted sum of multiple losses.
                - ``log_vars`` contains all the variables to be sent to the
                  logger.
                - ``num_samples`` indicates the batch size (when the model is
                  DDP, it means the batch size on each GPU), which is used for
                  averaging the logs.
        """
        self.teacher.eval()

        losses, gt_feats_down, backbone_down, sampled_proposals, gt_bboxes, gt_labels, img_metas = self(**data[0])

        with torch.no_grad():
            _, _, backbone_teacher_down = self.teacher(**data[0])
            #_, gt_feats_crop, backbone_crop = self.teacher(**data[1])
        #####################################dkd review######################################
        stu_predictions = self.forward_student_roi_head(self.roi_head, backbone_down, sampled_proposals, gt_bboxes, gt_labels, img_metas)
        tea_predictions = self.forward_teacher_roi_head(self.teacher.roi_head, backbone_teacher_down, sampled_proposals, gt_bboxes, gt_labels, img_metas)
        gt_labels = torch.cat(tuple(gt_labels), 0).reshape(-1)
        dkd_loss = self.dkd_loss(stu_predictions, tea_predictions, gt_labels, 1.0, 1.0, 1.0)
        losses.update({'dkd_loss': dkd_loss})
        #print("dkd_loss_tckd", tckd_loss)
        #print("dkd_loss_nckd", nckd_loss)
        
        backbone_down = self.kd_trans(backbone_down)
        loss_mkdr = self.hcl(backbone_down, backbone_teacher_down) * 1.0
        losses.update({'reviewkd_loss': loss_mkdr})
        #print('reviewkd_loss', loss_mkdr)
        #####################################################################################
        
        loss, log_vars = self._parse_losses(losses)
        
        outputs = dict(
            loss=loss, log_vars=log_vars, num_samples=len(data[0]['img_metas']))

        return outputs

    def simple_test(self, img, img_metas, proposals=None, rescale=False):
        """Test without augmentation."""

        assert self.with_bbox, 'Bbox head must be implemented.'
        x  = self.extract_feat(img)
        if proposals is None:
            proposal_list = self.rpn_head.simple_test_rpn(x, img_metas)
        else:
            proposal_list = proposals

        return self.roi_head.simple_test(
            x, proposal_list, img_metas, rescale=rescale)
    

