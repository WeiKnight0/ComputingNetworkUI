import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Union
import openpyxl


def export_simulation_results(
        json_path: str,
        export_config: Dict[str, Dict[str, bool]],
        output_path: str,
        format: str = 'csv'
) -> None:
    """
    导出仿真结果到CSV或Excel文件

    参数:
        json_path: results.json文件的路径
        export_config: 导出配置字典，指定要导出的指标
            格式示例:
            {
                "globalInfo": {
                    "taskThroughput": True
                },
                "computeNodeInfo": {
                    "averageUtilization": True,
                    "totalAssignedTasks": False,
                    "totalProcessedLoad": True,
                    "energyConsumption": True
                },
                "taskInfo": {
                    "status": True,
                    "endToEndDelay": True,
                    "computationTime": False,
                    "cost": True
                }
            }
        output_path: 输出文件路径
        format: 输出格式，'csv' 或 'excel'
    """
    # 读取JSON文件
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 初始化DataFrame列表
    dfs = []

    # 处理全局指标
    if 'globalInfo' in export_config and data.get('globalInfo'):
        global_metrics = []
        row = {}

        for metric, include in export_config['globalInfo'].items():
            if include and metric in data['globalInfo']:
                row[metric] = data['globalInfo'][metric]['value']
                row[f"{metric}_description"] = data['globalInfo'][metric]['description']

        if row:
            global_metrics.append(row)
            df_global = pd.DataFrame(global_metrics)
            dfs.append(("Global Metrics", df_global))

    # 处理计算节点指标
    if 'computeNodeInfo' in export_config and data.get('computeNodeInfo'):
        compute_node_metrics = []

        for node in data['computeNodeInfo']:
            row = {'computeNodeId': node['computeNodeId']}

            if 'loadBalancingMetrics' in export_config['computeNodeInfo']:
                lb_metrics = export_config['computeNodeInfo']['loadBalancingMetrics']
                if lb_metrics and 'loadBalancingMetrics' in node:
                    for metric, include in lb_metrics.items():
                        if include and metric in node['loadBalancingMetrics']:
                            row[f"lb_{metric}"] = node['loadBalancingMetrics'][metric]['value']
                            row[f"lb_{metric}_description"] = node['loadBalancingMetrics'][metric]['description']

            if 'energyConsumption' in export_config['computeNodeInfo']:
                ec_include = export_config['computeNodeInfo']['energyConsumption']
                if ec_include and 'energyConsumption' in node:
                    row['energyConsumption'] = node['energyConsumption']['value']
                    row['energyConsumption_description'] = node['energyConsumption']['description']

            compute_node_metrics.append(row)

        if compute_node_metrics:
            df_compute = pd.DataFrame(compute_node_metrics)
            dfs.append(("Compute Node Metrics", df_compute))

    # 处理任务指标
    if 'taskInfo' in export_config and data.get('taskInfo'):
        task_metrics = []

        for task in data['taskInfo']:
            row = {
                'taskId': task['taskId'],
                'userNodeId': task['userNodeId'],
                'status': task['status'],
                'computeNodeId': task['computeNodeId']
            }

            if 'status' in export_config['taskInfo']:
                if not export_config['taskInfo']['status']:
                    del row['status']

            if 'delayDistribution' in export_config['taskInfo'] and task['delayDistribution']:
                dd_metrics = export_config['taskInfo']['delayDistribution']
                if dd_metrics:
                    for metric, include in dd_metrics.items():
                        if include and metric in task['delayDistribution']:
                            row[f"delay_{metric}"] = task['delayDistribution'][metric]['value']
                            row[f"delay_{metric}_description"] = task['delayDistribution'][metric]['description']

            if 'cost' in export_config['taskInfo']:
                cost_include = export_config['taskInfo']['cost']
                if cost_include and 'cost' in task:
                    row['cost'] = task['cost']['value']
                    row['cost_description'] = task['cost']['description']

            task_metrics.append(row)

        if task_metrics:
            df_task = pd.DataFrame(task_metrics)
            dfs.append(("Task Metrics", df_task))

    # 导出到文件
    if format.lower() == 'csv':
        # 对于CSV，将所有数据合并到一个文件中，用不同的sheet名称作为注释
        with open(output_path, 'w', encoding='utf-8') as f:
            for sheet_name, df in dfs:
                f.write(f"# {sheet_name}\n")
                df.to_csv(f, index=False)
                f.write("\n\n")
        print(f"结果已成功导出到 {output_path}")
    elif format.lower() == 'excel':
        # 对于Excel，使用不同的sheet
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, df in dfs:
                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        print(f"结果已成功导出到 {output_path}")
    else:
        raise ValueError("不支持的格式，请选择 'csv' 或 'excel'")


# 示例使用
if __name__ == "__main__":
    # 示例导出配置
    example_export_config = {
        "globalInfo": {
            "taskThroughput": True
        },
        "computeNodeInfo": {
            "loadBalancingMetrics": {
                "averageUtilization": True,
                "totalAssignedTasks": False,
                "totalProcessedLoad": True
            },
            "energyConsumption": True
        },
        "taskInfo": {
            "status": True,
            "delayDistribution": {
                "endToEndDelay": True,
                "computationTime": False
            },
            "cost": True
        }
    }

    # 示例JSON文件路径 (假设当前目录下有results.json)
    example_json_path = "results.json"

    # 示例输出路径
    example_output_csv = "simulation_results.csv"
    example_output_excel = "simulation_results.xlsx"

    # 执行导出 (CSV示例)
    try:
        export_simulation_results(
            json_path=example_json_path,
            export_config=example_export_config,
            output_path=example_output_csv,
            format='csv'
        )
    except Exception as e:
        print(f"导出CSV时出错: {e}")

    # 执行导出 (Excel示例)
    try:
        export_simulation_results(
            json_path=example_json_path,
            export_config=example_export_config,
            output_path=example_output_excel,
            format='excel'
        )
    except Exception as e:
        print(f"导出Excel时出错: {e}")