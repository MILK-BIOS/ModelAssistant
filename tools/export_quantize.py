# Copyright (c) Seeed Technology Co.,Ltd. All rights reserved.
import argparse
import logging
import os
import os.path as osp
import time

from onnxmltools.utils import load_model, save_model
from onnxmltools.utils.float16_converter import convert_float_to_float16
from onnxruntime.quantization import (
    QuantFormat,
    QuantType,
    quantize_dynamic,
    quantize_static,
)
from utils.quant_read import Quan_Reader


def log_init():
    logger = logging.getLogger('ENV_CONFIG')
    logger.setLevel(logging.INFO)

    hd = logging.StreamHandler()
    hd.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    hd.setFormatter(formatter)
    logger.addHandler(hd)
    return logger


def command(cmd, retry_num=3):
    for i in range(retry_num):
        if os.system(cmd) != 0:
            time.sleep(1)
            logger.warning(f'COMMAND:"{cmd}"execution failed')
            logger.info('retrying') if i != (retry_num - 1) else None
        else:
            return True
    return False


def onnx_quant_static(onnx_path):
    onnx_dir = osp.dirname(onnx_path)
    onnx_name = osp.basename(onnx_path)
    quant_file = osp.join(onnx_dir, onnx_name.replace('.onnx', '_quant_static.onnx'))

    quantize_static(
        onnx_path,
        quant_file,
        quant_format=QuantFormat.QDQ,
        optimize_model=False,
        calibration_data_reader=Quan_Reader('./img_e', (112, 112), 'images'),
        weight_type=QuantType.QInt8,
    )
    logger.info('onnx static succeeded!\nfile in: {}'.format(quant_file))


def onnx_quant_dynamic(onnx_path):
    onnx_dir = osp.dirname(onnx_path)
    onnx_name = osp.basename(onnx_path)
    quant_file = osp.join(onnx_dir, onnx_name.replace('.onnx', '_quant_dynamic.onnx'))
    quantize_dynamic(onnx_path, quant_file, per_channel=True, weight_type=QuantType.QUInt8)
    logger.info('onnx dynamic succeeded!\nfile in: {}'.format(quant_file))


def export_ncnn(onnx_path):
    onnx_dir = osp.dirname(onnx_path)
    onnx_name = osp.basename(onnx_path)
    ncnn_param = osp.join(onnx_dir, onnx_name.replace('.onnx', '.param'))
    ncnn_bin = osp.join(onnx_dir, onnx_name.replace('.onnx', '.bin'))
    if command(f'{onnx2ncnn} {onnx_path} {ncnn_param} {ncnn_bin}'):
        logger.info('ncnn export succeeded!')


def ncnn_quant(onnx_path, image_dir='./img_e', img_size=[112, 112, 3]):
    onnx_dir = osp.dirname(onnx_path)
    onnx_name = osp.basename(onnx_path)
    ncnn_param = osp.join(onnx_dir, onnx_name.replace('.onnx', '.param'))
    ncnn_bin = osp.join(onnx_dir, onnx_name.replace('.onnx', '.bin'))
    ncnn_param_opt = osp.join(onnx_dir, onnx_name.replace('.onnx', '_opt.param'))
    ncnn_bin_opt = osp.join(onnx_dir, onnx_name.replace('.onnx', '_opt.bin'))
    ncnn_table = osp.join(onnx_dir, onnx_name.replace('.onnx', '.table'))
    ncnn_param_int8 = osp.join(onnx_dir, onnx_name.replace('.onnx', '_int8.param'))
    ncnn_bin_int8 = osp.join(onnx_dir, onnx_name.replace('.onnx', '_int8.bin'))

    # check ncnn's .bin and param
    if os.path.exists(ncnn_bin) and os.path.exists(ncnn_param):
        export_ncnn(onnx_path)

    # optimizer model
    if command(f'{ncnnoptimize} {ncnn_param} {ncnn_bin} {ncnn_param_opt} {ncnn_bin_opt} 0'):
        logger.info('export optimizer ncnn succeeded!')
    else:
        logger.warning('export optimizer ncnn fail!')
        return

    # gener calibration datasets
    command(f'find {image_dir} -type f > imagelist.txt')
    cmd = f'{ncnn2table} {ncnn_param_opt} {ncnn_bin_opt} imagelist.txt {ncnn_table} mean=[104,117,123] norm=[0.017,0.017,0.017] shape={img_size} pixel=BGR thread=8 method=kl'

    # gener calibration table
    if command(cmd):
        logger.info('export ncnn quantize table succeeded!')
    else:
        logger.error('export ncnn quantize table fail!')
        return

    if command(
        f'{ncnn2int8} {ncnn_param_opt} {ncnn_bin_opt} {ncnn_param_int8} {ncnn_bin_int8} {ncnn_table}'
    ):  # quantize model
        logger.info('ncnn quantize succeeded!')

    else:
        logger.error('ncnn quantize fail!')
        return


