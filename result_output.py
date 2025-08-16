import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Union, Optional
import openpyxl


def export_simulation_results(
        json_path: str,
        export_config: Dict[str, Union[bool, Dict]],
        output_path: str
) -> None:
    """
    导出仿真结果到CSV或Excel文件

    参数:
        json_path: results.json文件的路径
        export_config: 导出配置字典，指定要导出的指标
            格式示例:
            {
                "globalInfo": True,
                "computeNodeInfo": {
                    "enabled": True,
                    "metrics": {
                        "loadBalancingMetrics": ["averageUtilization", "totalAssignedTasks"],
                        "energyConsumption": True
                    }
                },
                "taskInfo": {
                    "enabled": True,
                    "metrics": {
                        "delayDistribution": ["endToEndDelay", "computationTime"],
                        "cost": True
                    }
                }
            }
        output_path: 输出文件路径
    """
    # 读取JSON文件
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 初始化DataFrame列表
    dfs = []

    # 处理全局指标
    if export_config.get("globalInfo", False) and data.get('globalInfo'):
        global_metrics = []
        row = {}

        global_info = data['globalInfo']
        if isinstance(global_info, dict):
            for metric, metric_data in global_info.items():
                if isinstance(metric_data, dict):
                    row[metric] = metric_data.get('value', '')
                    row[f"{metric}_description"] = metric_data.get('description', '')

        if row:
            global_metrics.append(row)
            df_global = pd.DataFrame(global_metrics)
            dfs.append(("Global Metrics", df_global))

    # 处理计算节点指标
    node_config = export_config.get("computeNodeInfo", {})
    if isinstance(node_config, dict) and node_config.get("enabled", False) and data.get('computeNodeInfo'):
        compute_node_metrics = []
        lb_metrics = node_config.get("metrics", {}).get("loadBalancingMetrics", [])
        ec_enabled = node_config.get("metrics", {}).get("energyConsumption", False)

        nodes_info = data['computeNodeInfo']
        if isinstance(nodes_info, list):
            for node in nodes_info:
                if not isinstance(node, dict):
                    continue

                row = {'computeNodeId': node.get('computeNodeId', '')}

                # 处理负载均衡指标
                if lb_metrics and isinstance(lb_metrics, list) and 'loadBalancingMetrics' in node:
                    lb_data = node['loadBalancingMetrics']
                    if isinstance(lb_data, dict):
                        for metric in lb_metrics:
                            if metric in lb_data:
                                metric_data = lb_data[metric]
                                if isinstance(metric_data, dict):
                                    row[f"lb_{metric}"] = metric_data.get('value', '')
                                    row[f"lb_{metric}_description"] = metric_data.get('description', '')

                # 处理能耗指标
                if ec_enabled and 'energyConsumption' in node:
                    ec_data = node['energyConsumption']
                    if isinstance(ec_data, dict):
                        row['energyConsumption'] = ec_data.get('value', '')
                        row['energyConsumption_description'] = ec_data.get('description', '')

                compute_node_metrics.append(row)

        if compute_node_metrics:
            df_compute = pd.DataFrame(compute_node_metrics)
            dfs.append(("Compute Node Metrics", df_compute))

    # 处理任务指标
    task_config = export_config.get("taskInfo", {})
    if isinstance(task_config, dict) and task_config.get("enabled", False) and data.get('taskInfo'):
        task_metrics = []
        dd_metrics = task_config.get("metrics", {}).get("delayDistribution", [])
        cost_enabled = task_config.get("metrics", {}).get("cost", False)

        tasks_info = data['taskInfo']
        if isinstance(tasks_info, list):
            for task in tasks_info:
                if not isinstance(task, dict):
                    continue

                row = {
                    'taskId': task.get('taskId', ''),
                    'userNodeId': task.get('userNodeId', ''),
                    'status': task.get('status', ''),
                    'computeNodeId': task.get('computeNodeId', '')
                }

                # 处理延迟分布指标
                if dd_metrics and isinstance(dd_metrics, list) and 'delayDistribution' in task:
                    dd_data = task['delayDistribution']
                    if isinstance(dd_data, dict):
                        for metric in dd_metrics:
                            if metric in dd_data:
                                metric_data = dd_data[metric]
                                if isinstance(metric_data, dict):
                                    row[f"delay_{metric}"] = metric_data.get('value', '')
                                    row[f"delay_{metric}_description"] = metric_data.get('description', '')

                # 处理成本指标
                if cost_enabled and 'cost' in task:
                    cost_data = task['cost']
                    if isinstance(cost_data, dict):
                        row['cost'] = cost_data.get('value', '')
                        row['cost_description'] = cost_data.get('description', '')

                task_metrics.append(row)

        if task_metrics:
            df_task = pd.DataFrame(task_metrics)
            dfs.append(("Task Metrics", df_task))

    # 根据文件扩展名确定输出格式
    file_ext = Path(output_path).suffix.lower()

    if not dfs:
        raise ValueError("没有可导出的数据，请检查导出配置和JSON数据")

    try:
        if file_ext == '.csv':
            # 对于CSV，将所有数据合并到一个文件中，用不同的sheet名称作为注释
            with open(output_path, 'w', encoding='utf-8') as f:
                for sheet_name, df in dfs:
                    f.write(f"# {sheet_name}\n")
                    df.to_csv(f, index=False)
                    f.write("\n\n")
        elif file_ext in ('.xlsx', '.xls'):
            # 对于Excel，使用不同的sheet
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for sheet_name, df in dfs:
                    df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        else:
            raise ValueError("不支持的格式，请使用 .csv 或 .xlsx 文件扩展名")
    except Exception as e:
        raise ValueError(f"导出文件时出错: {str(e)}")


# 示例使用
if __name__ == "__main__":
    # 示例导出配置 (匹配SimulationExportDialog的输出格式)
    example_export_config = {
        "globalInfo": True,
        "computeNodeInfo": {
            "enabled": True,
            "metrics": {
                "loadBalancingMetrics": ["averageUtilization", "totalAssignedTasks", "totalProcessedLoad"],
                "energyConsumption": True
            }
        },
        "taskInfo": {
            "enabled": True,
            "metrics": {
                "delayDistribution": ["endToEndDelay", "computationTime"],
                "cost": True
            }
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
            output_path=example_output_csv
        )
        print(f"结果已成功导出到 {example_output_csv}")
    except Exception as e:
        print(f"导出CSV时出错: {e}")

    # 执行导出 (Excel示例)
    try:
        export_simulation_results(
            json_path=example_json_path,
            export_config=example_export_config,
            output_path=example_output_excel
        )
        print(f"结果已成功导出到 {example_output_excel}")
    except Exception as e:
        print(f"导出Excel时出错: {e}")