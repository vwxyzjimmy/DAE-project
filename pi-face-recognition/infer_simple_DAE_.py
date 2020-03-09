# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
##############################################################################

"""Perform inference on a single image or all images with a certain extension
(e.g., .jpg) in a folder.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import defaultdict
import argparse
import cv2  # NOQA (Must import before importing caffe2 due to bug in cv2)
import glob
import logging
import os
import sys
import time
import socket

from caffe2.python import workspace

from detectron.core.config import assert_and_infer_cfg
from detectron.core.config import cfg
from detectron.core.config import merge_cfg_from_file
from detectron.utils.io import cache_url
from detectron.utils.logging import setup_logging
from detectron.utils.timer import Timer
import detectron.core.test_engine as infer_engine
import detectron.datasets.dummy_datasets as dummy_datasets
import detectron.utils.c2 as c2_utils
import detectron.utils.vis as vis_utils
import matplotlib.pyplot as plt

c2_utils.import_detectron_ops()

# OpenCL may be enabled by default in OpenCV3; disable it because it's not
# thread safe and causes unwanted GPU memory allocations.
cv2.ocl.setUseOpenCL(False)

def parse_args():
    parser = argparse.ArgumentParser(description='End-to-end inference')
    parser.add_argument(
        '--cfg',
        dest='cfg',
        help='cfg model file (/path/to/model_config.yaml)',
        default=None,
        type=str
    )
    parser.add_argument(
        '--wts',
        dest='weights',
        help='weights model file (/path/to/model_weights.pkl)',
        default=None,
        type=str
    )
    parser.add_argument(
        '--output-dir',
        dest='output_dir',
        help='directory for visualization pdfs (default: /tmp/infer_simple)',
        default='/tmp/infer_simple',
        type=str
    )
    parser.add_argument(
        '--image-ext',
        dest='image_ext',
        help='image file name extension (default: jpg)',
        default='jpg',
        type=str
    )
    parser.add_argument(
        'im_or_folder', help='image or folder of images', default=None
    )
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    return parser.parse_args()


def main(args):
    global dot_count
    dot_count = 0
    logger = logging.getLogger(__name__)
    merge_cfg_from_file(args.cfg)
    cfg.NUM_GPUS = 1
    args.weights = cache_url(args.weights, cfg.DOWNLOAD_CACHE)
    assert_and_infer_cfg(cache_urls=False)
    model = infer_engine.initialize_model_from_cfg(args.weights)
    dummy_coco_dataset = dummy_datasets.get_coco_dataset()

    if os.path.isdir(args.im_or_folder):
        im_list = glob.iglob(args.im_or_folder + '/*.' + args.image_ext)
    else:
        im_list = [args.im_or_folder]

    host = '127.0.0.1'
    port = 9998
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(5)
    s.settimeout(2)
    SIZE = 4096
    #s.settimeout(10)
    multiTracker = cv2.MultiTracker_create()
    while True:
        try:
            sock, addr = s.accept()
            receive = sock.recv(SIZE).decode()
            tmp = str(receive).split("|")
            path = tmp[0]
            device_addr = tmp[1]
            print("path: {0}, device_addr: {1}".format(path, device_addr))
            im_list = []
            im_list.append(path)
            for i, im_name in enumerate(im_list):
                out_name = os.path.join(
                    args.output_dir, '{}'.format(os.path.basename(im_name))
                )
                logger.info('Processing {} -> {}'.format(im_name, out_name))
                im = cv2.imread(im_name)
                timers = defaultdict(Timer)
                t = time.time()
                with c2_utils.NamedCudaScope(0):
                    cls_boxes, cls_segms, cls_keyps, cls_bodys = infer_engine.im_detect_all(
                        model, im, None, timers=timers
                    )
                logger.info('Inference time: {:.3f}s'.format(time.time() - t))
                for k, v in timers.items():
                    logger.info(' | {}: {:.3f}s'.format(k, v.average_time))
                if i == 0:
                    logger.info(
                        ' \ Note: inference on the first image will be slower than the '
                        'rest (caches and auto-tuning need to warm up)'
                    )

                vis_utils.vis_one_image(
                    im[:, :, ::-1],  # BGR -> RGB for visualization
                    im_name,
                    args.output_dir,
                    cls_boxes,
                    cls_segms,
                    cls_keyps,
                    cls_bodys,
                    dataset=dummy_coco_dataset,
                    box_alpha=0.3,
                    show_class=True,
                    thresh=0.8,
                    kp_thresh =2
                )

                print("len(cls_boxes[1])-1: {0}".format(len(cls_boxes[1])-1))
                count_people = 0
                now_boxes = []
                now_center = []
                try:
                    for i in range(len(cls_boxes[1])):
                        if cls_boxes[1][i][4] > 0.8:
                            now_boxes.append(cls_boxes[1][i][:4])
                            now_center.append([int((cls_boxes[1][i][0] + cls_boxes[1][i][2])//2), int((cls_boxes[1][i][1] + cls_boxes[1][i][3])//2)])
                            count_people = count_people + 1
                except:
                    count_people = 0
                print("now_center: {0}".format(now_center))
                print("count_people: {0}".format(count_people))
                ans_command = str(count_people) + " "
                for i in range(int(count_people)):
                    ans_command = ans_command + str(now_center[i][0]) + "," + str(now_center[i][1]) + ","
                ans_command = ans_command.strip(",")
                print(ans_command)
                sock.send(ans_command.encode())
                im_name = ""
        except Exception as e:
            print('                                                 ', end='\r')
            error_text = "Exception: " + str(e) + ", reconnecting "
            for i in range(dot_count):
            	error_text = error_text + "."
            dot_count = dot_count + 1
            if dot_count > 3:
            	dot_count = 0
            print(error_text, end='\r')
    s.close()


if __name__ == '__main__':
    workspace.GlobalInit(['caffe2', '--caffe2_log_level=0'])
    setup_logging(__name__)
    args = parse_args()
    main(args)
