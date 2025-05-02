import aws_cdk as core
import aws_cdk.assertions as assertions

from stacks.app_layer_stack import AppLayerStack

# example tests. To run these tests, uncomment this file along with the example
# resource in stacks/app_layer_stack.py
def test_lambda_function_created():
    app = core.App()
    stack = AppLayerStack(app, "SampleAppLayerStack")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::Lambda::Function", {
#         "Timeout": 30
#     })
