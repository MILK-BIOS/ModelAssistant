# Meter Reader with Grove - Vision AI

This tutorial will demonstrate the development process of meter reader using EdgeLab based on Grove - Vision AI module.

::: tip

Before starting, we recommend that you should read [Grove - Deploy](./deploy.md) first.

:::


## Preparation

Please refer to [Grove - Deploy - Prerequisites](./deploy.md#prerequisites).


## Train Model

The meter reading feature is based on the PFLD model, in this step you need a PFLD model weight with the suffix `.pth`, you have two ways to get the model weight.

- Download the pre-trained model from our [Model Zoo](https://github.com/Seeed-Studio/EdgeLab/releases).

- Refer to [Training - PFLD Models](../../tutorials/training/pfld.md) to train the PFLD model and get the model weights using PyTorch and EdgeLab by yourself.


## Export Model

Since the trained model is not suitable for running directly on edge computing devices, we need to export it to a TFLite format with a `.tflite` suffix, and you have two ways to get the exported model (with model weights contained).

- Download the exported TFLite model from our [Model Zoo](https://github.com/Seeed-Studio/EdgeLab/releases).

- Refer to [Export - PyTorch to TFLite](../../tutorials/export/pytorch_2_tflite.md) to convert the PFLD model from PyTorch format to TFLite format by yourself.


## Deploy Model

This is the last and most important step to complete the meter reading, in this step you need to compile and flash the firmware to the Grove - Vision AI modules. Please refer to [Grove - Deployment - Compile and Deploy](./deploy.md#compile-and-deploy) to complete the deployment of the model.


## Run Example

After completing the [Grove - Deployment Tutorial - Compile and Deploy - Deployment Routines](./deploy.md#deployment-routines), you need to do a manual calibration in the [Grove Vision AI Console](https://files.seeedstudio.com/grove_ai_vision/index.html) to get the correct meter readings, which is mainly divided into three steps:

1. Set 3 points: center point, start point and end point.

2. Set the first and last digit of the dial to set the measurement range.

3. Configure the number of decimal places.

The above steps are graphically indicated in the console, and finally, you can see the real-time dial reading results as shown in the figure below.

![PFLD Meter Reader](/static/grove/images/pfld_meter.gif)