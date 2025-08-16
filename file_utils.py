import os
import json
import pathlib
import pickle
from typing import Dict, Any, List, Union
from io import TextIOWrapper
import weakref

from allTypeItem import *
from channel import Channel


ROUTERTYPE = ["Router", "ComputingGateway", "UserGateway"]
EDGETYPE = ["ComputingNode", "ComputeScheduleNode", "UserNode"]

def get_node_en_name(node) -> str:
    return f"{node.nodetype}{node.index}"


def write_network_topology(nodes_list: List[Union[UserGateway, ComputingGateway]],
                           project_dir:str):
    user_gateways = [node for node in nodes_list if isinstance(node, UserGateway)]
    computing_gateways = [node for node in nodes_list if isinstance(node, ComputingGateway)]

    topology = {
        "userGateways": [],
        "computeGateways": []
    }

    # Process user gateways and their user nodes
    for gateway in user_gateways:
        user_nodes = []
        for channel in gateway.channelList:
            another_node = channel.another_point_of_channel(gateway)
            if isinstance(another_node, UserNode):
                user_nodes.append({
                    "nodeId": another_node.index,
                    "nodeIp": another_node.ip
                })

        gateway_info = {
            "gatewayId": gateway.index,
            "gatewayIp": list(gateway.ip_dict.values())[0],
            "userNodes": user_nodes
        }
        topology["userGateways"].append(gateway_info)

    # Process computing gateways and their compute nodes
    for gateway in computing_gateways:
        compute_nodes = []
        for channel in gateway.channelList:
            another_node = channel.another_point_of_channel(gateway)
            if isinstance(another_node, ComputingNode):
                compute_nodes.append({
                    "nodeId": another_node.index,
                    "nodeIp": another_node.ip
                })

        gateway_info = {
            "gatewayId": gateway.index,
            "gatewayIp": list(gateway.ip_dict.values())[0],
            "computeNodes": compute_nodes
        }
        topology["computeGateways"].append(gateway_info)

    with open(os.path.join(project_dir,'network_topology.json'), 'w') as f:
        json.dump(topology, f, indent=2)



class TaskWriter:
    def __init__(self, node_list:List[UserNode], project_dir:Union[str,pathlib.Path]):
        self.nodes = [node for node in node_list if isinstance(node, UserNode)]
        self.project_dir = str(project_dir)
        if project_dir and os.path.exists(project_dir):
            pass
        else:
            raise ValueError("错误的项目地址")

    def write(self):
        for node in self.nodes:
            self.save_tasks_to_json(node, self.project_dir)

    def save_tasks_to_json(self, node:UserNode, project_dir:Union[str,pathlib.Path]):
        """
        将Node的task_queue保存为JSON文件

        参数:
            node: 用户节点对象，包含task_queue和index属性
            project_dir: 项目根目录路径
        """
        # 准备要保存的数据列表
        tasks_data = []

        for task in node.task_queue:
            task_data = {
                "taskId": task["任务编号"],
                "userNodeId": task["所属用户节点编号"],
                "generationTime": task["任务产生的时刻"],
                "computingType": task["所需算力类型"],
                "requiredStorage": task["任务所需存储空间"],
                "computingAmount": task["任务计算量"],
                "transferAmount": task["任务传输量"],
                "maxDelay": task["最大时延要求"],
                "budget": task["预算"]
            }
            tasks_data.append(task_data)

        # 创建目录（如果不存在）
        output_dir = os.path.join(project_dir, "task_requirements")
        os.makedirs(output_dir, exist_ok=True)

        # 构建文件路径
        filename = f"tasks_user_{node.index}.json"
        filepath = os.path.join(output_dir, filename)

        # 写入JSON文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(tasks_data, f, indent=2, ensure_ascii=False)

        # print(f"任务数据已保存到: {filepath}")

