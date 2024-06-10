from engine import execute_workflow
import json
import uiautomator2 as u2
from validate import validate_json_with_schema
from workflow_schema import workflow_schema
import logging 


if __name__=="__main__":
    # 示例：加载 JSON 文件并执行工作流
    with open('./temp.json', encoding='utf-8') as f:
        workflow=json.load(f)
        is_valid,err =validate_json_with_schema(f, workflow_schema)
        if is_valid:
            logging.error("JSON is valid according to schema.")
            exit(0)
    device = u2.connect()  # 请替换为实际设备IP或序列号
    execute_workflow(workflow, device)
