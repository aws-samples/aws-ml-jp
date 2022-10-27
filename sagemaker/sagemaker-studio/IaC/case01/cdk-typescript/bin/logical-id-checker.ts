import * as cdk from 'aws-cdk-lib'
import { IConstruct } from 'constructs'

const regExp = /sagemaker/i

export class LogicalIdChecker implements cdk.IAspect {
  public visit(node: IConstruct): void {
    // Logical ID に "sagemaker" が含まれていないことをチェック
    if (node instanceof cdk.CfnResource) {
      if (regExp.test(node.logicalId)) {
        cdk.Annotations.of(node).addError('LogicalId contains "sagemaker"')
      }
    }
  }
}