class NEDWriter:
    def __init__(self, filename: str, nodeList: list, channelList: list, project_name:str):
        self.filename = filename
        self.nodeList = nodeList
        self.channelList = channelList
        # 用户节点列表
        self.user_nodes = [node for node in nodeList if node.nodetype == "UserNode"]
        # 算力节点列表
        self.compute_nodes = [node for node in nodeList if node.nodetype == "ComputingNode"]
        # 用户网关列表
        self.user_gateways = [node for node in nodeList if node.nodetype == "UserGateway"]
        # 算力网关列表
        self.computing_gateways = [
            node for node in nodeList if node.nodetype == "ComputingGateway"
        ]
        # 调度决策网关列表
        self.compute_schedule_nodes = [
            node for node in nodeList if node.nodetype == "ComputeScheduleNode"
        ]
        # 路由器列表
        self.routers = [node for node in nodeList if node.nodetype == "Router"]
        # 项目名称
        self.project_name = project_name


    def write(self):
        self.write_network_ned(open(self.filename, "w"))

    def write_network_ned(self, f):
        # 示例：写一个简单的 OMNeT++ 网络模块结构
        self.write_dependent_source(f)
        f.write("\nnetwork Network \n{\n")
        f.write("\tsubmodules:\n")
        self.write_submodules(f)
        f.write("\tconnections:\n")
        self.write_connections(f)
        f.write("}\n")
        return

    def write_submodules(self, f):
        """
        写入submodules:部分
        """
        def get_new_type(node) -> str:
            if node.nodetype == "Router":
                return "IndexedOspfRouter"
            elif node.nodetype == "ComputingNode":
                return "ComputeNode"
            else:
                return node.nodetype
        for node in self.nodeList:
            f.write(
                "\t\t"
                + get_node_en_name(node)
                + ":"
                + get_new_type(node)
                + "{\n"
            )
            if node.nodetype == "Router":
                f.write(f"\t\t\tparameters:\n\t\t\t\trouterId = {node.index};\n\t\t\t\thasStatus = true;\n")
            elif node.nodetype == "UserGateway" or node.nodetype == "ComputingGateway":
                f.write(f"\t\t\tparameters:\n\t\t\t\thasStatus = true;\n")
            f.write("\t\t\tgates:\n")
            f.write(f"\t\t\t\tethg[{len(node.channelList)}];\n")
            f.write("\t\t}\n")
            pass
        f.write("""
        EventLogger: NetworkEventLogger {
            @display("p=97.57126,244.92377;is=s");
        }        
""")
        f.write("\t\tconfigurator: Ipv4NetworkConfigurator {\n")
        f.write("\t\t\tparameters:\n")
        f.write("\t"*4+"config = xml(\"<config>\" +\n")
        edgenodes = self.user_nodes+self.compute_nodes+self.compute_schedule_nodes
        routernodes = self.computing_gateways+self.user_gateways+self.routers
        for node in edgenodes:
            for channel in node.channelList:
                another = channel.another_point_of_channel(node)
                f.write("\t"*6+f"\"<interface hosts='{get_node_en_name(node)}'"
                               f" towards='{get_node_en_name(another)}' address='{node.ip}' netmask='{node.mask}'  />\" +\n")

        for node in routernodes:
            for channel in node.channelList:
                another = channel.another_point_of_channel(node)
                f.write("\t"*6+f"\"<interface hosts='{get_node_en_name(node)}'"
                               f" towards='{get_node_en_name(another)}' address='{node.ip_dict[another]}' netmask='{node.mask_dict[another]}'  />\" +\n")

        for node in edgenodes:
            another = None
            # print(len(node.channelList), node.name)
            for channel in node.channelList:
                another = channel.another_point_of_channel(node)
                # print(node.nodetype, another.nodetype)
                if another.nodetype in ROUTERTYPE:
                    break
            if another is not None:
                f.write("\t"*6+f"\"<route hosts='{get_node_en_name(node)}' destination='*' gateway='{get_node_en_name(another)}'/>\"+\n")

        f.write("\t"*4+"\"</config>\");\n")
        f.write("\t\t}\n\n")
        f.write('''
        scenarioManager: ScenarioManager {
            @display("p=98.15749,135.4325;is=s");
        }
''')
        f.write('\n')

    def write_connections(self, f):
        for channel in self.channelList:
            start_name = get_node_en_name(channel.start_item)
            start_index = channel.start_item.channelList.index(channel)
            end_name = get_node_en_name(channel.end_item)
            end_index = channel.end_item.channelList.index(channel)
            # bandwidth = channel.bandwidth if channel.bandwidth != 0 else 100
            f.write(
                f"\t\t{start_name}.ethg[{start_index}]"
                f" <--> ThruputMeteringChannel {{delay = {channel.banddelay}us; datarate = {channel.bandwidth}Mbps; thruputDisplayFormat = \"#N\";}} <--> "
                f"{end_name}.ethg[{end_index}];\n"
            )

    def write_dependent_source(self, f):
        f.write(f"package inet.examples.computing_power_network.{self.project_name};\n\n")

        f.write("import inet.common.misc.ThruputMeteringChannel;\n")
        f.write("import inet.common.scenario.ScenarioManager;\n")
        f.write("import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;\n")
        f.write("import inet.node.ospfv2.OspfRouter;\n")
        f.write("import inet.node.inet.StandardHost;\n")
        f.write("import inet.applications.udpapp.UdpBasicApp;\n\n")

        f.write("import inet.computing_power_network.node.UserGateway;\n")
        f.write("import inet.computing_power_network.node.ComputingGateway;\n")
        f.write("import inet.computing_power_network.node.UserNode;\n")
        f.write("import inet.computing_power_network.node.ComputeNode;\n")
        f.write("import inet.computing_power_network.node.ComputeScheduleNode;\n")
        f.write("import inet.computing_power_network.node.IndexedOspfRouter;\n")
        f.write("import inet.computing_power_network.logger.NetworkEventLogger;\n\n")

