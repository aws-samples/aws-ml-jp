#!/usr/bin/env python3

import aws_cdk as cdk

from chococones.chococones import ChococonesStack
from chococones.logical_id_checker import LogicalIdChecker

PROJECT_NAME = "chococones"

app = cdk.App()
stack = ChococonesStack(
    app,
    "ChococonesStack",
)

# Stack が生成するリソースに共通のタグをつける
cdk.Tags.of(app).add("project", PROJECT_NAME)

# 作成する各リソースに sagemaker という名前がついていないかをチェック(SageMakerFullAccessがついていると操作できるため)
cdk.Aspects.of(stack).add(LogicalIdChecker())

app.synth()