def onnx_fp16(onnx_path):
    onnx_dir = osp.dirname(onnx_path)
    onnx_name = osp.basename(onnx_path)
    onnx_fp16 = osp.join(onnx_dir, onnx_name.replace('.onnx', '_fp16.onnx'))
    onnx_model = load_model(onnx_path)
    fp16_model = convert_float_to_float16(onnx_model)
    save_model(fp16_model, onnx_fp16)
    logger.info('export onnx fp16 format succeeded!')


def ncnn_fp16(onnx_path):
    onnx_dir = osp.dirname(onnx_path)
    onnx_name = osp.basename(onnx_path)
    ncnn_param = osp.join(onnx_dir, onnx_name.replace('.onnx', '.param'))
    ncnn_bin = osp.join(onnx_dir, onnx_name.replace('.onnx', '.bin'))
    ncnn_param_opt = osp.join(onnx_dir, onnx_name.replace('.onnx', '_fp16.param'))
    ncnn_bin_opt = osp.join(onnx_dir, onnx_name.replace('.onnx', '_fp16.bin'))

    # check ncnn's .bin and param
    if os.path.exists(ncnn_bin) and os.path.exists(ncnn_param):
        export_ncnn(onnx_path)

    if command(f'{ncnnoptimize} {ncnn_param} {ncnn_bin} {ncnn_param_opt} {ncnn_bin_opt} 65536'):
        logger.info('export ncnn fp16 format succeeded!')
    else:
        logger.error('export ncnn fp16 format fail!')
        return


def main(args):
    global onnx2ncnn, ncnnoptimize, ncnn2table, ncnn2int8, ncnnmerge, ncnn
    func_dict = {
        'onnx_fp16': onnx_fp16,
        'onnx_quan_st': onnx_quant_static,
        'onnx_quan_dy': onnx_quant_dynamic,
        'ncnn': export_ncnn,
        'ncnn_fp16': ncnn_fp16,
        'ncnn_quan': ncnn_quant,
    }
    home = os.environ['HOME']
    ncnn_dir = f'{home}/software/ncnn/build'
    onnx2ncnn = osp.join(ncnn_dir, 'tools', 'onnx', 'onnx2ncnn')
    ncnnoptimize = osp.join(ncnn_dir, 'tools', 'ncnnoptimize')
    ncnn2table = osp.join(ncnn_dir, 'tools', 'quantize', 'ncnn2table')
    ncnn2int8 = osp.join(ncnn_dir, 'tools', 'quantize', 'ncnn2int8')
    ncnnmerge = osp.join(ncnn_dir, 'tools', 'ncnnmerge')

    onnx_path = onnx_path = osp.abspath(args.onnx)
    export_type = args.type
    imags_dir = args.images

    assert len(export_type), 'At least one export type needs to be selected'

    for f in export_type:
        if f not in func_dict.keys():
            logger.error(f'{f} not in {func_dict.keys()},Please enter the correct export type')
        if f == 'ncnn_quan' and imags_dir:
            func_dict[f](onnx_path, imags_dir)
        else:
            func_dict[f](onnx_path)


def args_parse():
    args = argparse.ArgumentParser(description='export onnx to othaer.')
    args.add_argument('--onnx', default='./weights/best.onnx', help='onnx model file path')
    args.add_argument('--images', help='celacrater data file path')
    args.add_argument(
        '--type',
        nargs='+',
        default=['onnx_quan_dy', 'onnx_quan_st'],
        help='from [onnx_fp16, onnx_quan_st, onnx_quan_dy, ncnn, ncnn_fp16, ncnn_quan]',
    )

    return args.parse_args()


if '__main__' == __name__:
    args = args_parse()
    logger = log_init()
    main(args=args)
