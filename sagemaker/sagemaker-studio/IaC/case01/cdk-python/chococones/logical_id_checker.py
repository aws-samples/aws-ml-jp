import aws_cdk as cdk
from constructs import IConstruct
import jsii


@jsii.implements(cdk.IAspect)
class LogicalIdChecker:
    def visit(self, node):
        if isinstance(node, cdk.CfnResource):
            print("check")
            print(node.logical_id, type(node.logical_id))
            if "sagemaker" in node.logical_id.lower():
                cdk.Annotations.of(node).add_error('LogicalId contains "sagemaker"')