class INIWriter:
    def __init__(self, filename: str, nodeList: list, channelList: list, project_dir:str):
        self.filename = filename
        self.nodeList = nodeList
        self.channelList = channelList
        self.project_dir = project_dir

    def write(self):
        self.write_omnetpp_ini(
            f=open(self.filename, "w"),
            nodeList=self.nodeList,
            channelList=self.channelList,
        )
        # return True

    # 写入 omnetpp.ini 的具体内容
    def write_omnetpp_ini(self, f, nodeList=None, channelList=None):
        f.write("[General]\n")
        f.write(
            f"network = inet.examples.computing_power_network.{self.project_dir}.Network\n"
        )
        f.write("scheduler-class = \"cRealTimeScheduler\"\n")
        f.write("realtimescheduler-scaling = 1\n")
        # f.write("cmdenv-express-mode = false\n")
        f.write("")
        f.write('\n')
        f.write('**.ospf.ospfConfig = xmldoc("config.xml")\n\n')
        # 用户节点列表
        user_nodes = [node for node in nodeList if node.nodetype == "UserNode"]
        # 算力节点列表
        compute_nodes = [node for node in nodeList if node.nodetype == "ComputingNode"]
        # 用户网关列表
        user_gateways = [node for node in nodeList if node.nodetype == "UserGateway"]
        # 算力网关列表
        computing_gateways = [
            node for node in nodeList if node.nodetype == "ComputingGateway"
        ]
        # 调度决策网关列表
        compute_schedule_nodes = [
            node for node in nodeList if node.nodetype == "ComputeScheduleNode"
        ]

        # 一个一个写
        for node in compute_schedule_nodes:
            # node = ComputeScheduleNode(node)
            pref = f"**.{get_node_en_name(node)}"
            f.write(f"{pref}.numApps = 1\n")
            f.write(f'{pref}.app[0].typename = "ComputeScheduleApp"\n')
            f.write(f'{pref}.app[0].localAddress = "{node.ip}"\n')
            f.write(f"{pref}.app[0].localPort = 13333\n")
            f.write(f"{pref}.app[0].computeGatewayPort = 12344\n")
            f.write(f"{pref}.app[0].userGatewayPort = 13333\n")
        f.write('\n')
        for node in user_nodes:
            pref = f"**.{get_node_en_name(node)}"
            f.write(f"{pref}.numApps = 1\n")
            f.write(f"{pref}.app[0].typename = \"UserNodeApp\"\n")
            f.write(f"{pref}.app[0].mask = \"255.255.255.0\"\n")
            # === 业务属性 ===
            f.write(f"{pref}.app[0].userNodeId = {node.index}\n")  # 使用节点ID
            for channel in node.channelList:
                if channel.start_item == node and isinstance(channel.end_item, UserGateway):
                    f.write(f"{pref}.app[0].userRouterId = {channel.end_item.index}\n")
                    break
                elif channel.end_item == node and isinstance(channel.start_item, UserGateway):
                    f.write(f"{pref}.app[0].userRouterId = {channel.start_item.index}\n")
                    break
            # === 端口与地址信息 ===
            f.write(f"{pref}.app[0].localAddress = \"{node.ip}\"\n")  # 使用节点IP
            f.write(f"{pref}.app[0].localPort = 13333\n")
            for channel in node.channelList:
                another = channel.another_point_of_channel(node)
                if another and isinstance(another, UserGateway):
                    f.write(f"{pref}.app[0].gatewayAddress = \"{another.ip_dict[node]}\"\n")
            f.write(f"{pref}.app[0].gatewayPort = 13333\n")
            f.write(f"{pref}.app[0].computeNodePort = 1234\n")
        f.write('\n')
        for node in compute_nodes:
            node: ComputingNode  # 类型标注
            pref = f"**.{get_node_en_name(node)}"
            f.write(f"{pref}.numApps = 1\n")
            f.write(f"{pref}.app[0].typename = \"ComputeNodeApp\"\n")
            f.write(f"{pref}.app[0].mask = \"{node.mask}\"\n")
            f.write(f"{pref}.app[0].computeNodeId = {node.index}\n")  # 使用节点ID
            for channel in node.channelList:
                another = channel.another_point_of_channel(node)
                if another and isinstance(another, ComputingGateway):
                    f.write(f"{pref}.app[0].computeRouterId = {another.index}\n")
                    f.write(f"{pref}.app[0].gatewayAddress = \"{another.ip_dict[node]}\"\n")
                    break
            f.write(f"{pref}.app[0].localAddress = \"{node.ip}\"\n")  # 使用节点IP
            f.write(f"{pref}.app[0].localPort = 1234\n")
            f.write(f"{pref}.app[0].gatewayPort = 12344\n")
            f.write(f"{pref}.app[0].computingType = {node.computing_type}\n")
            f.write(f"{pref}.app[0].computingCapacity = {node.computing_power}\n")
            f.write(f"{pref}.app[0].storageCapacity = {node.storage_space}\n")  # 使用节点存储容量
            f.write(f"{pref}.app[0].switchedCapacitance = {node.switching_capacitance}\n")  # 使用节点电容
            f.write(f"{pref}.app[0].quiescentDissipation = {node.static_power}\n")  # 使用节点功耗
            f.write(f"{pref}.app[0].powerGenerationMix = {node.power_mix}\n")  # 使用节点能源混合比
            f.write(f"{pref}.app[0].price = {node.price}\n")  # 使用节点价格
        f.write('\n')
        for node in computing_gateways:
            node: ComputingGateway  # 类型标注
            pref = f"**.{get_node_en_name(node)}"
            f.write(f"{pref}.computingGatewayApp.computingGatewayId = {node.index}\n")
            f.write(f"{pref}.computingGatewayApp.schedulerAddress = \"{compute_schedule_nodes[0].ip}\"\n")
            f.write(f"{pref}.computingGatewayApp.port = 12344\n")
            f.write(f"{pref}.computingGatewayApp.scheduleNodePort = 13333\n")
            f.write(f"{pref}.computingGatewayApp.computeNodePort = 1234\n")
            f.write(f"{pref}.computingGatewayApp.userRouterPort = 13333\n")
            # f.write(f"{pref}.computingGatewayApp.statusUpdateInterval = 5\n")
            # f.write(f"{pref}.computingGatewayApp.computeNodeIps = \"10.0.8.2 10.0.12.2\"\n")
            # compute_nodes_ips = []
            # for channel in node.channelList:
            #     if channel.start_item == node and isinstance(channel.end_item, ComputingNode):
            #         compute_nodes_ips.append(channel.end_item.ip)
            #         # break
            #     elif channel.end_item == node and isinstance(channel.start_item, ComputingNode):
            #         # f.write(f"{pref}.app[0].userRouterId = {channel.start_item.index}\n")
            #         compute_nodes_ips.append(channel.start_item.ip)
            #         # break
            # ips = ' '.join(compute_nodes_ips)
            # f.write(f"{pref}.computingGatewayApp.computeNodeIps = \"{ips}\"\n")

        f.write('\n')
        for node in user_gateways:
            node: UserGateway  # 类型标注
            pref = f"**.{get_node_en_name(node)}"
            f.write(f"{pref}.userGatewayApp.userRouterId = {node.index}\n")
            f.write(f"{pref}.userGatewayApp.port = 13333\n")
            f.write(f"{pref}.userGatewayApp.scheduleNodePort = 13333\n")
            f.write(f"{pref}.userGatewayApp.userNodePort = 13333\n")
            f.write(f"{pref}.userGatewayApp.schedulerAddress = \"{compute_schedule_nodes[0].ip}\"\n")

        f.write(
            '''
**.arp.cacheTimeout = 1s


*.configurator.addStaticRoutes = false
*.configurator.addSubnetRoutes = true
*.configurator.addDefaultRoutes = false

[Config static]
description = static topology
*.scenarioManager.script = xml("<empty/>")
            '''
        )

class XMLWriter:
    def __init__(self, filename: str, nodeList: list, channelList: list):
        self.filename = filename
        self.nodeList = nodeList
        self.channelList = channelList
        # 用户节点列表
        self.user_nodes = [node for node in nodeList if node.nodetype == "UserNode"]
        # 算力节点列表
        self.compute_nodes = [node for node in nodeList if node.nodetype == "ComputingNode"]
        # 用户网关列表
        self.user_gateways = [node for node in nodeList if node.nodetype == "UserGateway"]
        # 算力网关列表
        self.computing_gateways = [
            node for node in nodeList if node.nodetype == "ComputingGateway"
        ]
        # 调度决策网关列表
        self.compute_schedule_nodes = [
            node for node in nodeList if node.nodetype == "ComputeScheduleNode"
        ]
        # 路由器列表
        self.routers = [node for node in nodeList if node.nodetype == "Router"]

    def write(self):
        self.write_xml(file=open(self.filename, 'w'))

    def write_xml(self,file):
        # 写入 XML 头部
        file.write('<?xml version="1.0"?>\n')
        file.write(
            '<OSPFASConfig xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="OSPF.xsd">\n\n'
        )
        self.write_routers_connection(file)
        self.write_non_routers(file)
        self.write_routers_config(file)
        # 关闭根元素
        file.write("</OSPFASConfig>\n")

    def write_routers_connection(self, f):
        f.write('  <Area id="0.0.0.0">\n')
        routers_connections = [channel for channel in self.channelList if channel.start_item.nodetype in ROUTERTYPE and channel.end_item.nodetype in ROUTERTYPE]
        for conn in routers_connections:
            conn:Channel
            f.write(f"    <AddressRange address=\"{get_node_en_name(conn.start_item)}>{get_node_en_name(conn.end_item)}\""
                    f" mask=\"{get_node_en_name(conn.start_item)}>{get_node_en_name(conn.end_item)}\" />\n")
            f.write(f"    <AddressRange address=\"{get_node_en_name(conn.end_item)}>{get_node_en_name(conn.start_item)}\""
                    f" mask=\"{get_node_en_name(conn.end_item)}>{get_node_en_name(conn.start_item)}\" />\n")
        pass

    def write_non_routers(self, f):
        for node in self.user_nodes:
            f.write(f"    <AddressRange address=\"{get_node_en_name(node)}\" mask=\"{get_node_en_name(node)}\" />\n")
        for node in self.compute_nodes:
            f.write(f"    <AddressRange address=\"{get_node_en_name(node)}\" mask=\"{get_node_en_name(node)}\" />\n")
        for node in self.compute_schedule_nodes:
            f.write(f"    <AddressRange address=\"{get_node_en_name(node)}\" mask=\"{get_node_en_name(node)}\" />\n")
        f.write("  </Area>\n\n")
        pass

    def write_routers_config(self, f):
        all_routers = self.routers+self.user_gateways+self.computing_gateways
        for router in all_routers:
            f.write(f"  <Router name=\"{get_node_en_name(router)}\" RFC1583Compatible=\"true\">\n")
            for channel in router.channelList:
                item = channel.another_point_of_channel(router)
                if item.nodetype in EDGETYPE:
                    f.write(f"    <BroadcastInterface ifName=\"eth{router.channelList.index(channel)}\" area=\"0.0.0.0\" interfaceOutputCost=\"1\" />\n")
                elif item.nodetype in ROUTERTYPE:
                    f.write(
                        f"    <PointToPointInterface ifName=\"eth{router.channelList.index(channel)}\" area=\"0.0.0.0\" interfaceOutputCost=\"1\" />\n")

            f.write(f"  </Router>\n\n")
        pass